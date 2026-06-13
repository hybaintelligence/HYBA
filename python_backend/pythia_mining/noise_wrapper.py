"""Noise protocol wrapper for Stratum V2 encrypted connections.

This module implements the Noise protocol handshake required by pools like Braiins
for authenticated and encrypted Stratum V2 connections.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from typing import Optional, Tuple

try:
    from noise.connection import NoiseConnection, Keypair
    from noise.noise_protocol import NoiseProtocol
except ImportError:
    NoiseConnection = None
    NoiseProtocol = None
    Keypair = None


logger = logging.getLogger("noise_wrapper")


class NoiseProtocolError(Exception):
    """Raised when Noise protocol handshake fails."""


@dataclass
class NoiseHandshakeResult:
    """Result of a successful Noise protocol handshake."""
    protocol: Optional[NoiseProtocol] = None
    local_static_public: Optional[bytes] = None
    remote_static_public: Optional[bytes] = None
    encrypted: bool = False


class NoiseWrapper:
    """Wrapper for Noise protocol operations in Stratum V2 context."""

    def __init__(self, protocol_name: str = "Noise_XX_25519_ChaChaPoly_SHA256"):
        """
        Initialize Noise wrapper.
        
        Args:
            protocol_name: Noise protocol pattern (default: XX for Stratum V2)
        """
        if NoiseConnection is None:
            raise ImportError(
                "noiseprotocol library is required for Noise protocol support. "
                "Install with: pip install noiseprotocol"
            )
        
        # Convert string to bytes for the noise library
        self.protocol_name = protocol_name.encode('ascii') if isinstance(protocol_name, str) else protocol_name
        self.connection: Optional[NoiseConnection] = None
        self.handshake_complete = False

    def initialize(self, local_static_key: Optional[bytes] = None) -> None:
        """
        Initialize Noise connection with optional static key.
        
        Args:
            local_static_key: Optional local static private key (32 bytes for 25519)
                             If not provided, one will be generated automatically.
        """
        try:
            self.connection = NoiseConnection.from_name(self.protocol_name)
            self.connection.set_prologue(b"")
            
            # Generate or set static key
            if local_static_key:
                self.connection.set_keypair_from_private_bytes(
                    Keypair.STATIC, local_static_key
                )
            else:
                # Generate a new static key
                private_key = generate_static_key()
                self.connection.set_keypair_from_private_bytes(
                    Keypair.STATIC, private_key
                )
            
            logger.debug(f"Noise connection initialized with protocol: {self.protocol_name}")
        except Exception as e:
            raise NoiseProtocolError(f"Failed to initialize Noise connection: {e}")

    async def perform_handshake(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        is_initiator: bool = True,
    ) -> NoiseHandshakeResult:
        """
        Perform Noise protocol handshake over transport.
        
        Args:
            reader: Async stream reader
            writer: Async stream writer
            is_initiator: True if this side initiates the handshake
            
        Returns:
            NoiseHandshakeResult with connection state
        """
        if not self.connection:
            raise NoiseProtocolError("Noise connection not initialized")

        try:
            if is_initiator:
                self.connection.set_as_initiator()
            else:
                self.connection.set_as_responder()
            
            # Start handshake
            self.connection.start_handshake()
            
            # Perform handshake
            while not self.connection.handshake_finished:
                # Write handshake message if we have one
                if is_initiator or not self.connection.handshake_finished:
                    message = self.connection.write_message()
                    if message:
                        writer.write(len(message).to_bytes(4, 'big'))
                        writer.write(message)
                        await writer.drain()
                        logger.debug(f"Sent handshake message ({len(message)} bytes)")
                
                # Read handshake message if needed
                if not self.connection.handshake_finished:
                    try:
                        length_bytes = await asyncio.wait_for(reader.readexactly(4), timeout=30.0)
                        length = int.from_bytes(length_bytes, 'big')
                        message = await asyncio.wait_for(reader.readexactly(length), timeout=30.0)
                        self.connection.read_message(message)
                        logger.debug(f"Received handshake message ({len(message)} bytes)")
                    except asyncio.TimeoutError:
                        raise NoiseProtocolError("Handshake timeout")
            
            self.handshake_complete = True
            logger.info("Noise protocol handshake completed successfully")
            
            return NoiseHandshakeResult(
                protocol=self.connection,
                local_static_public=None,  # Not directly accessible in this API
                remote_static_public=None,  # Not directly accessible in this API
                encrypted=True,
            )
            
        except Exception as e:
            raise NoiseProtocolError(f"Handshake failed: {e}")

    async def encrypt(self, data: bytes) -> bytes:
        """Encrypt data using established Noise session."""
        if not self.handshake_complete:
            raise NoiseProtocolError("Handshake not complete")
        
        try:
            return self.connection.encrypt(data)
        except Exception as e:
            raise NoiseProtocolError(f"Encryption failed: {e}")

    async def decrypt(self, data: bytes) -> bytes:
        """Decrypt data using established Noise session."""
        if not self.handshake_complete:
            raise NoiseProtocolError("Handshake not complete")
        
        try:
            return self.connection.decrypt(data)
        except Exception as e:
            raise NoiseProtocolError(f"Decryption failed: {e}")

    def get_session_hash(self) -> Optional[str]:
        """Get the session hash for verification."""
        if not self.connection:
            return None
        try:
            handshake_hash = self.connection.get_handshake_hash()
            return hashlib.sha256(handshake_hash).hexdigest()
        except Exception:
            return None


def generate_static_key() -> bytes:
    """Generate a new static key pair for Noise protocol."""
    if NoiseConnection is None:
        raise ImportError("noiseprotocol library is required")
    
    # Generate a new key pair using cryptography
    from cryptography.hazmat.primitives.asymmetric import x25519
    private_key = x25519.X25519PrivateKey.generate()
    return private_key.private_bytes_raw()


__all__ = [
    "NoiseWrapper",
    "NoiseHandshakeResult", 
    "NoiseProtocolError",
    "generate_static_key",
]

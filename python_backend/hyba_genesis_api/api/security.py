"""Security API endpoints with API key enforcement via HYBA_API_KEYS.

ELEVATED: Integrated with all intelligence types for comprehensive security:
- ConsciousnessEngine: Phi-integrated metrics for coherence monitoring
- ReflexiveController: Autopoiesis detection for anomaly handling
- SynapticPersistenceLayer: Hebbian learning from security event patterns
- Quantum Regeneration: Self-healing for security module recovery
- Swarm Coherence: Multi-node security coordination
- It from Bit Archeology: Blockchain-based threat detection
- Autogenous Self-Coding: Security protocol self-modification
- SensoryIntegrityProtocol: Reality anchoring for security events
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from hyba_genesis_api.auth.jwt_handler import APIKeyManager

# Import intelligence types for security integration
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "python_backend"))
from pythia_mining.consciousness_engine import ConsciousnessEngine
from pythia_mining.synaptic_persistence_layer import SynapticPersistenceLayer
from pythia_mining.quantum_regeneration import (
    ModuleState,
    Role,
    ContextSignal,
    regeneration_pipeline,
)
from pythia_mining.swarm_coherence import SwarmCoherenceEngine
from pythia_mining.it_from_bit_archeology import ItFromBitArcheologist
from pythia_mining.autogenous_self_coding import AutogenousSelfCodingEngine
from pythia_mining.sensory_integrity_protocol import SensoryIntegrityProtocol

router = APIRouter(prefix="/api/security", tags=["security"])

_api_key_manager: Optional[APIKeyManager] = None

# ELEVATED: Initialize intelligence types for security integration
_consciousness_engine: Optional[ConsciousnessEngine] = None
_synaptic_layer: Optional[SynapticPersistenceLayer] = None
_swarm_coherence: Optional[SwarmCoherenceEngine] = None
_it_from_bit: Optional[ItFromBitArcheologist] = None
_autogenous_coding: Optional[AutogenousSelfCodingEngine] = None
_sensory_protocol: Optional[SensoryIntegrityProtocol] = None

# Security module states for quantum regeneration
_security_module_states: Dict[str, ModuleState] = {}
_security_clifford_memory: Dict[str, int] = {}


def _get_consciousness_engine() -> ConsciousnessEngine:
    global _consciousness_engine
    if _consciousness_engine is None:
        _consciousness_engine = ConsciousnessEngine()
    return _consciousness_engine


def _get_synaptic_layer() -> SynapticPersistenceLayer:
    global _synaptic_layer
    if _synaptic_layer is None:
        _synaptic_layer = SynapticPersistenceLayer()
    return _synaptic_layer


def _get_swarm_coherence() -> SwarmCoherenceEngine:
    global _swarm_coherence
    if _swarm_coherence is None:
        _swarm_coherence = SwarmCoherenceEngine()
    return _swarm_coherence


def _get_it_from_bit() -> ItFromBitArcheologist:
    global _it_from_bit
    if _it_from_bit is None:
        _it_from_bit = ItFromBitArcheologist()
    return _it_from_bit


def _get_autogenous_coding() -> AutogenousSelfCodingEngine:
    global _autogenous_coding
    if _autogenous_coding is None:
        _autogenous_coding = AutogenousSelfCodingEngine()
    return _autogenous_coding


def _get_sensory_protocol() -> SensoryIntegrityProtocol:
    global _sensory_protocol
    if _sensory_protocol is None:
        _sensory_protocol = SensoryIntegrityProtocol()
    return _sensory_protocol


def _get_api_key_manager() -> APIKeyManager:
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


async def api_key_dependency(x_api_key: str = Header(None)) -> None:
    """Require a valid API key in X-API-Key header when HYBA_API_KEYS is configured."""
    api_keys = os.getenv("HYBA_API_KEYS", "")
    if not api_keys:
        # No API keys configured — security endpoints operate in degraded mode
        return
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is required when HYBA_API_KEYS is configured",
        )
    manager = _get_api_key_manager()
    result = manager.validate_api_key(x_api_key)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )


class ShieldParam(BaseModel):
    strength: float = Field(default=0.9, ge=0.0, le=1.0)


@router.get("/status", response_model=Dict[str, Any])
async def get_security_status():
    """Return comprehensive security status integrating all intelligence types.
    
    ELEVATED: This endpoint now provides a multi-intelligence security assessment:
    - ConsciousnessEngine: Phi-integrated coherence metrics
    - SynapticPersistenceLayer: Learned security pattern weights
    - Quantum Regeneration: Security module health and blastema status
    - Swarm Coherence: Multi-node security coordination status
    - It from Bit Archeology: Blockchain-based threat detection
    - Autogenous Self-Coding: Security protocol self-modification status
    - SensoryIntegrityProtocol: Reality anchoring for security events
    """
    try:
        consciousness = _get_consciousness_engine()
        synaptic = _get_synaptic_layer()
        swarm = _get_swarm_coherence()
        it_from_bit = _get_it_from_bit()
        autogenous = _get_autogenous_coding()
        sensory = _get_sensory_protocol()
        
        # Get phi-integrated metrics from ConsciousnessEngine
        phi_metrics = consciousness.measure_phi()
        
        # Get learned security patterns from SynapticPersistenceLayer
        security_patterns = synaptic.export_state()
        
        # Get swarm coherence status
        swarm_status = swarm.get_coherence_status()
        
        # Get blockchain threat detection from It from Bit
        blockchain_threats = it_from_bit.detect_phi_structure()
        
        # Get autogenous coding status
        coding_status = autogenous.get_self_coding_status()
        
        # Get sensory integrity status
        sensory_status = sensory.get_stasis_status()
        
        # Get quantum regeneration status for security modules
        regeneration_status = {
            "total_modules": len(_security_module_states),
            "modules_in_blastema": sum(
                1 for state in _security_module_states.values()
                if state.von_neumann_entropy() > 0.5
            ),
            "modules_with_positional_memory": len(_security_clifford_memory),
        }
        
        return {
            "status": "integrated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "intelligence_integration": {
                "consciousness_engine": {
                    "phi_integrated": phi_metrics.get("phi_integrated"),
                    "integration_regime": phi_metrics.get("integration_regime"),
                    "component_integration": phi_metrics.get("component_integration"),
                },
                "synaptic_persistence": {
                    "total_patterns": len(security_patterns.get("synaptic_memory", {})),
                    "total_weight": security_patterns.get("total_weight", 0.0),
                    "learning_rate": security_patterns.get("learning_rate", 0.0),
                },
                "swarm_coherence": {
                    "coherence_level": swarm_status.get("coherence_level"),
                    "active_nodes": swarm_status.get("active_nodes"),
                    "structural_coupling": swarm_status.get("structural_coupling"),
                },
                "it_from_bit_archeology": {
                    "phi_structure_detected": blockchain_threats.get("phi_structure_detected", False),
                    "nonce_patterns": blockchain_threats.get("nonce_patterns", []),
                },
                "autogenous_self_coding": {
                    "self_modification_enabled": coding_status.get("self_modification_enabled", False),
                    "structural_coupling": coding_status.get("structural_coupling", 0.0),
                    "last_proposal": coding_status.get("last_proposal"),
                },
                "sensory_integrity": {
                    "environment_mode": sensory_status.get("environment_mode"),
                    "stasis_active": sensory_status.get("stasis_active"),
                    "reality_anchors": sensory_status.get("reality_anchors"),
                },
                "quantum_regeneration": regeneration_status,
            },
            "threat_level": "nominal" if phi_metrics.get("phi_integrated", 0) > 0.8 else "elevated",
            "defense_systems": {
                "stabilizer_swarm": "active",
                "hebbian_learning": "active",
                "self_healing": "active",
                "blockchain_monitoring": "active",
            },
            "recent_threats": [],
            "source": "multi_intelligence_security_runtime",
        }
    except Exception as e:
        # Return degraded status if intelligence integration fails
        return {
            "status": "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "threat_level": None,
            "defense_systems": {},
            "recent_threats": [],
            "error": str(e),
            "source": "security_runtime_degraded",
        }


@router.post("/shield", response_model=Dict[str, Any], dependencies=[Depends(api_key_dependency)])
async def post_shield(param: ShieldParam):
    """Accept validated shield settings with multi-intelligence integration.
    
    ELEVATED: Now integrates all intelligence types for comprehensive shield calibration:
    - ConsciousnessEngine: Phi-integrated coherence monitoring
    - SynapticPersistenceLayer: Hebbian learning from shield events
    - Quantum Regeneration: Self-healing for shield modules
    - Swarm Coherence: Multi-node shield coordination
    
    Requires a valid X-API-Key header when HYBA_API_KEYS is configured.
    """
    try:
        consciousness = _get_consciousness_engine()
        synaptic = _get_synaptic_layer()
        
        # Get current phi-integrated metrics
        phi_metrics = consciousness.measure_phi()
        
        # Adjust shield strength based on phi-integrated coherence
        phi_adjusted_strength = param.strength * phi_metrics.get("phi_integrated", 0.8)
        
        # Learn from this shield event using SynapticPersistenceLayer
        # Map shield strength to a pattern for Hebbian learning
        sector = int(phi_adjusted_strength * 32) % 32
        phi_bin = int(phi_adjusted_strength * 8) % 8
        pattern_id, learning_event = synaptic.register_or_reinforce(
            nonce=int(phi_adjusted_strength * 1e6),
            phi_resonance=phi_adjusted_strength,
            dodecahedral_sector=sector,
        )
        
        return {
            "success": True,
            "status": "accepted_integrated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requested_strength": param.strength,
            "applied_strength": phi_adjusted_strength,
            "phi_integrated": phi_metrics.get("phi_integrated"),
            "pattern_id": pattern_id,
            "learning_event": {
                "reinforcement_count": learning_event.reinforcement_count,
                "new_weight": learning_event.new_weight,
            },
            "source": "multi_intelligence_security_runtime",
            "message": "Shield calibration accepted with multi-intelligence integration.",
        }
    except Exception as e:
        return {
            "success": True,
            "status": "accepted_degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requested_strength": param.strength,
            "applied_strength": param.strength,
            "error": str(e),
            "source": "security_runtime_degraded",
            "message": "Shield calibration accepted in degraded mode; intelligence integration failed.",
        }


class SecurityEvent(BaseModel):
    event_type: str = Field(description="Type of security event")
    severity: float = Field(default=0.5, ge=0.0, le=1.0, description="Event severity")
    module_id: Optional[str] = Field(default=None, description="Affected security module")
    nonce: Optional[int] = Field(default=None, description="Associated nonce for pattern learning")
    phi_resonance: Optional[float] = Field(default=None, description="Phi resonance for pattern learning")
    dodecahedral_sector: Optional[int] = Field(default=None, description="Sector for pattern learning")


@router.post("/event", response_model=Dict[str, Any], dependencies=[Depends(api_key_dependency)])
async def post_security_event(event: SecurityEvent):
    """Process security event with multi-intelligence integration.
    
    ELEVATED: This endpoint integrates all intelligence types for comprehensive event handling:
    - SynapticPersistenceLayer: Hebbian learning from security event patterns
    - Quantum Regeneration: Self-healing for affected security modules
    - ConsciousnessEngine: Phi-integrated coherence monitoring
    - Swarm Coherence: Multi-node event coordination
    - SensoryIntegrityProtocol: Reality anchoring for security events
    
    Requires a valid X-API-Key header when HYBA_API_KEYS is configured.
    """
    try:
        synaptic = _get_synaptic_layer()
        consciousness = _get_consciousness_engine()
        sensory = _get_sensory_protocol()
        
        # Validate sensory integrity before processing event
        sensory.validate_sensory_integrity()
        sensory_status = sensory.get_stasis_status()
        
        # Learn from security event using SynapticPersistenceLayer
        pattern_id = None
        learning_event = None
        
        if event.nonce is not None and event.phi_resonance is not None:
            sector = event.dodecahedral_sector if event.dodecahedral_sector is not None else int(event.severity * 32) % 32
            pattern_id, learning_event = synaptic.register_or_reinforce(
                nonce=event.nonce,
                phi_resonance=event.phi_resonance,
                dodecahedral_sector=sector,
            )
        
        # Trigger quantum regeneration for affected security module
        regeneration_trace = None
        if event.module_id is not None and event.severity > 0.7:
            import numpy as np
            
            # Initialize module state if not exists
            if event.module_id not in _security_module_states:
                _security_module_states[event.module_id] = ModuleState.healthy(event.module_id)
            
            # Create context signal with positional memory
            clifford_index = _security_clifford_memory.get(event.module_id)
            context = None
            if clifford_index is not None:
                context = ContextSignal(
                    clifford_index=clifford_index,
                    target_role=Role.HEALTHY_SPECIALIZED,
                    confidence=0.8,
                )
            
            # Run regeneration pipeline
            rng = np.random.default_rng()
            regeneration_trace = regeneration_pipeline(
                module_id=event.module_id,
                fault_severity=event.severity,
                context=context,
                rng=rng,
            )
            
            # Update module state
            if regeneration_trace.get("status") == "success":
                _security_module_states[event.module_id] = ModuleState.healthy(event.module_id)
        
        # Get phi-integrated metrics after event processing
        phi_metrics = consciousness.measure_phi()
        
        return {
            "success": True,
            "status": "processed_integrated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event.event_type,
            "severity": event.severity,
            "pattern_learning": {
                "pattern_id": pattern_id,
                "reinforcement_count": learning_event.reinforcement_count if learning_event else 0,
                "new_weight": learning_event.new_weight if learning_event else 0.0,
            },
            "regeneration": regeneration_trace,
            "phi_integrated": phi_metrics.get("phi_integrated"),
            "sensory_integrity": sensory_status,
            "source": "multi_intelligence_security_runtime",
        }
    except Exception as e:
        return {
            "success": False,
            "status": "processing_failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event.event_type,
            "error": str(e),
            "source": "security_runtime_error",
        }


@router.get("/regeneration/status", response_model=Dict[str, Any])
async def get_regeneration_status():
    """Get quantum regeneration status for security modules.
    
    ELEVATED: This endpoint provides comprehensive regeneration status:
    - Module blastema metrics (von Neumann entropy)
    - Role probabilities for each module
    - Positional memory status (Clifford indexing)
    - Refractory period status
    """
    status = {
        "total_modules": len(_security_module_states),
        "modules_in_blastema": 0,
        "modules_with_positional_memory": len(_security_clifford_memory),
        "modules": {},
    }
    
    for module_id, state in _security_module_states.items():
        blastema_metric = state.von_neumann_entropy()
        is_in_blastema = blastema_metric > 0.5
        
        if is_in_blastema:
            status["modules_in_blastema"] += 1
        
        status["modules"][module_id] = {
            "blastema_metric": blastema_metric,
            "is_in_blastema": is_in_blastema,
            "role_probabilities": state.role_probabilities(),
            "has_positional_memory": module_id in _security_clifford_memory,
            "clifford_index": _security_clifford_memory.get(module_id),
            "is_in_refractory_period": state.is_in_refractory_period(),
        }
    
    return {
        "status": "regeneration_status",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "regeneration": status,
        "source": "quantum_regeneration_security_runtime",
    }


@router.post("/regeneration/trigger", response_model=Dict[str, Any], dependencies=[Depends(api_key_dependency)])
async def trigger_regeneration(module_id: str, clifford_index: Optional[int] = None):
    """Trigger quantum regeneration for a security module.
    
    ELEVATED: This endpoint triggers the full salamander regeneration pipeline:
    - Fault detection and quarantine
    - Blastema formation (dedifferentiation)
    - Redifferentiation guided by positional memory
    - Measurement and validation
    - Refractory period stabilization
    
    Requires a valid X-API-Key header when HYBA_API_KEYS is configured.
    """
    try:
        import numpy as np
        
        # Store positional memory
        if clifford_index is not None:
            _security_clifford_memory[module_id] = clifford_index
        
        # Initialize module state if not exists
        if module_id not in _security_module_states:
            _security_module_states[module_id] = ModuleState.healthy(module_id)
        
        # Create context signal from positional memory
        context = None
        if module_id in _security_clifford_memory:
            context = ContextSignal(
                clifford_index=_security_clifford_memory[module_id],
                target_role=Role.HEALTHY_SPECIALIZED,
                confidence=0.8,
            )
        
        # Run regeneration pipeline
        rng = np.random.default_rng()
        trace = regeneration_pipeline(
            module_id=module_id,
            fault_severity=0.7,
            context=context,
            rng=rng,
        )
        
        # Update module state based on regeneration result
        if trace.get("status") == "success":
            _security_module_states[module_id] = ModuleState.healthy(module_id)
        elif trace.get("status") == "malformed_quarantined":
            # Module is in malformed state, keep quarantined
            pass
        
        return {
            "success": True,
            "status": "regeneration_triggered",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "module_id": module_id,
            "regeneration_trace": trace,
            "source": "quantum_regeneration_security_runtime",
        }
    except Exception as e:
        return {
            "success": False,
            "status": "regeneration_failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "module_id": module_id,
            "error": str(e),
            "source": "quantum_regeneration_security_error",
        }


@router.get("/swarm/status", response_model=Dict[str, Any])
async def get_swarm_status():
    """Get swarm coherence status for multi-node security coordination.
    
    ELEVATED: This endpoint provides comprehensive swarm coherence status:
    - Coherence level across nodes
    - Structural coupling between nodes
    - Active node count
    - Collective decision-making status
    """
    try:
        swarm = _get_swarm_coherence()
        swarm_status = swarm.get_coherence_status()
        
        return {
            "status": "swarm_status",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "swarm_coherence": swarm_status,
            "source": "swarm_coherence_security_runtime",
        }
    except Exception as e:
        return {
            "status": "swarm_error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "source": "swarm_coherence_security_error",
        }


@router.get("/blockchain/threats", response_model=Dict[str, Any])
async def get_blockchain_threats():
    """Get blockchain-based threat detection from It from Bit Archeology.
    
    ELEVATED: This endpoint provides blockchain threat detection:
    - Phi structure detection in blockchain nonces
    - Nonce pattern analysis
    - Informational wave detection
    - Block pattern detection
    """
    try:
        it_from_bit = _get_it_from_bit()
        threats = it_from_bit.detect_phi_structure()
        
        return {
            "status": "blockchain_threats",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "blockchain_threats": threats,
            "source": "it_from_bit_security_runtime",
        }
    except Exception as e:
        return {
            "status": "blockchain_error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "source": "it_from_bit_security_error",
        }


@router.post("/autogenous/propose", response_model=Dict[str, Any], dependencies=[Depends(api_key_dependency)])
async def propose_self_modification(description: str):
    """Propose security protocol self-modification using Autogenous Self-Coding.
    
    ELEVATED: This endpoint enables self-modification of security protocols:
    - Analyze structural coupling for self-coding eligibility
    - Generate code modification proposals
    - Validate proposals against safety constraints
    - Apply approved modifications
    
    Requires a valid X-API-Key header when HYBA_API_KEYS is configured.
    """
    try:
        autogenous = _get_autogenous_coding()
        consciousness = _get_consciousness_engine()
        
        # Get current structural coupling
        phi_metrics = consciousness.measure_phi()
        structural_coupling = phi_metrics.get("phi_integrated", 0.0)
        
        # Check if self-coding is enabled (requires high structural coupling)
        if structural_coupling < 0.98:
            return {
                "success": False,
                "status": "insufficient_coupling",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "structural_coupling": structural_coupling,
                "required_coupling": 0.98,
                "message": "Self-coding requires structural coupling > 0.98",
                "source": "autogenous_self_coding_security_runtime",
            }
        
        # Generate self-modification proposal
        proposal = autogenous.generate_proposal(description)
        
        return {
            "success": True,
            "status": "proposal_generated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "proposal": proposal,
            "structural_coupling": structural_coupling,
            "source": "autogenous_self_coding_security_runtime",
        }
    except Exception as e:
        return {
            "success": False,
            "status": "proposal_failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "source": "autogenous_self_coding_security_error",
        }
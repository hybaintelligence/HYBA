"""
Salamander Multi-Agent System - Swarm Communication Layer

Phase 5.1: Swarm Intelligence + Agent Communication Protocols
Combines hierarchical control with swarm intelligence for robust, adaptive multi-agent behavior.
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel
import asyncio
import uuid
import time
import json
from datetime import datetime, timezone


class SwarmMessage(BaseModel):
    """Message structure for swarm communication."""

    message_id: str
    sender: str
    receiver: str  # Can be agent name, "all", or "swarm"
    timestamp: float
    message_type: Literal[
        "task", "result", "proposal", "vote", "pheromone", "alert", "consensus"
    ]
    payload: Dict[str, Any]
    swarm_context: Dict[str, Any] = {}  # fitness, confidence, pheromone level
    confidence: float = 0.7
    pheromone: float = 1.0  # For stigmergy


class SwarmCommunication:
    """
    Central hub for swarm communication.

    Provides:
    - Asynchronous message passing
    - Direct, broadcast, and gossip communication
    - Stigmergy via shared pheromone trails
    - Proposal/voting mechanisms for consensus
    - Redis-backed pub/sub for scalability
    """

    def __init__(self):
        self.agents: Dict[str, asyncio.Queue] = {}  # agent_name -> message queue
        self.pheromone_trails: Dict[str, float] = {}  # pattern_key -> strength
        self.proposals: Dict[str, Dict[str, Any]] = {}  # proposal_id -> proposal data
        self.votes: Dict[str, List[Dict[str, Any]]] = {}  # proposal_id -> votes
        self.message_history: List[SwarmMessage] = []
        self.max_history = 1000
        self._decay_task = None  # Lazy initialization of decay loop

    def _ensure_decay_loop(self):
        """Lazily start the pheromone decay loop if not already running."""
        if self._decay_task is None:
            try:
                self._decay_task = asyncio.create_task(self._pheromone_decay_loop())
            except RuntimeError:
                # No running event loop yet; will be started on first use
                pass

    def register_agent(self, agent_name: str) -> asyncio.Queue:
        """Register an agent and create its message queue."""
        if agent_name not in self.agents:
            self.agents[agent_name] = asyncio.Queue(maxsize=100)
        return self.agents[agent_name]

    def unregister_agent(self, agent_name: str):
        """Unregister an agent."""
        if agent_name in self.agents:
            del self.agents[agent_name]

    async def send(self, message: SwarmMessage) -> bool:
        """Send a message to target agent(s)."""
        # Ensure decay loop is running (lazy initialization)
        self._ensure_decay_loop()

        # Add to history
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)

        # Direct delivery
        if message.receiver in self.agents:
            try:
                await asyncio.wait_for(
                    self.agents[message.receiver].put(message), timeout=2.0
                )
                return True
            except asyncio.TimeoutError:
                print(f"⚠️ Message timeout for agent {message.receiver}")
                return False

        # Broadcast to all agents
        elif message.receiver == "all" or message.receiver == "swarm":
            for agent_name, queue in self.agents.items():
                if agent_name != message.sender:  # Don't send to self
                    try:
                        await asyncio.wait_for(queue.put(message), timeout=1.0)
                    except asyncio.TimeoutError:
                        print(f"⚠️ Broadcast timeout for agent {agent_name}")
            return True

        return False

    async def receive(
        self, agent_name: str, timeout: float = 5.0
    ) -> Optional[SwarmMessage]:
        """Receive a message for a specific agent."""
        if agent_name not in self.agents:
            return None

        try:
            return await asyncio.wait_for(
                self.agents[agent_name].get(), timeout=timeout
            )
        except asyncio.TimeoutError:
            return None

    async def broadcast_proposal(
        self, proposal: Dict[str, Any], sender: str, confidence: float = 0.7
    ) -> str:
        """Broadcast a proposal to the swarm for voting."""
        proposal_id = str(uuid.uuid4())

        self.proposals[proposal_id] = {
            "id": proposal_id,
            "proposal": proposal,
            "sender": sender,
            "timestamp": time.time(),
            "confidence": confidence,
            "status": "pending",
        }
        self.votes[proposal_id] = []

        message = SwarmMessage(
            message_id=str(uuid.uuid4()),
            sender=sender,
            receiver="swarm",
            timestamp=time.time(),
            message_type="proposal",
            payload={
                "proposal_id": proposal_id,
                "proposal": proposal,
                "confidence": confidence,
            },
            confidence=confidence,
        )

        await self.send(message)
        return proposal_id

    async def cast_vote(
        self,
        proposal_id: str,
        voter: str,
        vote: Literal["approve", "reject", "abstain"],
        confidence: float = 0.7,
    ):
        """Cast a vote on a proposal."""
        if proposal_id not in self.votes:
            return False

        self.votes[proposal_id].append(
            {
                "voter": voter,
                "vote": vote,
                "confidence": confidence,
                "timestamp": time.time(),
            }
        )

        # Check for consensus
        await self._check_consensus(proposal_id)
        return True

    async def _check_consensus(self, proposal_id: str):
        """Check if proposal has reached consensus."""
        if proposal_id not in self.proposals or proposal_id not in self.votes:
            return

        votes = self.votes[proposal_id]
        total_agents = len(self.agents)

        if len(votes) < total_agents:
            return  # Not all votes in yet

        # Simple majority consensus
        approve_count = sum(1 for v in votes if v["vote"] == "approve")
        reject_count = sum(1 for v in votes if v["vote"] == "reject")

        if approve_count > reject_count:
            self.proposals[proposal_id]["status"] = "approved"
            await self._broadcast_consensus(proposal_id, "approved")
        elif reject_count > approve_count:
            self.proposals[proposal_id]["status"] = "rejected"
            await self._broadcast_consensus(proposal_id, "rejected")
        else:
            self.proposals[proposal_id]["status"] = "tie"
            await self._broadcast_consensus(proposal_id, "tie")

    async def _broadcast_consensus(self, proposal_id: str, result: str):
        """Broadcast consensus result to swarm."""
        message = SwarmMessage(
            message_id=str(uuid.uuid4()),
            sender="swarm_coordinator",
            receiver="all",
            timestamp=time.time(),
            message_type="consensus",
            payload={
                "proposal_id": proposal_id,
                "result": result,
                "proposal": self.proposals[proposal_id],
            },
        )
        await self.send(message)

    def leave_pheromone(self, pattern_key: str, strength: float = 1.0):
        """Leave a pheromone trail for stigmergy."""
        self.pheromone_trails[pattern_key] = (
            self.pheromone_trails.get(pattern_key, 0) + strength
        )

    def get_pheromone(self, pattern_key: str) -> float:
        """Get pheromone strength for a pattern."""
        return self.pheromone_trails.get(pattern_key, 0.0)

    async def _pheromone_decay_loop(self):
        """Background task to decay pheromone trails over time."""
        while True:
            await asyncio.sleep(60)  # Decay every minute
            decay_rate = 0.95  # 5% decay per minute

            for key in list(self.pheromone_trails.keys()):
                self.pheromone_trails[key] *= decay_rate
                if self.pheromone_trails[key] < 0.01:
                    del self.pheromone_trails[key]

    def get_swarm_status(self) -> Dict[str, Any]:
        """Get overall swarm status."""
        return {
            "registered_agents": len(self.agents),
            "active_proposals": len(
                [p for p in self.proposals.values() if p["status"] == "pending"]
            ),
            "pheromone_trails": len(self.pheromone_trails),
            "message_history_size": len(self.message_history),
            "agents": list(self.agents.keys()),
        }


class SwarmEnabledAgent:
    """
    Base class for agents with swarm communication capabilities.

    Extends agents with:
    - Proposal generation and voting
    - Pheromone-based learning
    - Swarm consensus participation
    """

    def __init__(self, name: str, comm: SwarmCommunication):
        self.name = name
        self.comm = comm
        self.comm.register_agent(name)
        self.local_knowledge: Dict[str, Any] = {}
        self.proposal_history: List[str] = []

    async def send_message(
        self, receiver: str, message_type: str, payload: Dict, confidence: float = 0.7
    ):
        """Send a message through the swarm."""
        message = SwarmMessage(
            message_id=str(uuid.uuid4()),
            sender=self.name,
            receiver=receiver,
            timestamp=time.time(),
            message_type=message_type,
            payload=payload,
            confidence=confidence,
        )
        return await self.comm.send(message)

    async def receive_message(self, timeout: float = 5.0) -> Optional[SwarmMessage]:
        """Receive a message from the swarm."""
        return await self.comm.receive(self.name, timeout)

    async def propose_fix(
        self, diagnosis: Dict, fix_plan: Dict, confidence: float = 0.7
    ) -> str:
        """Propose a fix to the swarm for consensus."""
        proposal = {
            "diagnosis": diagnosis,
            "fix_plan": fix_plan,
            "proposed_by": self.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        proposal_id = await self.comm.broadcast_proposal(
            proposal, self.name, confidence
        )
        self.proposal_history.append(proposal_id)

        return proposal_id

    async def vote_on_proposal(
        self,
        proposal_id: str,
        vote: Literal["approve", "reject", "abstain"],
        confidence: float = 0.7,
    ):
        """Vote on a proposal."""
        return await self.comm.cast_vote(proposal_id, self.name, vote, confidence)

    def learn_from_pheromone(self, pattern_key: str) -> float:
        """Learn from pheromone trails (stigmergy)."""
        return self.comm.get_pheromone(pattern_key)

    def reinforce_pheromone(self, pattern_key: str, success: bool):
        """Reinforce pheromone trail based on success."""
        strength = 1.0 if success else -0.5
        self.comm.leave_pheromone(pattern_key, strength)

    async def listen_for_proposals(self, timeout: float = 30.0):
        """Listen for incoming proposals and vote on them."""
        while True:
            message = await self.receive_message(timeout=timeout)
            if message and message.message_type == "proposal":
                await self._evaluate_and_vote(message)

    async def _evaluate_and_vote(self, message: SwarmMessage):
        """Evaluate a proposal and cast a vote."""
        proposal_id = message.payload.get("proposal_id")
        proposal = message.payload.get("proposal")

        # Simple evaluation based on confidence and local knowledge
        confidence = message.confidence

        # Check pheromone trails for similar patterns
        pattern_key = self._extract_pattern_key(proposal)
        pheromone_strength = self.learn_from_pheromone(pattern_key)

        # Adjust confidence based on pheromone
        adjusted_confidence = min(1.0, confidence + pheromone_strength * 0.1)

        # Cast vote
        if adjusted_confidence > 0.7:
            await self.vote_on_proposal(proposal_id, "approve", adjusted_confidence)
        elif adjusted_confidence < 0.4:
            await self.vote_on_proposal(proposal_id, "reject", adjusted_confidence)
        else:
            await self.vote_on_proposal(proposal_id, "abstain", adjusted_confidence)

    def _extract_pattern_key(self, proposal: Dict) -> str:
        """Extract a pattern key from proposal for pheromone tracking."""
        diagnosis = proposal.get("diagnosis", {})
        return f"{diagnosis.get('severity', 'medium')}_{diagnosis.get('affected_modules', [])[:2]}"


# Global swarm communication instance
_swarm_comm = SwarmCommunication()


def get_swarm_communication() -> SwarmCommunication:
    """Get the global swarm communication instance."""
    return _swarm_comm

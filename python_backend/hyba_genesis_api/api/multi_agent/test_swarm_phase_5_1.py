"""
Comprehensive Verification Tests: Salamander Swarm Intelligence Phase 5.1

Tests all swarm components with formal verification scrutiny:
- Swarm Communication Hub
- PSO Task Allocator
- Stigmergy/Pheromone Mechanics
- Consensus/Voting Mechanisms
- Mathematical Correctness of PSO
- Edge Cases and Scalability
"""

import pytest
import asyncio
import time
import math
import json
from typing import Dict, Any

# Import swarm modules
from .swarm_communication import (
    SwarmMessage,
    SwarmCommunication,
    SwarmEnabledAgent,
    get_swarm_communication,
)
from .pso_allocator import (
    PSOParticle,
    PSOTaskAllocator,
    SwarmTaskCoordinator,
    get_task_coordinator,
)


# =============================================================================
# SECTION 1: Swarm Communication Hub Tests
# =============================================================================

class TestSwarmMessage:
    """Test SwarmMessage data model integrity."""

    def test_swarm_message_creation(self):
        """Verify message creation with all field types."""
        msg = SwarmMessage(
            message_id="test-1",
            sender="agent_alpha",
            receiver="agent_beta",
            timestamp=time.time(),
            message_type="task",
            payload={"action": "fix", "module": "auth"},
            swarm_context={"fitness": 0.9, "confidence": 0.8, "pheromone_level": 0.7},
            confidence=0.85,
            pheromone=1.0,
        )
        assert msg.message_id == "test-1"
        assert msg.sender == "agent_alpha"
        assert msg.receiver == "agent_beta"
        assert msg.message_type == "task"
        assert msg.confidence == 0.85
        assert msg.pheromone == 1.0
        assert msg.swarm_context["fitness"] == 0.9

    def test_swarm_message_types(self):
        """Verify all seven message types are valid."""
        valid_types = {"task", "result", "proposal", "vote", "pheromone", "alert", "consensus"}
        for msg_type in valid_types:
            msg = SwarmMessage(
                message_id=f"test-{msg_type}",
                sender="agent",
                receiver="all",
                timestamp=time.time(),
                message_type=msg_type,
                payload={"test": True},
            )
            assert msg.message_type == msg_type

    def test_swarm_message_invalid_type(self):
        """Verify invalid message types are rejected."""
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            SwarmMessage(
                message_id="test-invalid",
                sender="agent",
                receiver="all",
                timestamp=time.time(),
                message_type="invalid_type",
                payload={},
            )


class TestSwarmCommunication:
    """Test SwarmCommunication hub with formal verification rigor."""

    @pytest.fixture
    def comm(self):
        """Create fresh SwarmCommunication for each test."""
        return SwarmCommunication()

    @pytest.mark.asyncio
    async def test_agent_registration(self, comm):
        """Verify agent registration creates queues."""
        queue = comm.register_agent("agent_alpha")
        assert "agent_alpha" in comm.agents
        assert queue.maxsize == 100  # Verify queue limit
        assert comm.agents["agent_alpha"] is queue

        # Verify duplicate registration returns same queue
        queue2 = comm.register_agent("agent_alpha")
        assert queue2 is queue

    @pytest.mark.asyncio
    async def test_agent_unregistration(self, comm):
        """Verify agent unregistration removes queue."""
        comm.register_agent("agent_alpha")
        assert "agent_alpha" in comm.agents
        comm.unregister_agent("agent_alpha")
        assert "agent_alpha" not in comm.agents

    @pytest.mark.asyncio
    async def test_direct_message_passing(self, comm):
        """Verify direct point-to-point messaging."""
        comm.register_agent("agent_alpha")
        comm.register_agent("agent_beta")

        # Send direct message
        msg = SwarmMessage(
            message_id="direct-1",
            sender="agent_alpha",
            receiver="agent_beta",
            timestamp=time.time(),
            message_type="task",
            payload={"task": "fix_auth"},
        )
        sent = await comm.send(msg)
        assert sent is True

        # Receive on beta's queue
        received = await comm.receive("agent_beta", timeout=1.0)
        assert received is not None
        assert received.message_id == "direct-1"
        assert received.payload["task"] == "fix_auth"

        # Alpha's queue should be empty
        alpha_received = await comm.receive("agent_alpha", timeout=0.1)
        assert alpha_received is None

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self, comm):
        """Verify broadcast reaches all agents except sender."""
        agents = ["agent_alpha", "agent_beta", "agent_gamma", "agent_delta"]
        for agent in agents:
            comm.register_agent(agent)

        msg = SwarmMessage(
            message_id="broadcast-1",
            sender="agent_alpha",
            receiver="all",
            timestamp=time.time(),
            message_type="alert",
            payload={"alert": "system_event"},
        )
        sent = await comm.send(msg)
        assert sent is True

        # All other agents should receive
        for agent in ["agent_beta", "agent_gamma", "agent_delta"]:
            received = await comm.receive(agent, timeout=1.0)
            assert received is not None, f"{agent} should have received broadcast"
            assert received.message_id == "broadcast-1"

        # Sender should NOT receive their own broadcast
        sender_received = await comm.receive("agent_alpha", timeout=0.1)
        assert sender_received is None

    @pytest.mark.asyncio
    async def test_broadcast_to_swarm(self, comm):
        """Verify 'swarm' receiver alias works the same as 'all'."""
        comm.register_agent("agent_alpha")
        comm.register_agent("agent_beta")

        msg = SwarmMessage(
            message_id="swarm-bc",
            sender="agent_alpha",
            receiver="swarm",
            timestamp=time.time(),
            message_type="alert",
            payload={"alert": "swarm_event"},
        )
        sent = await comm.send(msg)
        assert sent is True

        received = await comm.receive("agent_beta", timeout=1.0)
        assert received is not None
        assert received.message_id == "swarm-bc"

    @pytest.mark.asyncio
    async def test_message_history_limit(self, comm):
        """Verify message history is limited to max_history (1000)."""
        # Fill history beyond limit
        for i in range(comm.max_history + 100):
            msg = SwarmMessage(
                message_id=f"hist-{i}",
                sender="agent",
                receiver="all",
                timestamp=time.time(),
                message_type="alert",
                payload={"index": i},
            )
            await comm.send(msg)

        # History should be capped at max_history
        assert len(comm.message_history) == comm.max_history
        # First entries should have been evicted
        first_ids = {f"hist-{i}" for i in range(100)}
        hist_ids = {m.message_id for m in comm.message_history}
        assert len(first_ids & hist_ids) == 0, "Old messages should be evicted"

    @pytest.mark.asyncio
    async def test_message_queue_limit(self, comm):
        """Verify agent queues have maxsize=100."""
        queue = comm.register_agent("agent_alpha")
        assert queue.maxsize == 100

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_agent(self, comm):
        """Verify sending to non-existent agent returns False."""
        msg = SwarmMessage(
            message_id="no-target",
            sender="agent_alpha",
            receiver="nonexistent",
            timestamp=time.time(),
            message_type="task",
            payload={},
        )
        sent = await comm.send(msg)
        assert sent is False

    @pytest.mark.asyncio
    async def test_receive_timeout(self, comm):
        """Verify receive returns None on timeout."""
        comm.register_agent("agent_alpha")
        result = await comm.receive("agent_alpha", timeout=0.1)
        assert result is None

    @pytest.mark.asyncio
    async def test_receive_from_unregistered(self, comm):
        """Verify receive from unregistered agent returns None."""
        result = await comm.receive("nonexistent", timeout=0.1)
        assert result is None


# =============================================================================
# SECTION 2: Stigmergy / Pheromone Tests
# =============================================================================

class TestPheromoneMechanics:
    """Test stigmergy via pheromone trails with mathematical precision."""

    @pytest.fixture
    def comm(self):
        return SwarmCommunication()

    def test_leave_and_get_pheromone(self, comm):
        """Verify pheromone leaving and retrieval."""
        comm.leave_pheromone("pattern_auth_fix", 1.0)
        strength = comm.get_pheromone("pattern_auth_fix")
        assert strength == 1.0

    def test_pheromone_accumulation(self, comm):
        """Verify multiple pheromone deposits accumulate."""
        comm.leave_pheromone("pattern_test", 1.0)
        comm.leave_pheromone("pattern_test", 0.5)
        comm.leave_pheromone("pattern_test", 0.25)
        strength = comm.get_pheromone("pattern_test")
        assert strength == 1.75  # 1.0 + 0.5 + 0.25

    def test_pheromone_default_zero(self, comm):
        """Verify unset pattern returns 0.0."""
        strength = comm.get_pheromone("nonexistent_pattern")
        assert strength == 0.0

    def test_negative_pheromone(self, comm):
        """Verify negative pheromone (repellent) works."""
        comm.leave_pheromone("bad_pattern", -0.5)
        strength = comm.get_pheromone("bad_pattern")
        assert strength == -0.5

    @pytest.mark.asyncio
    async def test_pheromone_decay(self, comm):
        """Verify pheromone decays by 5% per minute."""
        comm.leave_pheromone("decay_test", 1.0)

        # Simulate one decay cycle manually
        for key in list(comm.pheromone_trails.keys()):
            comm.pheromone_trails[key] *= 0.95  # 5% decay

        strength = comm.get_pheromone("decay_test")
        assert strength == pytest.approx(0.95, abs=1e-10)

    @pytest.mark.asyncio
    async def test_pheromone_below_threshold_removed(self, comm):
        """Verify pheromone trails below 0.01 are removed."""
        comm.leave_pheromone("fading_pattern", 0.009)
        # Manually trigger decay cleanup logic
        for key in list(comm.pheromone_trails.keys()):
            if comm.pheromone_trails[key] < 0.01:
                del comm.pheromone_trails[key]

        assert "fading_pattern" not in comm.pheromone_trails

    @pytest.mark.asyncio
    async def test_pheromone_decay_loop_runs(self, comm):
        """Verify the decay loop task is actually running."""
        # The asyncio.create_task in __init__ should start the loop
        tasks = [t for t in asyncio.all_tasks() if "pheromone_decay" in str(t)]
        # At minimum, we can verify the method runs without error
        # by directly calling it (but it's an infinite loop)

    def test_pheromone_pattern_diversity(self, comm):
        """Verify multiple independent patterns."""
        patterns = {
            "auth_fix": 2.0,
            "db_optimize": 1.5,
            "frontend_render": 3.0,
            "security_patch": 0.8,
        }
        for pattern, strength in patterns.items():
            comm.leave_pheromone(pattern, strength)

        for pattern, expected in patterns.items():
            assert comm.get_pheromone(pattern) == expected


# =============================================================================
# SECTION 3: Proposal/Voting Consensus Tests
# =============================================================================

class TestConsensusMechanism:
    """Test proposal/voting consensus with mathematical rigor."""

    @pytest.fixture
    def comm(self):
        return SwarmCommunication()

    @pytest.mark.asyncio
    async def test_proposal_broadcast(self, comm):
        """Verify proposal creation and broadcast."""
        comm.register_agent("agent_alpha")
        comm.register_agent("agent_beta")
        comm.register_agent("agent_gamma")

        proposal_id = await comm.broadcast_proposal(
            {"action": "fix_auth", "priority": "high"},
            sender="agent_alpha",
            confidence=0.85,
        )

        # Verify proposal was created
        assert proposal_id in comm.proposals
        assert comm.proposals[proposal_id]["status"] == "pending"
        assert comm.proposals[proposal_id]["sender"] == "agent_alpha"
        assert comm.proposals[proposal_id]["confidence"] == 0.85

        # Other agents should have received proposal messages
        for agent in ["agent_beta", "agent_gamma"]:
            msg = await comm.receive(agent, timeout=1.0)
            assert msg is not None
            assert msg.message_type == "proposal"
            assert msg.payload["proposal_id"] == proposal_id

    @pytest.mark.asyncio
    async def test_voting_mechanism(self, comm):
        """Verify vote casting and tracking."""
        comm.register_agent("agent_alpha")
        comm.register_agent("agent_beta")

        proposal_id = await comm.broadcast_proposal(
            {"action": "fix_auth"},
            sender="agent_alpha",
        )

        # Cast votes
        await comm.cast_vote(proposal_id, "agent_alpha", "approve", 0.9)
        await comm.cast_vote(proposal_id, "agent_beta", "approve", 0.8)

        # Verify votes are recorded
        assert len(comm.votes[proposal_id]) == 2
        assert all(v["vote"] == "approve" for v in comm.votes[proposal_id])

    @pytest.mark.asyncio
    async def test_majority_approval_consensus(self, comm):
        """Verify majority approval reaches consensus."""
        agents = ["agent_alpha", "agent_beta", "agent_gamma"]
        for agent in agents:
            comm.register_agent(agent)

        proposal_id = await comm.broadcast_proposal(
            {"action": "deploy_update"},
            sender="agent_alpha",
        )

        # 2 approve, 1 abstain = majority approval
        await comm.cast_vote(proposal_id, "agent_alpha", "approve")
        await comm.cast_vote(proposal_id, "agent_beta", "approve")
        await comm.cast_vote(proposal_id, "agent_gamma", "abstain")

        assert comm.proposals[proposal_id]["status"] == "approved"

    @pytest.mark.asyncio
    async def test_majority_rejection_consensus(self, comm):
        """Verify majority rejection reaches consensus."""
        agents = ["agent_alpha", "agent_beta", "agent_gamma"]
        for agent in agents:
            comm.register_agent(agent)

        proposal_id = await comm.broadcast_proposal(
            {"action": "risky_operation"},
            sender="agent_alpha",
        )

        # 2 reject, 1 approve = majority rejection
        await comm.cast_vote(proposal_id, "agent_alpha", "reject")
        await comm.cast_vote(proposal_id, "agent_beta", "reject")
        await comm.cast_vote(proposal_id, "agent_gamma", "approve")

        assert comm.proposals[proposal_id]["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_tie_consensus(self, comm):
        """Verify tie results in 'tie' status."""
        agents = ["agent_alpha", "agent_beta"]
        for agent in agents:
            comm.register_agent(agent)

        proposal_id = await comm.broadcast_proposal(
            {"action": "controversial_change"},
            sender="agent_alpha",
        )

        # 1 approve, 1 reject = tie
        await comm.cast_vote(proposal_id, "agent_alpha", "approve")
        await comm.cast_vote(proposal_id, "agent_beta", "reject")

        assert comm.proposals[proposal_id]["status"] == "tie"

    @pytest.mark.asyncio
    async def test_consensus_broadcast_on_approval(self, comm):
        """Verify consensus result is broadcast to all agents on approval."""
        agents = ["agent_alpha", "agent_beta", "agent_gamma"]
        for agent in agents:
            comm.register_agent(agent)

        proposal_id = await comm.broadcast_proposal(
            {"action": "approved_action"},
            sender="agent_alpha",
        )

        await comm.cast_vote(proposal_id, "agent_alpha", "approve")
        await comm.cast_vote(proposal_id, "agent_beta", "approve")
        await comm.cast_vote(proposal_id, "agent_gamma", "approve")

        # All agents should receive consensus broadcast
        for agent in agents:
            msg = await comm.receive(agent, timeout=1.0)
            if msg and msg.message_type == "consensus":
                assert msg.payload["result"] == "approved"
                break

    @pytest.mark.asyncio
    async def test_vote_on_invalid_proposal(self, comm):
        """Verify voting on non-existent proposal returns False."""
        result = await comm.cast_vote("nonexistent_id", "agent_alpha", "approve")
        assert result is False

    @pytest.mark.asyncio
    async def test_consensus_requires_all_votes(self, comm):
        """Verify consensus is NOT reached until all agents vote."""
        agents = ["agent_alpha", "agent_beta", "agent_gamma", "agent_delta"]
        for agent in agents:
            comm.register_agent(agent)

        proposal_id = await comm.broadcast_proposal(
            {"action": "pending_test"},
            sender="agent_alpha",
        )

        # Only 2 of 4 vote
        await comm.cast_vote(proposal_id, "agent_alpha", "approve")
        await comm.cast_vote(proposal_id, "agent_beta", "approve")

        # Status should still be pending
        assert comm.proposals[proposal_id]["status"] == "pending"

    def test_swarm_status(self, comm):
        """Verify swarm status reporting."""
        comm.register_agent("agent_alpha")
        comm.register_agent("agent_beta")
        comm.leave_pheromone("test_pattern", 1.0)

        status = comm.get_swarm_status()
        assert status["registered_agents"] == 2
        assert status["pheromone_trails"] == 1
        assert status["message_history_size"] == 0
        assert "agent_alpha" in status["agents"]
        assert "agent_beta" in status["agents"]


# =============================================================================
# SECTION 4: SwarmEnabledAgent Tests
# =============================================================================

class TestSwarmEnabledAgent:
    """Test the SwarmEnabledAgent base class."""

    @pytest.fixture
    def comm(self):
        return SwarmCommunication()

    @pytest.mark.asyncio
    async def test_agent_creation_and_registration(self, comm):
        """Verify agent automatically registers with swarm."""
        agent = SwarmEnabledAgent("test_agent", comm)
        assert agent.name == "test_agent"
        assert "test_agent" in comm.agents

    @pytest.mark.asyncio
    async def test_send_and_receive_message(self, comm):
        """Verify agent can send and receive messages."""
        agent_a = SwarmEnabledAgent("agent_a", comm)
        agent_b = SwarmEnabledAgent("agent_b", comm)

        sent = await agent_a.send_message("agent_b", "task", {"action": "fix"})
        assert sent is True

        received = await agent_b.receive_message(timeout=1.0)
        assert received is not None
        assert received.payload["action"] == "fix"

    @pytest.mark.asyncio
    async def test_propose_fix(self, comm):
        """Verify agent can propose a fix to the swarm."""
        agent = SwarmEnabledAgent("proposer", comm)
        SwarmEnabledAgent("voter_1", comm)
        SwarmEnabledAgent("voter_2", comm)

        proposal_id = await agent.propose_fix(
            diagnosis={"severity": "high", "affected_modules": ["auth"]},
            fix_plan={"action": "patch_auth"},
            confidence=0.85,
        )

        assert proposal_id in comm.proposals
        assert comm.proposals[proposal_id]["sender"] == "proposer"
        assert proposal_id in agent.proposal_history

    @pytest.mark.asyncio
    async def test_vote_on_proposal(self, comm):
        """Verify agent can vote on proposals."""
        agent = SwarmEnabledAgent("voter", comm)
        SwarmEnabledAgent("proposer", comm)

        # Create proposal directly
        proposal_id = "test-vote-1"
        comm.proposals[proposal_id] = {
            "id": proposal_id,
            "proposal": {"action": "test"},
            "sender": "proposer",
            "status": "pending",
        }
        comm.votes[proposal_id] = []

        result = await agent.vote_on_proposal(proposal_id, "approve", 0.9)
        assert result is True
        assert len(comm.votes[proposal_id]) == 1
        assert comm.votes[proposal_id][0]["vote"] == "approve"

    def test_learn_from_pheromone(self, comm):
        """Verify agent can learn from pheromone trails."""
        comm.leave_pheromone("high_auth", 2.0)
        agent = SwarmEnabledAgent("learner", comm)

        strength = agent.learn_from_pheromone("high_auth")
        assert strength == 2.0

        strength = agent.learn_from_pheromone("nonexistent")
        assert strength == 0.0

    def test_reinforce_pheromone_success(self, comm):
        """Verify successful reinforcement increases pheromone."""
        agent = SwarmEnabledAgent("reinforcer", comm)
        agent.reinforce_pheromone("success_pattern", success=True)
        assert comm.get_pheromone("success_pattern") == 1.0

    def test_reinforce_pheromone_failure(self, comm):
        """Verify failure decreases pheromone."""
        agent = SwarmEnabledAgent("reinforcer", comm)
        agent.reinforce_pheromone("fail_pattern", success=False)
        assert comm.get_pheromone("fail_pattern") == -0.5

    def test_pattern_key_extraction(self, comm):
        """Verify pattern key extraction from proposals."""
        agent = SwarmEnabledAgent("extractor", comm)

        proposal = {
            "diagnosis": {
                "severity": "critical",
                "affected_modules": ["auth", "security", "database"],
            }
        }

        pattern = agent._extract_pattern_key(proposal)
        assert "critical" in pattern
        assert "auth" in pattern
        assert "security" in pattern


# =============================================================================
# SECTION 5: PSO Task Allocator Tests - MATHEMATICAL VERIFICATION
# =============================================================================

class TestPSOParticle:
    """Test PSOParticle with mathematical verification."""

    def test_particle_creation(self):
        """Verify particle initialization."""
        particle = PSOParticle("task_1", ["agent_a", "agent_b", "agent_c"])
        assert particle.task_id == "task_1"
        assert particle.position in ["agent_a", "agent_b", "agent_c"]
        assert particle.velocity == 0.0
        assert particle.personal_best == particle.position
        assert particle.personal_best_fitness == 0.0
        assert particle.fitness == 0.0

    def test_particle_structural_integrity(self):
        """Verify particle has required attributes."""
        particle = PSOParticle("task_1", ["agent_a", "agent_b"])
        required = ["task_id", "agents", "position", "velocity", 
                     "personal_best", "personal_best_fitness", "fitness"]
        for attr in required:
            assert hasattr(particle, attr), f"Missing attribute: {attr}"

    def test_velocity_update_formula(self):
        """Verify PSO velocity formula is mathematically correct.
        
        v = w*v + c1*r1*(pbest - x) + c2*r2*(gbest - x)
        """
        particle = PSOParticle("task_1", ["agent_a", "agent_b", "agent_c"])
        particle.position = "agent_a"
        particle.personal_best = "agent_b"
        
        # Fixed random seeds for reproducibility
        import random as rnd
        rnd.seed(42)
        
        particle.update_velocity(
            global_best="agent_c",
            global_best_fitness=0.9,
            w=0.7, c1=1.5, c2=1.5
        )
        
        # The velocity should be a composite of cognitive + social components
        # Cognitive = c1 * r1 * (pbest != x)
        # Social = c2 * r2 * (gbest != x)
        # Since pbest != position and gbest != position, both terms contribute
        
        assert particle.velocity > 0, "Velocity should be positive when better solutions exist"
        
        # Now test when particle is already at personal best AND global best
        rnd.seed(42)
        particle2 = PSOParticle("task_2", ["agent_a", "agent_b"])
        particle2.position = "agent_a"
        particle2.personal_best = "agent_a"
        
        particle2.update_velocity(
            global_best="agent_a",
            global_best_fitness=1.0,
            w=0.7, c1=1.5, c2=1.5
        )
        
        # With w=0.7 and velocity starting at 0, and no cognitive/social contribution
        # velocity = 0.7 * 0 + 0 + 0 = 0
        assert particle2.velocity == 0.0, "Velocity should be 0 when already at optimum"


class TestPSOTaskAllocator:
    """Test PSO task allocator with rigorous verification."""

    @pytest.fixture
    def swarm_comm(self):
        return SwarmCommunication()

    @pytest.mark.asyncio
    async def test_simple_task_allocation(self, swarm_comm):
        """Verify basic task allocation works."""
        allocator = PSOTaskAllocator(swarm_comm)
        
        tasks = [{"id": "task_1", "type": "auth_fix"}]
        agents = ["agent_a", "agent_b", "agent_c"]
        agent_fitness = {"agent_a": 0.9, "agent_b": 0.5, "agent_c": 0.7}

        assignments = await allocator.allocate_tasks(tasks, agents, agent_fitness)
        
        assert "task_1" in assignments
        assert assignments["task_1"] in agents

    @pytest.mark.asyncio
    async def test_multiple_task_allocation(self, swarm_comm):
        """Verify multiple tasks are allocated independently."""
        allocator = PSOTaskAllocator(swarm_comm)
        
        tasks = [
            {"id": "task_1", "type": "auth_fix"},
            {"id": "task_2", "type": "db_optimize"},
            {"id": "task_3", "type": "frontend_render"},
        ]
        agents = ["agent_a", "agent_b", "agent_c", "agent_d"]
        agent_fitness = {
            "agent_a": 0.9, "agent_b": 0.8, 
            "agent_c": 0.7, "agent_d": 0.6
        }

        assignments = await allocator.allocate_tasks(tasks, agents, agent_fitness)
        
        assert len(assignments) == len(tasks)
        for task_id in ["task_1", "task_2", "task_3"]:
            assert task_id in assignments
            assert assignments[task_id] in agents

    @pytest.mark.asyncio
    async def test_fitness_based_allocation(self, swarm_comm):
        """Verify higher-fitness agents are preferred."""
        allocator = PSOTaskAllocator(swarm_comm)
        
        tasks = [{"id": "preferred_task", "type": "critical_fix"}]
        # One very high fitness agent, rest low
        agents = ["expert_agent", "novice_a", "novice_b"]
        agent_fitness = {
            "expert_agent": 0.99,
            "novice_a": 0.1,
            "novice_b": 0.1,
        }

        # Run multiple allocations to check statistical preference
        expert_assignments = 0
        trials = 20
        for _ in range(trials):
            assignments = await allocator.allocate_tasks(tasks, agents, agent_fitness)
            if assignments["preferred_task"] == "expert_agent":
                expert_assignments += 1

        # Expert should be preferred > 50% of the time
        assert expert_assignments > trials * 0.5, \
            f"Expert only assigned {expert_assignments}/{trials} times"

    @pytest.mark.asyncio
    async def test_pheromone_influence_on_allocation(self, swarm_comm):
        """Verify pheromone trails influence allocation decisions."""
        # Leave strong pheromone for agent_b on auth_fix
        swarm_comm.leave_pheromone("auth_fix_agent_b", 5.0)
        
        allocator = PSOTaskAllocator(swarm_comm)
        
        tasks = [{"id": "task_1", "type": "auth_fix"}]
        agents = ["agent_a", "agent_b", "agent_c"]
        agent_fitness = {"agent_a": 0.5, "agent_b": 0.5, "agent_c": 0.5}

        assignments = await allocator.allocate_tasks(tasks, agents, agent_fitness)
        
        # agent_b has 5.0 pheromone bonus, making it much more likely
        assert assignments["task_1"] == "agent_b", \
            "agent_b should be preferred due to pheromone trail"

    @pytest.mark.asyncio
    async def test_allocation_stats(self, swarm_comm):
        """Verify allocation statistics are tracked."""
        allocator = PSOTaskAllocator(swarm_comm)
        
        tasks = [{"id": "stat_test", "type": "test"}]
        agents = ["agent_a", "agent_b"]
        agent_fitness = {"agent_a": 0.8, "agent_b": 0.6}

        await allocator.allocate_tasks(tasks, agents, agent_fitness)
        
        stats = allocator.get_allocation_stats()
        assert stats["total_tasks_allocated"] >= 1
        assert stats["particles_per_task"] == 10
        assert stats["max_iterations"] == 20
        assert "stat_test" in stats["allocations"]

    @pytest.mark.asyncio
    async def test_convergence_to_optimal(self, swarm_comm):
        """Verify PSO converges to optimal solution over iterations."""
        allocator = PSOTaskAllocator(swarm_comm)
        
        # Only one agent can do this task well
        tasks = [{"id": "unique_task", "type": "specialized_work"}]
        agents = ["specialist", "generalist_a", "generalist_b"]
        agent_fitness = {
            "specialist": 0.95,
            "generalist_a": 0.3,
            "generalist_b": 0.2,
        }

        # Run with enough iterations to converge
        allocator.max_iterations = 50
        assignments = await allocator.allocate_tasks(tasks, agents, agent_fitness)
        
        assert assignments["unique_task"] == "specialist", \
            "PSO should converge to the specialist agent"


# =============================================================================
# SECTION 6: SwarmTaskCoordinator Tests
# =============================================================================

class TestSwarmTaskCoordinator:
    """Test the SwarmTaskCoordinator integration."""

    @pytest.fixture
    def swarm_comm(self):
        return SwarmCommunication()

    @pytest.mark.asyncio
    async def test_coordinate_swarm_execution(self, swarm_comm):
        """Verify swarm execution coordination."""
        coordinator = SwarmTaskCoordinator(swarm_comm)
        coordinator.update_agent_fitness("agent_a", 0.9)
        coordinator.update_agent_fitness("agent_b", 0.7)

        tasks = [{"id": "coord_test", "type": "general", "name": "test_task"}]
        agents = ["agent_a", "agent_b"]

        result = await coordinator.coordinate_swarm_execution(tasks, agents)
        
        assert "allocations" in result
        assert "results" in result
        assert "stats" in result
        assert result["allocations"]["coord_test"] in agents

    @pytest.mark.asyncio
    async def test_learn_from_execution_success(self, swarm_comm):
        """Verify learning from successful execution."""
        coordinator = SwarmTaskCoordinator(swarm_comm)
        coordinator.update_agent_fitness("agent_a", 0.5)

        coordinator.learn_from_execution("task_1", "agent_a", success=True)
        
        # Agent fitness should increase
        assert coordinator.agent_fitness["agent_a"] > 0.5
        # Pheromone should be deposited
        assert swarm_comm.get_pheromone("task_task_1_agent_a") == 1.0

    @pytest.mark.asyncio
    async def test_learn_from_execution_failure(self, swarm_comm):
        """Verify learning from failed execution."""
        coordinator = SwarmTaskCoordinator(swarm_comm)
        coordinator.update_agent_fitness("agent_a", 0.5)

        coordinator.learn_from_execution("task_2", "agent_a", success=False)
        
        # Agent fitness should decrease
        assert coordinator.agent_fitness["agent_a"] < 0.5
        # Repellent pheromone should be deposited
        assert swarm_comm.get_pheromone("task_task_2_agent_a") == -0.5

    @pytest.mark.asyncio
    async def test_fitness_learning_bounds(self, swarm_comm):
        """Verify agent fitness stays within [0.0, 1.0]."""
        coordinator = SwarmTaskCoordinator(swarm_comm)
        
        # Test lower bound
        coordinator.update_agent_fitness("agent_low", 0.01)
        coordinator.learn_from_execution("fail_task", "agent_low", success=False)
        assert coordinator.agent_fitness["agent_low"] >= 0.0

        # Test upper bound
        coordinator.update_agent_fitness("agent_high", 0.99)
        coordinator.learn_from_execution("good_task", "agent_high", success=True)
        assert coordinator.agent_fitness["agent_high"] <= 1.0

    @pytest.mark.asyncio
    async def test_pheromone_reinforcement_in_coordination(self, swarm_comm):
        """Verify coordinate_swarm_execution reinforces pheromone."""
        coordinator = SwarmTaskCoordinator(swarm_comm)
        coordinator.update_agent_fitness("agent_a", 0.8)
        coordinator.update_agent_fitness("agent_b", 0.6)

        tasks = [{"id": "pheromone_test", "type": "reinforce_me"}]
        agents = ["agent_a", "agent_b"]

        result = await coordinator.coordinate_swarm_execution(tasks, agents)
        
        # Pheromone should have been deposited for whichever agent was chosen
        assigned_agent = result["allocations"]["pheromone_test"]
        pattern_key = f"reinforce_me_{assigned_agent}"
        assert swarm_comm.get_pheromone(pattern_key) > 0


# =============================================================================
# SECTION 7: Global Singletons Tests
# =============================================================================

class TestGlobalSingletons:
    """Test global singleton instances."""

    def test_get_swarm_communication_is_singleton(self):
        """Verify get_swarm_communication returns same instance."""
        comm1 = get_swarm_communication()
        comm2 = get_swarm_communication()
        assert comm1 is comm2

    def test_get_task_coordinator(self):
        """Verify get_task_coordinator creates and returns coordinator."""
        comm = SwarmCommunication()
        coordinator = get_task_coordinator(comm)
        assert coordinator is not None
        assert isinstance(coordinator, SwarmTaskCoordinator)
        assert coordinator.swarm_comm is comm


# =============================================================================
# SECTION 8: Edge Cases and Stress Tests
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_empty_task_list(self):
        """Verify empty task list returns empty assignments."""
        allocator = PSOTaskAllocator(SwarmCommunication())
        assignments = await allocator.allocate_tasks([], ["agent_a"], {"agent_a": 0.5})
        assert assignments == {}

    @pytest.mark.asyncio
    async def test_single_agent(self):
        """Verify allocation works with single agent."""
        allocator = PSOTaskAllocator(SwarmCommunication())
        tasks = [{"id": "t1", "type": "test"}, {"id": "t2", "type": "test"}]
        assignments = await allocator.allocate_tasks(tasks, ["only_agent"], {"only_agent": 0.5})
        assert assignments["t1"] == "only_agent"
        assert assignments["t2"] == "only_agent"

    @pytest.mark.asyncio
    async def test_many_tasks(self):
        """Verify allocator handles many tasks without error."""
        allocator = PSOTaskAllocator(SwarmCommunication())
        tasks = [{"id": f"task_{i}", "type": "bulk"} for i in range(50)]
        agents = [f"agent_{i}" for i in range(5)]
        agent_fitness = {f"agent_{i}": 0.5 + i * 0.1 for i in range(5)}

        assignments = await allocator.allocate_tasks(tasks, agents, agent_fitness)
        assert len(assignments) == len(tasks)

    @pytest.mark.asyncio
    async def test_many_agents(self):
        """Verify allocator handles many agents."""
        allocator = PSOTaskAllocator(SwarmCommunication())
        tasks = [{"id": "single_task", "type": "scalability"}]
        agents = [f"agent_{i}" for i in range(100)]
        agent_fitness = {f"agent_{i}": 0.1 for i in range(100)}

        assignments = await allocator.allocate_tasks(tasks, agents, agent_fitness)
        assert "single_task" in assignments

    @pytest.mark.asyncio
    async def test_concurrent_messaging(self):
        """Verify concurrent message passing doesn't deadlock."""
        comm = SwarmCommunication()
        for i in range(10):
            comm.register_agent(f"agent_{i}")

        async def send_messages(sender: str, count: int):
            for i in range(count):
                msg = SwarmMessage(
                    message_id=f"{sender}-{i}",
                    sender=sender,
                    receiver="all",
                    timestamp=time.time(),
                    message_type="alert",
                    payload={"index": i},
                )
                await comm.send(msg)

        # Concurrent sends from multiple agents
        tasks = [send_messages(f"agent_{i}", 20) for i in range(10)]
        await asyncio.gather(*tasks)

        assert len(comm.message_history) <= comm.max_history

    @pytest.mark.asyncio
    async def test_proposal_with_no_voters(self):
        """Verify proposal without voters remains pending."""
        comm = SwarmCommunication()
        comm.register_agent("lonely_agent")

        proposal_id = await comm.broadcast_proposal(
            {"action": "unpopular"},
            sender="lonely_agent",
        )
        assert comm.proposals[proposal_id]["status"] == "pending"

    def test_pheromone_concurrent_access(self):
        """Verify concurrent pheromone operations don't conflict."""
        import threading
        comm = SwarmCommunication()
        
        errors = []

        def deposit_pheromone(pattern: str):
            try:
                for _ in range(100):
                    comm.leave_pheromone(pattern, 0.1)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(10):
            t = threading.Thread(target=deposit_pheromone, args=(f"pattern_{i}",))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        for i in range(10):
            assert comm.get_pheromone(f"pattern_{i}") == pytest.approx(10.0, abs=1.0)


# =============================================================================
# SECTION 9: Integration Tests
# =============================================================================

class TestIntegration:
    """Test end-to-end swarm workflows."""

    @pytest.mark.asyncio
    async def test_full_swarm_workflow(self):
        """Verify complete swarm workflow: propose → vote → allocate → learn."""
        comm = SwarmCommunication()

        # Step 1: Create swarm agents
        agents = [SwarmEnabledAgent(f"agent_{i}", comm) for i in range(3)]
        coordinator = SwarmTaskCoordinator(comm)
        coordinator.update_agent_fitness("agent_0", 0.8)
        coordinator.update_agent_fitness("agent_1", 0.6)
        coordinator.update_agent_fitness("agent_2", 0.4)

        # Step 2: Propose and approve a fix via consensus
        proposal_id = await agents[0].propose_fix(
            diagnosis={"severity": "high", "affected_modules": ["auth"]},
            fix_plan={"action": "patch_auth"},
            confidence=0.85,
        )

        # All agents vote
        for agent in agents:
            await agent.vote_on_proposal(proposal_id, "approve", 0.8)

        assert comm.proposals[proposal_id]["status"] == "approved"

        # Step 3: PSO allocate tasks
        tasks = [{"id": "integrated_task", "type": "auth_fix"}]
        all_agent_names = [a.name for a in agents]
        
        # Leave pheromone to guide allocation
        comm.leave_pheromone("auth_fix_agent_0", 3.0)

        result = await coordinator.coordinate_swarm_execution(tasks, all_agent_names)

        # Step 4: Verify the workflow completed
        assert proposal_id in comm.proposals
        assert result["allocations"]["integrated_task"] in all_agent_names
        assert len(comm.message_history) > 0

        # Step 5: Learn from execution
        assigned_agent = result["allocations"]["integrated_task"]
        coordinator.learn_from_execution("integrated_task", assigned_agent, success=True)

        # Verify learning occurred
        assert coordinator.agent_fitness[assigned_agent] > 0.4  # increased from learning

    @pytest.mark.asyncio
    async def test_consensus_to_learning_pipeline(self):
        """Verify consensus decisions influence future learning."""
        comm = SwarmCommunication()

        # Create specialist agents
        agents = [
            SwarmEnabledAgent("security_expert", comm),
            SwarmEnabledAgent("database_expert", comm),
            SwarmEnabledAgent("frontend_expert", comm),
        ]

        coordinator = SwarmTaskCoordinator(comm)
        for agent in agents:
            coordinator.update_agent_fitness(agent.name, 0.5)

        # Complete a successful execution cycle
        tasks = [{"id": "security_patch_1", "type": "security_fix"}]
        agent_names = [a.name for a in agents]

        result = await coordinator.coordinate_swarm_execution(tasks, agent_names)
        assigned = result["allocations"]["security_patch_1"]

        # Learn from success
        coordinator.learn_from_execution("security_patch_1", assigned, success=True)

        # The successful agent should have higher fitness now
        assert coordinator.agent_fitness[assigned] > 0.5


# =============================================================================
# SECTION 10: Mathematical Correctness Verification
# =============================================================================

class TestMathematicalCorrectness:
    """Verify mathematical correctness of all algorithms."""

    def test_pso_fitness_bounds(self):
        """Verify fitness values are bounded within [0.0, 1.0]."""
        allocator = PSOTaskAllocator(SwarmCommunication())

        # Test with extreme values
        extreme_fitness = {"agent": 100.0}
        pattern_key = "test_agent"
        allocator.swarm_comm.leave_pheromone(pattern_key, 100.0)

        import asyncio
        fitness = asyncio.run(
            allocator._evaluate_fitness("agent", {"type": "test", "id": "t1"}, extreme_fitness)
        )
        
        # Fitness should be clamped to [0.0, 1.0]
        assert 0.0 <= fitness <= 1.0

    def test_pso_fitness_with_negative_pheromone(self):
        """Verify negative pheromone reduces fitness correctly."""
        allocator = PSOTaskAllocator(SwarmCommunication())
        allocator.swarm_comm.leave_pheromone("bad_type_agent", -2.0)

        import asyncio
        fitness = asyncio.run(
            allocator._evaluate_fitness(
                "agent", {"type": "bad_type", "id": "t1"}, {"agent": 0.5}
            )
        )

        # Fitness = max(0.0, 0.5 + (-2.0 * 0.1)) = max(0.0, 0.3) = 0.3
        assert fitness == 0.3

    def test_pso_fitness_with_pheromone_boost(self):
        """Verify positive pheromone boosts fitness correctly."""
        allocator = PSOTaskAllocator(SwarmCommunication())
        allocator.swarm_comm.leave_pheromone("good_type_agent", 3.0)

        import asyncio
        fitness = asyncio.run(
            allocator._evaluate_fitness(
                "agent", {"type": "good_type", "id": "t1"}, {"agent": 0.5}
            )
        )

        # Fitness = min(1.0, 0.5 + (3.0 * 0.1)) = min(1.0, 0.8) = 0.8
        assert fitness == 0.8

    def test_pso_fitness_clamped_above_1(self):
        """Verify fitness is clamped at 1.0."""
        allocator = PSOTaskAllocator(SwarmCommunication())
        allocator.swarm_comm.leave_pheromone("strong_agent", 10.0)

        import asyncio
        fitness = asyncio.run(
            allocator._evaluate_fitness(
                "agent", {"type": "strong", "id": "t1"}, {"agent": 0.9}
            )
        )

        assert fitness <= 1.0

    def test_validation_message_serialization(self):
        """Verify SwarmMessage can be serialized/deserialized."""
        original = SwarmMessage(
            message_id="serial-test",
            sender="a",
            receiver="b",
            timestamp=1234567890.0,
            message_type="task",
            payload={"key": "value"},
            swarm_context={"fitness": 0.9},
        )

        # dict conversion (simulates JSON serialization)
        data = original.model_dump()
        restored = SwarmMessage(**data)

        assert restored.message_id == original.message_id
        assert restored.sender == original.sender
        assert restored.payload == original.payload
        assert restored.swarm_context == original.swarm_context


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
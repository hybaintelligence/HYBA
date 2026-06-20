from pathlib import Path

from pythia_mining.pythia_autonomous_mining_agent import (
    MiningChainState,
    PythiaAutonomousMiningAgent,
    PythiaPersistentMiningMemory,
)


def test_pythia_autonomous_lifecycle_submits_verified_share(tmp_path: Path) -> None:
    submitted = []

    def verifier(nonce: int, chain_state: MiningChainState) -> int:
        return 0 if nonce == 7 else chain_state.target + 1

    def submitter(nonce: int, hash_value: int, chain_state: MiningChainState) -> bool:
        submitted.append((nonce, hash_value, chain_state.block_height))
        return True

    memory = PythiaPersistentMiningMemory(tmp_path / "memory.json")
    agent = PythiaAutonomousMiningAgent(
        repo_structure={"repo": "HYBA_FULLSTACK", "pythia": "in_charge"},
        memory=memory,
        hash_verifier=verifier,
        share_submitter=submitter,
    )
    chain_state = MiningChainState(
        block_height=840000,
        pool_difficulty=1000.0,
        target=1,
        nonce_ranges=((0, 15),),
        job_id="job-1",
    )

    observation = agent.run_lifecycle(
        chain_state, max_candidates=16, requested_hashrate_ehs=2.0
    )

    assert observation.accepted is True
    assert observation.submitted is True
    assert observation.nonce == 7
    assert submitted == [(7, 0, 840000)]
    assert memory.accepted_nonces == [7]
    assert any(e["event_type"] == "pythia_plan_built" for e in memory.audit_events)
    assert memory.path and memory.path.exists()


def test_pythia_autonomous_plan_is_structured_not_grover() -> None:
    agent = PythiaAutonomousMiningAgent(repo_structure={"repo": "HYBA_FULLSTACK"})
    chain_state = MiningChainState(
        block_height=840001,
        pool_difficulty=2_000_000.0,
        target=100,
        nonce_ranges=((20, 35),),
    )

    plan = agent.build_plan(chain_state, max_candidates=8, requested_hashrate_ehs=5.0)

    assert plan.search_mode == "pythia_structured_autonomous_search"
    assert plan.grover_amplification_enabled is False
    assert len(plan.candidate_order) == 8
    assert all(20 <= nonce <= 35 for nonce in plan.candidate_order)
    assert plan.requested_hashrate_ehs <= agent.MAX_AUTONOMOUS_HASHRATE_EHS

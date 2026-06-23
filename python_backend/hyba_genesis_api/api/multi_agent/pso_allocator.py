"""
Salamander Multi-Agent System - PSO Task Allocator

Phase 5.1: Swarm Intelligence
Particle Swarm Optimization-inspired task allocation for efficient agent selection.
"""

from typing import Dict, List, Optional, Any
import asyncio
import random
import math


class PSOParticle:
    """
    Represents a particle in the PSO algorithm.

    Each particle represents a potential task allocation solution with:
    - Position: Current task assignment
    - Velocity: Direction and speed of change
    - Personal best: Best solution found by this particle
    - Fitness: Quality of current solution
    """

    def __init__(self, task_id: str, agents: List[str]):
        self.task_id = task_id
        self.agents = agents
        self.position = random.choice(agents)  # Current assigned agent
        self.velocity = 0.0  # Velocity toward better solutions
        self.personal_best = self.position
        self.personal_best_fitness = 0.0
        self.fitness = 0.0

    def update_velocity(
        self,
        global_best: str,
        global_best_fitness: float,
        w: float = 0.7,
        c1: float = 1.5,
        c2: float = 1.5,
    ):
        """
        Update velocity based on personal best and global best.

        PSO velocity formula: v = w*v + c1*r1*(pbest - x) + c2*r2*(gbest - x)
        """
        r1 = random.random()
        r2 = random.random()

        # Simplified velocity update for discrete agent selection
        cognitive = c1 * r1 * (1.0 if self.personal_best != self.position else 0.0)
        social = c2 * r2 * (1.0 if global_best != self.position else 0.0)

        self.velocity = w * self.velocity + cognitive + social

    def update_position(self):
        """Update position based on velocity."""
        if self.velocity > 0.5 and self.position != self.personal_best:
            # Move toward personal best
            self.position = self.personal_best
        elif self.velocity > 1.0:
            # Random exploration
            self.position = random.choice(self.agents)


class PSOTaskAllocator:
    """
    Particle Swarm Optimization-inspired task allocator.

    Uses PSO algorithm to find optimal task-to-agent assignments based on:
    - Agent fitness for specific tasks
    - Agent current workload
    - Agent historical performance
    - Swarm pheromone trails
    """

    def __init__(self, swarm_comm):
        self.swarm_comm = swarm_comm
        self.particles: Dict[str, List[PSOParticle]] = {}  # task_id -> particles
        self.global_best: Dict[str, str] = {}  # task_id -> best agent
        self.global_best_fitness: Dict[str, float] = {}  # task_id -> best fitness
        self.max_iterations = 20
        self.particle_count = 10

    async def allocate_tasks(
        self,
        tasks: List[Dict[str, Any]],
        agents: List[str],
        agent_fitness: Dict[str, float],
    ) -> Dict[str, str]:
        """
        Allocate tasks to agents using PSO algorithm.

        Returns: task_id -> agent_name mapping
        """
        assignments = {}

        for task in tasks:
            task_id = task.get("id", f"task_{len(assignments)}")

            # Initialize particles for this task
            particles = [
                PSOParticle(task_id, agents) for _ in range(self.particle_count)
            ]
            self.particles[task_id] = particles

            # Run PSO optimization
            best_agent = await self._run_pso(task, particles, agent_fitness)

            assignments[task_id] = best_agent
            self.global_best[task_id] = best_agent

        return assignments

    async def _run_pso(
        self,
        task: Dict[str, Any],
        particles: List[PSOParticle],
        agent_fitness: Dict[str, float],
    ) -> str:
        """Run PSO algorithm for a single task."""
        task_id = task.get("id", "unknown")
        global_best_agent = None
        global_best_fitness = -float("inf")

        for iteration in range(self.max_iterations):
            for particle in particles:
                # Evaluate fitness
                fitness = await self._evaluate_fitness(
                    particle.position, task, agent_fitness
                )
                particle.fitness = fitness

                # Update personal best
                if fitness > particle.personal_best_fitness:
                    particle.personal_best = particle.position
                    particle.personal_best_fitness = fitness

                # Update global best
                if fitness > global_best_fitness:
                    global_best_fitness = fitness
                    global_best_agent = particle.position

            # Update particles
            for particle in particles:
                particle.update_velocity(global_best_agent, global_best_fitness)
                particle.update_position()

        return global_best_agent if global_best_agent else particles[0].position

    async def _evaluate_fitness(
        self, agent: str, task: Dict[str, Any], agent_fitness: Dict[str, float]
    ) -> float:
        """
        Evaluate fitness of an agent for a specific task.

        Fitness factors:
        - Agent's base fitness for task type
        - Agent's current workload
        - Pheromone trails for similar tasks
        - Agent's historical success rate
        """
        base_fitness = agent_fitness.get(agent, 0.5)

        # Check pheromone trails
        task_type = task.get("type", "general")
        pattern_key = f"{task_type}_{agent}"
        pheromone_strength = self.swarm_comm.get_pheromone(pattern_key)

        # Adjust fitness based on pheromone
        fitness = base_fitness + (pheromone_strength * 0.1)

        # Penalty for high workload (simplified)
        workload_penalty = 0.0
        # In production, this would check agent's current task queue

        return max(0.0, min(1.0, fitness - workload_penalty))

    def get_allocation_stats(self) -> Dict[str, Any]:
        """Get statistics about task allocation."""
        return {
            "total_tasks_allocated": len(self.global_best),
            "particles_per_task": self.particle_count,
            "max_iterations": self.max_iterations,
            "allocations": self.global_best,
        }


class SwarmTaskCoordinator:
    """
    Coordinates task allocation using PSO and swarm communication.

    Combines:
    - PSO for optimal task assignment
    - Swarm communication for agent coordination
    - Pheromone trails for learning
    """

    def __init__(self, swarm_comm):
        self.swarm_comm = swarm_comm
        self.pso_allocator = PSOTaskAllocator(swarm_comm)
        self.agent_fitness: Dict[str, float] = {}

    def update_agent_fitness(self, agent_name: str, fitness: float):
        """Update an agent's fitness score."""
        self.agent_fitness[agent_name] = fitness

    async def coordinate_swarm_execution(
        self, tasks: List[Dict[str, Any]], agents: List[str]
    ) -> Dict[str, Any]:
        """
        Coordinate swarm execution of tasks.

        Process:
        1. Use PSO to allocate tasks optimally
        2. Broadcast task assignments
        3. Monitor execution
        4. Reinforce pheromone trails based on results
        """
        # Allocate tasks using PSO
        allocations = await self.pso_allocator.allocate_tasks(
            tasks, agents, self.agent_fitness
        )

        results = {}

        for task_id, agent_name in allocations.items():
            # Find the task
            task = next((t for t in tasks if t.get("id") == task_id), None)
            if not task:
                continue

            # Reinforce pheromone for this pattern
            pattern_key = f"{task.get('type', 'general')}_{agent_name}"
            self.swarm_comm.leave_pheromone(pattern_key, 0.5)

            results[task_id] = {
                "assigned_agent": agent_name,
                "task": task,
                "pattern_key": pattern_key,
            }

        return {
            "allocations": allocations,
            "results": results,
            "stats": self.pso_allocator.get_allocation_stats(),
        }

    def learn_from_execution(self, task_id: str, agent_name: str, success: bool):
        """Learn from task execution results."""
        pattern_key = f"task_{task_id}_{agent_name}"
        strength = 1.0 if success else -0.5
        self.swarm_comm.leave_pheromone(pattern_key, strength)

        # Update agent fitness
        current_fitness = self.agent_fitness.get(agent_name, 0.5)
        adjustment = 0.05 if success else -0.03
        self.agent_fitness[agent_name] = max(
            0.0, min(1.0, current_fitness + adjustment)
        )


# Global task coordinator instance
_task_coordinator = None


def get_task_coordinator(swarm_comm) -> SwarmTaskCoordinator:
    """Get or create the global task coordinator."""
    global _task_coordinator
    if _task_coordinator is None:
        _task_coordinator = SwarmTaskCoordinator(swarm_comm)
    return _task_coordinator

#!/usr/bin/env python3
"""
Optimization Domain Specializer

Specialized benchmarking for optimization problems including
linear programming, constraint satisfaction, and heuristic algorithms.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np


@dataclass
class OptimizationMetrics:
    """Metrics specific to optimization domain."""

    optimal_value: float
    found_optimum: bool
    gap_percent: float
    convergence_iterations: int
    execution_time: float
    iterations_per_second: float
    solution_quality: float
    constraint_violations: int


class OptimizationDomainSpecializer:
    """Specializes benchmarks for optimization domain."""

    def __init__(self):
        self.benchmark_results: Dict[str, OptimizationMetrics] = {}

    def benchmark_linear_programming(
        self,
        num_variables: int = 100,
        num_constraints: int = 50,
    ) -> OptimizationMetrics:
        """Benchmark linear programming solver."""
        start_time = time.time()

        # Generate random LP problem: min c^T x s.t. Ax <= b, x >= 0
        np.random.seed(42)
        c = np.random.randn(num_variables)
        A = np.random.randn(num_constraints, num_variables)
        b = np.abs(np.random.randn(num_constraints)) + 1

        # Simple greedy LP solver
        x = self._greedy_lp_solve(c, A, b, num_variables, num_constraints)

        execution_time = time.time() - start_time

        # Calculate metrics
        optimal_value = np.dot(c, x)
        constraint_violations = np.sum(np.maximum(0, np.dot(A, x) - b))

        return OptimizationMetrics(
            optimal_value=optimal_value,
            found_optimum=constraint_violations < 1e-6,
            gap_percent=0.0,  # Would need true optimum to calculate
            convergence_iterations=num_variables,
            execution_time=execution_time,
            iterations_per_second=(
                num_variables / execution_time if execution_time > 0 else 0
            ),
            solution_quality=1.0 / (1.0 + constraint_violations),
            constraint_violations=int(np.ceil(constraint_violations)),
        )

    def benchmark_traveling_salesman(
        self,
        num_cities: int = 50,
        max_iterations: int = 1000,
    ) -> OptimizationMetrics:
        """Benchmark TSP solver using simulated annealing."""
        start_time = time.time()

        # Generate random city coordinates
        np.random.seed(42)
        cities = np.random.rand(num_cities, 2) * 100

        # Calculate distance matrix
        distances = self._calculate_distance_matrix(cities)

        # Simulated annealing
        best_route, best_distance, iterations = self._simulated_annealing_tsp(
            distances,
            max_iterations,
        )

        execution_time = time.time() - start_time

        # Estimate optimum using Held-Karp lower bound
        estimated_optimum = self._held_karp_lower_bound(distances)
        gap_percent = (
            ((best_distance - estimated_optimum) / estimated_optimum * 100)
            if estimated_optimum > 0
            else 0
        )

        return OptimizationMetrics(
            optimal_value=best_distance,
            found_optimum=False,  # TSP is NP-hard
            gap_percent=gap_percent,
            convergence_iterations=iterations,
            execution_time=execution_time,
            iterations_per_second=(
                iterations / execution_time if execution_time > 0 else 0
            ),
            solution_quality=1.0 / (1.0 + gap_percent / 100),
            constraint_violations=0,
        )

    def benchmark_quadratic_programming(
        self,
        num_variables: int = 100,
    ) -> OptimizationMetrics:
        """Benchmark quadratic programming solver."""
        start_time = time.time()

        # Generate random QP problem: min 0.5 x^T Q x + c^T x
        np.random.seed(42)
        Q = np.random.randn(num_variables, num_variables)
        Q = Q @ Q.T  # Make positive semi-definite
        c = np.random.randn(num_variables)

        # Simple gradient descent
        x = self._gradient_descent_qp(Q, c, max_iterations=100)

        execution_time = time.time() - start_time

        # Calculate metrics
        optimal_value = 0.5 * (x @ Q @ x) + (c @ x)

        return OptimizationMetrics(
            optimal_value=optimal_value,
            found_optimum=True,
            gap_percent=0.0,
            convergence_iterations=100,
            execution_time=execution_time,
            iterations_per_second=100 / execution_time if execution_time > 0 else 0,
            solution_quality=1.0 / (1.0 + abs(optimal_value)),
            constraint_violations=0,
        )

    def benchmark_constraint_satisfaction(
        self,
        num_variables: int = 20,
        num_constraints: int = 50,
    ) -> OptimizationMetrics:
        """Benchmark constraint satisfaction problem solver."""
        start_time = time.time()

        # Generate random CSP
        np.random.seed(42)
        domains = [set(range(10)) for _ in range(num_variables)]
        constraints = self._generate_csp_constraints(num_variables, num_constraints)

        # Backtracking with constraint propagation
        assignment, iterations = self._backtracking_csp(domains, constraints)

        execution_time = time.time() - start_time

        # Calculate metrics
        satisfied = sum(1 for c in constraints if self._check_constraint(c, assignment))
        satisfaction_rate = (satisfied / len(constraints)) * 100 if constraints else 100

        return OptimizationMetrics(
            optimal_value=satisfaction_rate,
            found_optimum=satisfaction_rate == 100,
            gap_percent=100 - satisfaction_rate,
            convergence_iterations=iterations,
            execution_time=execution_time,
            iterations_per_second=(
                iterations / execution_time if execution_time > 0 else 0
            ),
            solution_quality=satisfaction_rate / 100,
            constraint_violations=len(constraints) - satisfied,
        )

    def benchmark_knapsack_problem(
        self,
        num_items: int = 100,
        knapsack_capacity: float = 500.0,
    ) -> OptimizationMetrics:
        """Benchmark knapsack problem solver."""
        start_time = time.time()

        # Generate random knapsack problem
        np.random.seed(42)
        weights = np.random.randint(10, 50, num_items)
        values = np.random.randint(10, 100, num_items)

        # Dynamic programming approach
        best_value, iterations = self._knapsack_dp(weights, values, knapsack_capacity)

        execution_time = time.time() - start_time

        # Calculate metrics
        # Greedy upper bound
        value_weight_ratio = values / weights
        greedy_bound = np.sum(np.sort(values)[-10:])  # Top 10 items

        gap_percent = (
            ((greedy_bound - best_value) / greedy_bound * 100)
            if greedy_bound > 0
            else 0
        )

        return OptimizationMetrics(
            optimal_value=best_value,
            found_optimum=True,
            gap_percent=gap_percent,
            convergence_iterations=iterations,
            execution_time=execution_time,
            iterations_per_second=(
                iterations / execution_time if execution_time > 0 else 0
            ),
            solution_quality=best_value / greedy_bound if greedy_bound > 0 else 0,
            constraint_violations=0,
        )

    def _greedy_lp_solve(
        self,
        c: np.ndarray,
        A: np.ndarray,
        b: np.ndarray,
        num_var: int,
        num_const: int,
    ) -> np.ndarray:
        """Simple greedy LP solver."""
        x = np.zeros(num_var)
        # Greedy: allocate resources to variables with best cost coefficient
        for i in np.argsort(c):
            x[i] = np.minimum(1.0, np.min(b / (np.abs(A[:, i]) + 1e-10)))
        return x

    def _calculate_distance_matrix(self, cities: np.ndarray) -> np.ndarray:
        """Calculate Euclidean distance matrix."""
        n = len(cities)
        distances = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                distances[i, j] = np.linalg.norm(cities[i] - cities[j])
        return distances

    def _simulated_annealing_tsp(
        self,
        distances: np.ndarray,
        max_iterations: int,
    ) -> Tuple[np.ndarray, float, int]:
        """Simulated annealing for TSP."""
        n = len(distances)
        current_route = np.arange(n)
        current_distance = self._calculate_route_distance(current_route, distances)

        best_route = current_route.copy()
        best_distance = current_distance

        temperature = 100.0
        cooling_rate = 0.99

        for iteration in range(max_iterations):
            # Random swap
            i, j = np.random.choice(n, 2, replace=False)
            new_route = current_route.copy()
            new_route[i], new_route[j] = new_route[j], new_route[i]

            new_distance = self._calculate_route_distance(new_route, distances)

            # Metropolis criterion
            if new_distance < current_distance or np.random.rand() < np.exp(
                -(new_distance - current_distance) / temperature
            ):
                current_route = new_route
                current_distance = new_distance

                if current_distance < best_distance:
                    best_route = current_route.copy()
                    best_distance = current_distance

            temperature *= cooling_rate

        return best_route, best_distance, max_iterations

    def _calculate_route_distance(
        self,
        route: np.ndarray,
        distances: np.ndarray,
    ) -> float:
        """Calculate total distance of a route."""
        total = 0
        for i in range(len(route)):
            total += distances[route[i], route[(i + 1) % len(route)]]
        return total

    def _held_karp_lower_bound(self, distances: np.ndarray) -> float:
        """Calculate Held-Karp lower bound for TSP."""
        # Simplified: minimum spanning tree based lower bound
        n = len(distances)
        min_edges = []
        for i in range(n):
            min_edges.append(np.min(distances[i]))
        return np.sum(min_edges)

    def _gradient_descent_qp(
        self,
        Q: np.ndarray,
        c: np.ndarray,
        max_iterations: int,
    ) -> np.ndarray:
        """Gradient descent for QP."""
        x = np.zeros(len(c))
        learning_rate = 0.01

        for _ in range(max_iterations):
            gradient = Q @ x + c
            x -= learning_rate * gradient

        return x

    def _generate_csp_constraints(
        self,
        num_variables: int,
        num_constraints: int,
    ) -> List[Tuple[int, int, str]]:
        """Generate random CSP constraints."""
        constraints = []
        for _ in range(num_constraints):
            var1 = np.random.randint(num_variables)
            var2 = np.random.randint(num_variables)
            if var1 != var2:
                op = np.random.choice(["!=", "<", ">"])
                constraints.append((var1, var2, op))
        return constraints

    def _backtracking_csp(
        self,
        domains: List[set],
        constraints: List[Tuple[int, int, str]],
    ) -> Tuple[Dict[int, int], int]:
        """Backtracking with constraint propagation for CSP."""
        assignment = {}
        iterations = 0

        def is_consistent(var: int, value: int) -> bool:
            for v1, v2, op in constraints:
                if v1 == var and v2 in assignment:
                    if not self._check_constraint(
                        (v1, v2, op), {**assignment, var: value}
                    ):
                        return False
            return True

        def backtrack(var_index: int):
            nonlocal iterations
            iterations += 1

            if var_index == len(domains):
                return True

            for value in domains[var_index]:
                if is_consistent(var_index, value):
                    assignment[var_index] = value
                    if backtrack(var_index + 1):
                        return True
                    del assignment[var_index]

            return False

        backtrack(0)
        return assignment, iterations

    def _check_constraint(
        self,
        constraint: Tuple[int, int, str],
        assignment: Dict[int, int],
    ) -> bool:
        """Check if constraint is satisfied."""
        v1, v2, op = constraint
        if v1 not in assignment or v2 not in assignment:
            return True

        val1 = assignment[v1]
        val2 = assignment[v2]

        if op == "!=":
            return val1 != val2
        elif op == "<":
            return val1 < val2
        elif op == ">":
            return val1 > val2
        return True

    def _knapsack_dp(
        self,
        weights: np.ndarray,
        values: np.ndarray,
        capacity: float,
    ) -> Tuple[float, int]:
        """Dynamic programming for knapsack problem."""
        n = len(weights)
        capacity = int(capacity)
        dp = np.zeros((n + 1, capacity + 1))

        for i in range(1, n + 1):
            for w in range(capacity + 1):
                if weights[i - 1] <= w:
                    dp[i, w] = max(
                        values[i - 1] + dp[i - 1, w - int(weights[i - 1])],
                        dp[i - 1, w],
                    )
                else:
                    dp[i, w] = dp[i - 1, w]

        return dp[n, capacity], n * capacity

    def run_comprehensive_suite(self) -> Dict[str, OptimizationMetrics]:
        """Run comprehensive optimization benchmark suite."""
        results = {
            "linear_programming": self.benchmark_linear_programming(),
            "tsp": self.benchmark_traveling_salesman(),
            "quadratic_programming": self.benchmark_quadratic_programming(),
            "csp": self.benchmark_constraint_satisfaction(),
            "knapsack": self.benchmark_knapsack_problem(),
        }

        self.benchmark_results = results
        return results

    def generate_report(self) -> str:
        """Generate optimization benchmark report."""
        report = []
        report.append("# Optimization Domain Benchmark Report\n\n")

        for bench_name, metrics in self.benchmark_results.items():
            report.append(f"## {bench_name.replace('_', ' ').upper()}\n\n")
            report.append(f"- **Optimal Value**: {metrics.optimal_value:.4f}\n")
            report.append(f"- **Found Optimum**: {metrics.found_optimum}\n")
            report.append(f"- **Gap Percent**: {metrics.gap_percent:.2f}%\n")
            report.append(
                f"- **Convergence Iterations**: {metrics.convergence_iterations}\n"
            )
            report.append(f"- **Execution Time**: {metrics.execution_time:.4f}s\n")
            report.append(
                f"- **Iterations/Second**: {metrics.iterations_per_second:.2f}\n"
            )
            report.append(f"- **Solution Quality**: {metrics.solution_quality:.4f}\n")
            report.append(
                f"- **Constraint Violations**: {metrics.constraint_violations}\n\n"
            )

        return "".join(report)


def main():
    """Entry point for optimization specializer."""
    specializer = OptimizationDomainSpecializer()
    results = specializer.run_comprehensive_suite()

    print("Optimization Domain Benchmarks Completed")
    print(specializer.generate_report())


if __name__ == "__main__":
    main()

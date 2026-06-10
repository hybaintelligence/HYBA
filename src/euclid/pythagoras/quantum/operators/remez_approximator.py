"""
remez_approximator.py — Remez Exchange Algorithm for minimax polynomial approximation.
Computes the best uniform (L∞) polynomial approximation to a continuous function
on a closed interval using the Remez exchange method.
"""

from __future__ import annotations

from typing import Callable, List, Optional, Tuple

import numpy as np


class RemezApproximator:
    """
    Remez Exchange Algorithm for minimax polynomial approximation.

    Finds the polynomial P of degree ≤ n that minimizes max_{x in [a,b]} |f(x) - P(x)|.
    Convergence is quadratic near the solution for smooth functions.
    """

    def __init__(
        self,
        tol: float = 1e-10,
        max_iter: int = 50,
        dense_points: int = 10000,
    ) -> None:
        if tol <= 0:
            raise ValueError("tolerance must be positive")
        if max_iter < 1:
            raise ValueError("max_iter must be >= 1")
        self.tol = float(tol)
        self.max_iter = int(max_iter)
        self.dense_points = int(dense_points)

    @staticmethod
    def chebyshev_nodes(a: float, b: float, n: int) -> np.ndarray:
        """Return n Chebyshev nodes (roots of T_n) scaled to [a, b]."""
        if n < 1:
            raise ValueError("n must be >= 1")
        k = np.arange(1, n + 1, dtype=float)
        return 0.5 * (a + b) + 0.5 * (b - a) * np.cos(
            (2.0 * k - 1.0) * np.pi / (2.0 * n)
        )

    def approximate(
        self,
        f: Callable[[float], float],
        interval: Tuple[float, float],
        degree: int,
    ) -> Tuple[np.ndarray, float, List[np.ndarray]]:
        """
        Compute the minimax polynomial approximation of degree `degree` to f on [a,b].

        Args:
            f: Continuous function to approximate.
            interval: (a, b) closed interval.
            degree: Polynomial degree (≥ 0).

        Returns:
            coeffs: Polynomial coefficients (highest degree first, like np.polyfit).
            max_error: Estimated minimax deviation.
            ref_history: Evolution of reference points across iterations.
        """
        if degree < 0:
            raise ValueError("degree must be >= 0")
        a, b = interval
        if a >= b:
            raise ValueError("interval must satisfy a < b")

        num_ref = degree + 2
        x_ref = self.chebyshev_nodes(a, b, num_ref)
        ref_history: List[np.ndarray] = [x_ref.copy()]

        for iteration in range(self.max_iter):
            # Build the interpolation system
            # P(x_i) + (-1)^i * delta = f(x_i)  for i = 0..num_ref-1
            V = np.vander(x_ref, degree + 1, increasing=True)
            alt = (-1.0) ** np.arange(num_ref)
            A = np.column_stack([V, alt])
            rhs = np.array([f(xi) for xi in x_ref])

            try:
                sol = np.linalg.solve(A, rhs)
            except np.linalg.LinAlgError:
                sol = np.linalg.lstsq(A, rhs, rcond=None)[0]

            coeffs = sol[:-1]  # increasing degree order
            delta = sol[-1]

            # Evaluate error on dense grid
            x_dense = np.linspace(a, b, self.dense_points)
            fx = np.array([f(xi) for xi in x_dense])
            # Polyval wants highest degree first
            coeffs_high = coeffs[::-1]
            px = np.polyval(coeffs_high, x_dense)
            error = fx - px

            # Find new reference points: local extrema of |error|
            sign_changes = np.diff(np.sign(error))
            candidate_idx = np.where(sign_changes != 0)[0]

            if len(candidate_idx) < num_ref:
                # Fall back to uniform grid
                new_x = np.linspace(a, b, num_ref)
            else:
                # Pick alternating points with largest error
                candidates = x_dense[candidate_idx]
                err_at_candidates = np.abs(error[candidate_idx])
                top_idx = np.argsort(err_at_candidates)[::-1][: num_ref * 2]
                top_candidates = candidates[top_idx]
                err_top = error[
                    np.where(np.isin(x_dense, top_candidates))[0]
                ]

                # Enforce alternating signs
                selected = [top_candidates[0]]
                last_sign = np.sign(err_top[0])
                for xi, err_i in zip(top_candidates[1:], err_top[1:]):
                    if np.sign(err_i) != last_sign and len(selected) < num_ref:
                        selected.append(xi)
                        last_sign = np.sign(err_i)
                    elif len(selected) >= num_ref:
                        break

                if len(selected) < num_ref:
                    new_x = np.linspace(a, b, num_ref)
                else:
                    new_x = np.array(selected[:num_ref])

            ref_history.append(new_x.copy())

            # Convergence check: reference points stabilized
            if np.max(np.abs(new_x - x_ref)) < self.tol:
                break
            x_ref = new_x

        # Final solve to get converged coefficients
        V = np.vander(x_ref, degree + 1, increasing=True)
        alt = (-1.0) ** np.arange(num_ref)
        A = np.column_stack([V, alt])
        rhs = np.array([f(xi) for xi in x_ref])
        sol = np.linalg.solve(A, rhs)
        coeffs = sol[:-1]
        delta = sol[-1]

        coeffs_high = coeffs[::-1]  # highest degree first for polyval
        max_error = abs(delta)

        return coeffs_high, max_error, ref_history


__all__ = ["RemezApproximator"]
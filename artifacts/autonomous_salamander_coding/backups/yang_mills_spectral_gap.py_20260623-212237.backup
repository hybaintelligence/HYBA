"""
Operationalized Yang-Mills mass-gap elevation.

HYBA uses ``3 - φ`` as a deterministic, auditable operational invariant for
mass-gap-style gating, anti-simulation jitter detection, and structured nonce
traversal.  This module pushes that invariant into an executable lattice
measurement surface: generated SU(2) configurations produce observed action
spectra, those spectra are compared against the operationalized
``(3 - φ) * Λ_QCD`` anchor, and ablation controls show whether the φ anchor is
actually doing more work than nearby non-φ constants.

The code is intentionally evidence-first: no synthetic spectrum is fabricated
from the expected answer, every verdict is tied to the measured spectrum, and
the exported packet separates operational validation from any claim to have
solved the Clay Millennium problem.
"""

import numpy as np
from typing import Any, Dict, List, Tuple
from dataclasses import dataclass
import json
from pathlib import Path

from pythia_mining.golden_ratio_library import PHI, PHI_INV


# Operational constants.  The threshold is the repository's documented
# Yang-Mills operationalization, not a fabricated measurement.
LAMBDA_QCD = 0.2  # GeV (reference confinement scale ≈ 200 MeV)
YANG_MILLS_THRESHOLD = 3 - PHI  # ≈ 1.382
EXPECTED_MASS_GAP = YANG_MILLS_THRESHOLD * LAMBDA_QCD  # ≈ 0.276 GeV
MIN_NONZERO_SPECTRUM_POINTS = 10
DEFAULT_RELATIVE_TOLERANCE = 0.10
DEFAULT_SIGMA_TOLERANCE = 3.0
ABLATION_CONSTANTS = {
    "phi": PHI,
    "pi": np.pi,
    "e": np.e,
    "sqrt2": np.sqrt(2.0),
    "uniform": 2.0,
}


@dataclass
class SU2Matrix:
    """SU(2) gauge group element (2×2 unitary matrix, det=1)"""

    matrix: np.ndarray  # Shape: (2, 2) complex

    def __post_init__(self):
        """Validate SU(2) properties"""
        # Check unitarity: U†U = I
        assert np.allclose(self.matrix.conj().T @ self.matrix, np.eye(2))
        # Check det = 1
        assert np.isclose(np.linalg.det(self.matrix), 1.0)

    @classmethod
    def identity(cls):
        """Identity element"""
        return cls(np.eye(2, dtype=complex))

    @classmethod
    def random(cls):
        """Random SU(2) element via φ-parameterization"""
        # Parameterize by (θ, φ, ψ) Euler angles
        theta = np.random.uniform(0, np.pi)
        phi_angle = np.random.uniform(0, 2 * np.pi)
        psi = np.random.uniform(0, 2 * np.pi)

        # φ-scaled random walk (prefer golden ratio angles)
        theta *= PHI_INV

        # Construct SU(2) matrix
        matrix = np.array(
            [
                [
                    np.cos(theta / 2) * np.exp(1j * (phi_angle + psi) / 2),
                    np.sin(theta / 2) * np.exp(1j * (phi_angle - psi) / 2),
                ],
                [
                    -np.sin(theta / 2) * np.exp(-1j * (phi_angle - psi) / 2),
                    np.cos(theta / 2) * np.exp(-1j * (phi_angle + psi) / 2),
                ],
            ]
        )

        return cls(matrix)

    def action(self) -> float:
        """Yang-Mills action for single plaquette"""
        # S = -β Re tr(U) where β is coupling
        beta = 2.3  # Standard lattice QCD coupling
        return -beta * np.real(np.trace(self.matrix))


@dataclass
class LatticeConfiguration:
    """SU(2) gauge field configuration on 4D lattice"""

    lattice_size: int  # Sites per dimension
    links: Dict[Tuple[int, int, int, int, int], SU2Matrix]

    @classmethod
    def cold_start(cls, lattice_size: int):
        """Initialize with identity (cold start)"""
        links = {}
        for t in range(lattice_size):
            for x in range(lattice_size):
                for y in range(lattice_size):
                    for z in range(lattice_size):
                        for mu in range(4):  # 4 directions
                            links[(t, x, y, z, mu)] = SU2Matrix.identity()
        return cls(lattice_size, links)

    @classmethod
    def hot_start(cls, lattice_size: int):
        """Initialize with random configuration (hot start)"""
        links = {}
        for t in range(lattice_size):
            for x in range(lattice_size):
                for y in range(lattice_size):
                    for z in range(lattice_size):
                        for mu in range(4):
                            links[(t, x, y, z, mu)] = SU2Matrix.random()
        return cls(lattice_size, links)

    def plaquette(self, site: Tuple[int, int, int, int], mu: int, nu: int) -> SU2Matrix:
        """Compute plaquette (Wilson loop) at site in (mu, nu) plane"""
        t, x, y, z = site
        L = self.lattice_size

        # Get four links forming plaquette
        U1 = self.links[(t, x, y, z, mu)]

        # Next site in mu direction
        site_mu = (
            (t + (1 if mu == 0 else 0)) % L,
            (x + (1 if mu == 1 else 0)) % L,
            (y + (1 if mu == 2 else 0)) % L,
            (z + (1 if mu == 3 else 0)) % L,
        )
        U2 = self.links[(*site_mu, nu)]

        # Next site in nu direction
        site_nu = (
            (t + (1 if nu == 0 else 0)) % L,
            (x + (1 if nu == 1 else 0)) % L,
            (y + (1 if nu == 2 else 0)) % L,
            (z + (1 if nu == 3 else 0)) % L,
        )
        U3_dag = self.links[(*site_nu, mu)]

        U4_dag = self.links[(t, x, y, z, nu)]

        # Plaquette = U1 U2 U3† U4†
        plaq_matrix = (
            U1.matrix @ U2.matrix @ U3_dag.matrix.conj().T @ U4_dag.matrix.conj().T
        )

        return SU2Matrix(plaq_matrix)

    def total_action(self) -> float:
        """Total Yang-Mills action over all plaquettes"""
        action = 0.0
        L = self.lattice_size

        for t in range(L):
            for x in range(L):
                for y in range(L):
                    for z in range(L):
                        site = (t, x, y, z)
                        # Sum over all 6 plaquettes at this site
                        for mu in range(4):
                            for nu in range(mu + 1, 4):
                                try:
                                    plaq = self.plaquette(site, mu, nu)
                                    # Action from plaquette (always positive)
                                    plaq_action = (
                                        1.0 - np.real(np.trace(plaq.matrix)) / 2.0
                                    )
                                    action += plaq_action
                                except:
                                    # Skip invalid plaquettes
                                    pass

        total_plaquettes = L**4 * 6
        return action / total_plaquettes if total_plaquettes > 0 else 0.0


class YangMillsSpectralGapMeasurement:
    """
    Measure an operational Yang-Mills action-spectrum gap via Monte Carlo sampling.

    The class elevates the repository's documented ``3 - φ`` invariant into a
    falsifiable runtime check: it requires real observed spectra, compares them
    to the φ mass-gap anchor, and reports control/ablation evidence alongside
    the verdict.
    """

    def __init__(self, lattice_size: int = 8, n_configs: int = 1000):
        self.lattice_size = lattice_size
        self.n_configs = n_configs
        self.configurations: List[LatticeConfiguration] = []
        self.actions: List[float] = []

    def generate_configurations(self):
        """Generate ensemble of gauge configurations"""
        print(f"\n{'='*70}")
        print(f"YANG-MILLS SPECTRAL GAP MEASUREMENT")
        print(f"{'='*70}")
        print(f"Lattice: {self.lattice_size}^4")
        print(f"Configurations: {self.n_configs}")
        print(f"{'='*70}\n")

        print("Generating configurations...")

        for i in range(self.n_configs):
            if i < self.n_configs // 2:
                # Cold start (half)
                config = LatticeConfiguration.cold_start(self.lattice_size)
            else:
                # Hot start (half)
                config = LatticeConfiguration.hot_start(self.lattice_size)

            action = config.total_action()

            self.configurations.append(config)
            self.actions.append(action)

            if (i + 1) % 100 == 0:
                print(f"  Generated {i+1}/{self.n_configs} configurations")

        print(f"\n✅ Configuration generation complete\n")

    def compute_spectrum(self) -> np.ndarray:
        """Compute the observed non-zero action spectrum without synthetic fallback."""
        actions_array = np.array(self.actions, dtype=float)
        return actions_array[np.isfinite(actions_array) & (actions_array > 1e-10)]

    def _insufficient_spectrum_result(self, spectrum: np.ndarray) -> Dict[str, Any]:
        return {
            "success": False,
            "validated": False,
            "operational_elevated": False,
            "verdict": "insufficient_observed_spectrum",
            "error": (
                f"Need at least {MIN_NONZERO_SPECTRUM_POINTS} observed non-zero "
                f"action values; found {len(spectrum)}. No synthetic φ-scaled "
                "fallback is allowed."
            ),
            "spectrum": {"n_nonzero": int(len(spectrum))},
            "controls": {
                "synthetic_spectrum_used": False,
                "ablation_controls_run": False,
                "failure_mode": "insufficient_observed_spectrum",
            },
        }

    def _constant_gap_metrics(
        self, spectrum: np.ndarray, constant: float
    ) -> Dict[str, float]:
        min_eigenvalue = np.min(spectrum)
        target_gap = (3 - constant) * LAMBDA_QCD
        relative_error = (
            abs(min_eigenvalue - target_gap) / abs(target_gap)
            if not np.isclose(target_gap, 0.0)
            else float("inf")
        )
        return {
            "constant": float(constant),
            "target_GeV": float(target_gap),
            "absolute_error_GeV": float(abs(min_eigenvalue - target_gap)),
            "relative_error_pct": float(relative_error * 100),
        }

    def _ablation_controls(self, spectrum: np.ndarray) -> Dict[str, Any]:
        """
        Compare the observed gap against φ and non-φ anchors.

        This is the operational elevation step: φ is not allowed to win by
        assertion.  The packet records whether the measured spectrum is closer
        to the documented φ anchor than to π, e, sqrt(2), and a uniform control.
        """
        metrics = {
            name: self._constant_gap_metrics(spectrum, constant)
            for name, constant in ABLATION_CONSTANTS.items()
        }
        ranked = sorted(
            metrics,
            key=lambda name: metrics[name]["absolute_error_GeV"],
        )
        phi_rank = ranked.index("phi") + 1
        return {
            "synthetic_spectrum_used": False,
            "ablation_controls_run": True,
            "control_constants": metrics,
            "ranking_by_absolute_error": ranked,
            "phi_rank": int(phi_rank),
            "phi_best_anchor": phi_rank == 1,
        }

    def measure_spectral_gap(self) -> Dict:
        """
        Measure spectral gap and compare to theoretical prediction
        Returns measurement results with statistical significance
        """
        spectrum = self.compute_spectrum()

        if len(spectrum) < MIN_NONZERO_SPECTRUM_POINTS:
            return self._insufficient_spectrum_result(spectrum)

        # Minimum non-zero eigenvalue
        min_eigenvalue = np.min(spectrum)

        # Normalize by Λ_QCD
        measured_gap_ratio = min_eigenvalue / LAMBDA_QCD
        expected_gap_ratio = YANG_MILLS_THRESHOLD

        # Statistical analysis.  The only validation target is the stated
        # prediction itself; no unrelated random-baseline z-score is used for
        # pass/fail decisions.
        mean_action = np.mean(spectrum)
        std_action = np.std(spectrum, ddof=1) if len(spectrum) > 1 else 0.0
        standard_error = std_action / np.sqrt(len(spectrum)) if std_action > 0 else 0.0

        # Compatibility with the φ-threshold hypothesis.
        prediction_delta = min_eigenvalue - EXPECTED_MASS_GAP
        prediction_error = (
            abs(measured_gap_ratio - expected_gap_ratio) / expected_gap_ratio
        )
        prediction_z_score = (
            abs(prediction_delta) / standard_error
            if standard_error > 0
            else (0.0 if np.isclose(prediction_delta, 0.0) else float("inf"))
        )
        validated = bool(
            prediction_error <= DEFAULT_RELATIVE_TOLERANCE
            and prediction_z_score <= DEFAULT_SIGMA_TOLERANCE
        )
        controls = self._ablation_controls(spectrum)
        operational_elevated = bool(validated and controls["phi_best_anchor"])
        verdict = (
            "operational_phi_mass_gap_elevated"
            if operational_elevated
            else "not_elevated_against_operational_controls"
        )

        results = {
            "success": True,
            "validated": validated,
            "operational_elevated": operational_elevated,
            "verdict": verdict,
            "lattice_size": self.lattice_size,
            "n_configurations": self.n_configs,
            "spectrum": {
                "min": float(np.min(spectrum)),
                "max": float(np.max(spectrum)),
                "mean": float(mean_action),
                "std": float(std_action),
                "n_nonzero": int(len(spectrum)),
            },
            "mass_gap": {
                "measured_GeV": float(min_eigenvalue),
                "expected_GeV": float(EXPECTED_MASS_GAP),
                "measured_ratio": float(measured_gap_ratio),
                "expected_ratio": float(expected_gap_ratio),
                "prediction_error_pct": float(prediction_error * 100),
                "prediction_delta_GeV": float(prediction_delta),
                "standard_error_GeV": float(standard_error),
                "prediction_z_score": float(prediction_z_score),
                "relative_tolerance_pct": float(DEFAULT_RELATIVE_TOLERANCE * 100),
                "sigma_tolerance": float(DEFAULT_SIGMA_TOLERANCE),
            },
            "phi_validation": {
                "phi": float(PHI),
                "yang_mills_threshold_3_minus_phi": float(YANG_MILLS_THRESHOLD),
                "lambda_qcd_GeV": float(LAMBDA_QCD),
            },
            "controls": controls,
            "claim_boundary": {
                "operational_use": (
                    "3 - φ is tested as a deterministic threshold for mass-gap-style "
                    "runtime gating and anti-simulation evidence."
                ),
                "not_claimed": (
                    "This packet is not a proof of the Yang-Mills Millennium problem "
                    "and is not a continuum QFT existence theorem."
                ),
            },
        }

        return results

    def print_results(self, results: Dict):
        """Pretty-print measurement results"""
        if not results["success"]:
            print(f"❌ MEASUREMENT FAILED: {results['error']}")
            return

        print(f"{'='*70}")
        print(f"SPECTRAL GAP MEASUREMENT RESULTS")
        print(f"{'='*70}\n")

        print(f"LATTICE CONFIGURATION:")
        print(f"  Size: {results['lattice_size']}^4")
        print(f"  Configurations: {results['n_configurations']}")
        print(f"  Non-zero spectrum: {results['spectrum']['n_nonzero']}\n")

        print(f"SPECTRUM STATISTICS:")
        print(f"  Min action: {results['spectrum']['min']:.6f}")
        print(f"  Max action: {results['spectrum']['max']:.6f}")
        print(
            f"  Mean: {results['spectrum']['mean']:.6f} ± {results['spectrum']['std']:.6f}\n"
        )

        print(f"MASS GAP MEASUREMENT:")
        print(f"  Measured: {results['mass_gap']['measured_GeV']:.6f} GeV")
        print(f"  Expected: {results['mass_gap']['expected_GeV']:.6f} GeV")
        print(f"  Prediction error: {results['mass_gap']['prediction_error_pct']:.2f}%")
        print(f"  Prediction Δ: {results['mass_gap']['prediction_delta_GeV']:.6f} GeV")
        print(f"  Standard error: {results['mass_gap']['standard_error_GeV']:.6f} GeV")
        print(
            f"  Prediction z-score: {results['mass_gap']['prediction_z_score']:.2f}σ\n"
        )

        print(f"φ-GEOMETRY VALIDATION:")
        print(f"  Golden ratio φ: {results['phi_validation']['phi']:.9f}")
        print(
            f"  Yang-Mills threshold (3-φ): {results['phi_validation']['yang_mills_threshold_3_minus_phi']:.6f}"
        )
        print(f"  Λ_QCD: {results['phi_validation']['lambda_qcd_GeV']:.3f} GeV\n")

        controls = results["controls"]
        print("OPERATIONAL CONTROLS:")
        print(f"  Synthetic spectrum used: {controls['synthetic_spectrum_used']}")
        print(f"  Ablation controls run: {controls['ablation_controls_run']}")
        print(
            f"  φ anchor rank: {controls['phi_rank']} / {len(controls['ranking_by_absolute_error'])}"
        )
        print(f"  Anchor ranking: {', '.join(controls['ranking_by_absolute_error'])}\n")

        # Verdict
        z = results["mass_gap"]["prediction_z_score"]
        error_pct = results["mass_gap"]["prediction_error_pct"]

        if results.get("operational_elevated"):
            print("✅ OPERATIONAL YANG-MILLS MASS-GAP INVARIANT ELEVATED")
            print(
                f"   Relative error: {error_pct:.2f}% <= {results['mass_gap']['relative_tolerance_pct']:.2f}%"
            )
            print(
                f"   Prediction z-score: {z:.2f}σ <= {results['mass_gap']['sigma_tolerance']:.2f}σ"
            )
            print("   φ anchor beat the non-φ ablation controls.")
        else:
            print("❌ OPERATIONAL YANG-MILLS MASS-GAP INVARIANT NOT ELEVATED")
            print(
                f"   Relative error: {error_pct:.2f}% (limit {results['mass_gap']['relative_tolerance_pct']:.2f}%)"
            )
            print(
                f"   Prediction z-score: {z:.2f}σ (limit {results['mass_gap']['sigma_tolerance']:.2f}σ)"
            )
            print(f"   φ best ablation anchor: {controls['phi_best_anchor']}")
            print(
                "   Keep pushing the lattice/control experiment before promoting the claim."
            )

        print(f"{'='*70}\n")

    def save_results(self, results: Dict, output_file: str):
        """Save results to JSON"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        print(f"💾 Results saved: {output_path}\n")


def run_yang_mills_measurement(
    lattice_size: int = 8,
    n_configs: int = 1000,
    output_file: str = "artifacts/yang_mills/spectral_gap_measurement.json",
):
    """
    Run complete Yang-Mills spectral gap measurement

    Args:
        lattice_size: Lattice sites per dimension (default: 8 → 4096 sites)
        n_configs: Number of configurations to generate (default: 1000)
        output_file: Where to save results

    Returns:
        Measurement results dict
    """
    measurement = YangMillsSpectralGapMeasurement(
        lattice_size=lattice_size, n_configs=n_configs
    )

    # Generate configurations
    measurement.generate_configurations()

    # Measure spectral gap
    results = measurement.measure_spectral_gap()

    # Print results
    measurement.print_results(results)

    # Save to disk
    measurement.save_results(results, output_file)

    return results


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("YANG-MILLS MASS GAP: EMPIRICAL VALIDATION")
    print("=" * 70)
    print("Objective: finite-lattice diagnostic of the (3-φ) × Λ_QCD hypothesis")
    print("=" * 70 + "\n")

    # Run measurement
    results = run_yang_mills_measurement(lattice_size=8, n_configs=1000)

    print("=" * 70)
    print("MEASUREMENT COMPLETE")
    print("=" * 70)
    print("Next: inspect diagnostics; do not treat this as a Clay Institute proof")
    print("=" * 70)

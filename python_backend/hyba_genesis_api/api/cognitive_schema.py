"""Cognitive and Metabolic schema models for the Organism CNS."""

from pydantic import BaseModel


class Conjecture(BaseModel):
    """A Popperian conjecture for self-optimization."""

    conjecture_id: str
    explanation: str
    predicted_phi_gain: float
    confidence_interval: float
    status: str  # "PROPOSED", "SIMULATING", "REJECTED", "VINDICATED"


class MetabolicFlux(BaseModel):
    """Measurement of energy-to-intelligence conversion rate."""

    energy_per_phi: float
    hashrate_normalized_entropy: float
    hunger_level: float
    metabolic_rate: str  # "QUIESCENT", "ACTIVE", "HYPER"

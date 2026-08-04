"""AgroIA Backend services package."""

from agroia_backend.services.data_adapters import (
    ALL_SOIL_VARIABLES,
    VARIABLES_BLOQUEANTES,
    SoilData,
    SueloAdapter,
    validate_soil_reading,
)
from agroia_backend.services.justification import (
    estimate_cost,
    generate_justification,
    translate_soil_condition,
)
from agroia_backend.services.orchestrator import (
    RecommendationOrchestrator,
    RecommendationRequest,
    RecommendationResult,
)
from agroia_backend.services.rules_engine import (
    RuleViolation,
    RulesEngine,
    RulesResult,
)

__all__ = [
    # Data adapters
    "ALL_SOIL_VARIABLES",
    "VARIABLES_BLOQUEANTES",
    "SoilData",
    "SueloAdapter",
    "validate_soil_reading",
    # Rules engine
    "RuleViolation",
    "RulesEngine",
    "RulesResult",
    # Orchestrator
    "RecommendationOrchestrator",
    "RecommendationRequest",
    "RecommendationResult",
    # Justification
    "generate_justification",
    "translate_soil_condition",
    "estimate_cost",
]

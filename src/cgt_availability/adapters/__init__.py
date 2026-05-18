"""Optional adapters for external scientific tooling.

Adapters are not imported by the core analyzer. They are explicit integration
points for users who install optional libraries or external tools.
"""

from cgt_availability.adapters.base import (
    AdapterErrorRecord,
    AdapterExecutionError,
    AdapterUnavailable,
)
from cgt_availability.adapters.model_checking import (
    PRISM_COMMAND_PROFILE,
    STORM_COMMAND_PROFILE,
    ExternalModelCheckerAdapter,
    ExternalModelCheckResult,
    ModelCheckerCommandProfile,
    ModelCheckerOutputMode,
)
from cgt_availability.adapters.statistics import (
    TTestEvidence,
    scipy_binomial_verifier,
    scipy_one_sample_t_test,
)

__all__ = [
    "AdapterExecutionError",
    "AdapterErrorRecord",
    "AdapterUnavailable",
    "ExternalModelCheckResult",
    "ExternalModelCheckerAdapter",
    "ModelCheckerCommandProfile",
    "ModelCheckerOutputMode",
    "PRISM_COMMAND_PROFILE",
    "STORM_COMMAND_PROFILE",
    "TTestEvidence",
    "scipy_binomial_verifier",
    "scipy_one_sample_t_test",
]

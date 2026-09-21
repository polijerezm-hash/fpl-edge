from typing import Dict, Any, Optional

class FplEdgeError(Exception):
    """Base exception for FPL Edge errors."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": "error",
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


class LiveDataUnavailableError(FplEdgeError):
    """Raised when official FPL API is unreachable or returns non-200."""
    def __init__(self, message: str = "Current FPL live data could not be loaded. No recommendation has been generated.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="LIVE_DATA_UNAVAILABLE", details=details)


class LiveDataInvalidError(FplEdgeError):
    """Raised when official FPL data fails schema or integrity validation."""
    def __init__(self, message: str = "Official FPL data failed integrity validation.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="LIVE_DATA_INVALID", details=details)


class InvalidTeamIdError(FplEdgeError):
    """Raised when a supplied FPL Team ID does not exist or has no picks."""
    def __init__(self, message: str = "Supplied FPL Team ID is invalid or has no registered squad.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="INVALID_TEAM_ID", details=details)


class CurrentSquadInvalidError(FplEdgeError):
    """Raised when an imported squad contains players not present in active snapshot or violates rules."""
    def __init__(self, message: str = "Imported manager squad is invalid against current live data snapshot.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="CURRENT_SQUAD_INVALID", details=details)


class StaleSnapshotError(FplEdgeError):
    """Raised when a request or recommendation is based on an outdated snapshot."""
    def __init__(self, message: str = "The active snapshot has expired or been superseded. Please refresh and re-optimise.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="STALE_SNAPSHOT", details=details)


class ProjectionFailedError(FplEdgeError):
    """Raised when expected points or availability projections fail."""
    def __init__(self, message: str = "Projection calculation failed for current gameweek.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="PROJECTION_FAILED", details=details)


class OptimisationFailedError(FplEdgeError):
    """Raised when PuLP MILP solver fails to produce a feasible plan."""
    def __init__(self, message: str = "Optimizer failed to find a valid squad optimization plan.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="OPTIMISATION_FAILED", details=details)


class RecommendationValidationFailedError(FplEdgeError):
    """Raised when optimizer output violates post-solve integrity checks."""
    def __init__(self, message: str = "Optimizer plan failed post-solve integrity validation gate.", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code="RECOMMENDATION_VALIDATION_FAILED", details=details)

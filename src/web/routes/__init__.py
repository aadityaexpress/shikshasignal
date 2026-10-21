from .health import router as health_router
from .import_routes import router as import_router
from .overview import router as overview_router
from .students import router as students_router
from .interventions import router as interventions_router
from .governance import router as governance_router

__all__ = [
    "health_router",
    "import_router",
    "overview_router",
    "students_router",
    "interventions_router",
    "governance_router",
]

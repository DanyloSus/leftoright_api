from .base import Model, TimestampMixin

# Import all ORM models so alembic autogenerate can detect them
import app.features.user.model # noqa: F401, E402
import app.features.tournament.model # noqa: F401, E402
import app.features.entity.model # noqa: F401, E402
import app.features.session.model # noqa: F401, E402
import app.features.match.model # noqa: F401, E402

__all__ = ["Model", "TimestampMixin"]

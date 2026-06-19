import tempfile
from pathlib import Path

from api.database import LocationDB
from api.schemas import LocationOut


def create_location_out(
    id: int = 1,
    name: str = "Paris",
    topic: str = "paris",
    country: str | None = "France",
    created_at: str = "2024-01-01T00:00:00+00:00"
) -> LocationOut:
    """Create a LocationOut object for testing purposes."""
    return LocationOut(
        id=id,
        name=name,
        topic=topic,
        country=country,
        created_at=created_at
    )

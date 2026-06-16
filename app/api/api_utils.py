from __future__ import annotations

from typing import Any

from dataclasses import asdict
from pydantic import ValidationError

from app.models.models import Crew, Flight, Roster, UnassignedFlight
from app.services.utils import _total_flight_hours

def _get_current_run(_current_run: dict[str, Any]) -> dict[str, Any] | None:
    if not _current_run:
        return None
    return _current_run


def _serialize_roster_by_flight(
    roster: Roster,
    flights: dict[str, Flight],
) -> dict[str, list[str]]:
    return {
        flight_id: roster.get_flight_crew(flight_id)
        for flight_id in flights
        if roster.get_flight_crew(flight_id)
    }


def _serialize_unassigned(item: UnassignedFlight) -> dict[str, str]:
    return asdict(item)


def _serialize_crew_breakdown(
    roster: Roster,
    flights: dict[str, Flight],
    crew: dict[str, Crew],
    layover_costs: dict[str, float],
) -> dict[str, dict[str, Any]]:
    
    breakdown: dict[str, dict[str, Any]] = {}
    
    for crew_id, member in crew.items():
        schedule = roster.get_crew_schedule(crew_id=crew_id, flights=flights)
        breakdown[crew_id] = {
            "role": member.role,
            "flights": [flight.flight_id for flight in schedule],
            "total_hours": _total_flight_hours(schedule),
            "layover_cost": layover_costs.get(crew_id, 0.0),
        }
    return breakdown



def _format_validation_error(error: ValidationError | ValueError) -> str:
    if isinstance(error, ValidationError):
        first_error = error.errors()[0]
        location = ".".join(str(item) for item in first_error["loc"])
        return f"{location}: {first_error['msg']}"
    return str(error)
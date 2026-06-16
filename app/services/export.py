"""Used by the script entry point to build the roster_output.json file"""

from __future__ import annotations

from typing import Any

from app.models.models import Crew, Flight, Roster, UnassignedFlight
from app.services.costs import calculate_layover_costs

from app.services.utils import _total_flight_hours

def build_roster_output(
    roster: Roster,
    flights: dict[str, Flight],
    crew_list: dict[str, Crew],
    unassigned: list[UnassignedFlight],
) -> dict[str, Any]:
    layover_costs, total_layover_cost = calculate_layover_costs(
        roster=roster,
        flights=flights,
        crew_list=crew_list,
    )

    output: dict[str, Any] = {}
    for crew_id, crew in crew_list.items():
        schedule = roster.get_crew_schedule(crew_id=crew_id, flights=flights)
        output[crew_id] = {
            "role": crew.role,
            "flights": [flight.flight_id for flight in schedule],
            "total_hours": _total_flight_hours(schedule),
            "layover_cost": layover_costs.get(crew_id, 0.0),
        }

    output["unassigned"] = [
        {
            "flight_id": item.flight_id,
            "reason": item.reason,
        }
        for item in unassigned
    ]
    output["total_layover_cost"] = total_layover_cost
    return output

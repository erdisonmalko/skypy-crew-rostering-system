from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request
from pydantic import ValidationError

from app.models.models import Crew, Flight, Roster, UnassignedFlight
from app.models.schemas import ScheduleRequest
from app.services.costs import calculate_layover_costs
from app.services.scheduler import generate_schedule

from .api_utils import (
    _get_current_run,
    _serialize_crew_breakdown,
    _serialize_roster_by_flight,
    _serialize_unassigned,
    _total_flight_hours,
    _format_validation_error,
)

api = Blueprint("api", __name__)

_current_run: dict[str, Any] = {}


@api.post("/schedule")
def schedule():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    try:
        schedule_request = ScheduleRequest.model_validate(payload)
        flights, crew = schedule_request.to_domain()
    except (ValidationError, ValueError) as exc:
        return jsonify({"error": _format_validation_error(exc)}), 400

    roster, unassigned = generate_schedule(flights=flights, crew_list=crew)
    layover_costs, total_layover_cost = calculate_layover_costs(
        roster=roster,
        flights=flights,
        crew_list=crew,
    )

    _current_run.clear()
    _current_run.update(
        {
            "flights": flights,
            "crew": crew,
            "roster": roster,
            "unassigned": unassigned,
            "layover_costs": layover_costs,
            "total_layover_cost": total_layover_cost,
        }
    )

    return jsonify(
        {
            "roster": _serialize_roster_by_flight(roster, flights),
            "unassigned": [_serialize_unassigned(item) for item in unassigned],
        }
    ), 200



@api.get("/roster/<crew_id>")
def get_roster_for_crew(crew_id: str):
    run = _get_current_run(_current_run)
    if run is None:
        return jsonify({"error": "No scheduling run available"}), 404

    crew: dict[str, Crew] = run["crew"]
    if crew_id not in crew:
        return jsonify({"error": f"Crew member {crew_id!r} does not exist"}), 404

    roster: Roster = run["roster"]
    flights: dict[str, Flight] = run["flights"]
    layover_costs: dict[str, float] = run["layover_costs"]
    schedule = roster.get_crew_schedule(crew_id=crew_id, flights=flights)

    return jsonify(
        {
            "crew_id": crew_id,
            "flight_ids": [flight.flight_id for flight in schedule],
            "total_flight_hours": _total_flight_hours(schedule),
            "layover_cost": layover_costs.get(crew_id, 0.0),
        }
    ), 200


@api.get("/report")
def report():
    run = _get_current_run(_current_run)
    if run is None:
        return jsonify({"error": "No scheduling run available"}), 404

    flights: dict[str, Flight] = run["flights"]
    crew: dict[str, Crew] = run["crew"]
    roster: Roster = run["roster"]
    unassigned: list[UnassignedFlight] = run["unassigned"]
    layover_costs: dict[str, float] = run["layover_costs"]

    return jsonify(
        {
            "total_flights_scheduled": len(flights) - len(unassigned),
            "total_unassigned_flights": len(unassigned),
            "total_layover_cost": run["total_layover_cost"],
            "crew": _serialize_crew_breakdown(
                roster=roster,
                flights=flights,
                crew=crew,
                layover_costs=layover_costs,
            ),
        }
    ), 200

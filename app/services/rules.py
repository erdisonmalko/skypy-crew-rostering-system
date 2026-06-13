from app.models.models import (
    Crew,
    Flight,
    Roster,
    RuleViolation,
)

from app.utils.engine_rules_utils import (
    _check_home_base, 
    _check_range_certification, 
    _check_route_continuity,
    _check_dynamic_rest
    )

# from app.utils.crew_pairing_utils import (
#     _validate_dynamic_rest_for_single_flight
# )

# validate roster function(point 3 of the requirements)
def validate_roster(roster: Roster,flights: dict[str, Flight],crew_list: dict[str, Crew]) -> list[RuleViolation]:
    violations: list[RuleViolation] = []

    for crew in crew_list.values():
        schedule = roster.get_crew_schedule(crew.crew_id, flights)
        if not schedule:
            continue

        _check_home_base(crew, schedule, violations)
        _check_range_certification(crew, schedule, violations)
        _check_route_continuity(crew, schedule, violations)
        _check_dynamic_rest(crew, schedule, violations)

    return violations


# validate pairing function(point 4 of the requirements)
def validate_pairing(
    flight: Flight,
    roster: Roster,
    crew_list: dict[str, Crew],
) -> list[RuleViolation]:
    violations: list[RuleViolation] = []

    assigned_crew_ids = roster.get_flight_crew(flight.flight_id)

    if not assigned_crew_ids:
        violations.append(
            RuleViolation(
                crew_id="N/A",
                flight_id=flight.flight_id,
                description="Incomplete Pairing: no crew assigned",
            )
        )
        return violations

    assigned_crew: list[Crew] = []

    for crew_id in assigned_crew_ids:
        crew = crew_list.get(crew_id)

        if crew is None:
            violations.append(
                RuleViolation(
                    crew_id=crew_id,
                    flight_id=flight.flight_id,
                    description="Assigned crew member does not exist",
                )
            )
            continue

        assigned_crew.append(crew)

    captain_count = sum(1 for crew in assigned_crew if crew.role == "Captain")
    first_officer_count = sum(1 for crew in assigned_crew if crew.role == "FirstOfficer")

    if captain_count != 1:
        violations.append(
            RuleViolation(
                crew_id="N/A",
                flight_id=flight.flight_id,
                description=(
                    f"Invalid Pairing: expected exactly 1 Captain, "
                    f"found {captain_count}"
                ),
            )
        )

    if first_officer_count < 1:
        violations.append(
            RuleViolation(
                crew_id="N/A",
                flight_id=flight.flight_id,
                description="Incomplete Pairing: at least 1 FirstOfficer is required",
            )
        )

    for crew in assigned_crew:
        if flight.distance_miles > crew.max_range_miles:
            violations.append(
                RuleViolation(
                    crew_id=crew.crew_id,
                    flight_id=flight.flight_id,
                    description=(
                        f"Range Certification failed: flight distance "
                        f"{flight.distance_miles} exceeds crew range "
                        f"{crew.max_range_miles}"
                    ),
                )
            )

    return violations
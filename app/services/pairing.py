from app.models.models import (
    Crew,
    Flight,
    Roster,
    RuleViolation,
)

from app.services.utils import required_rest_minutes


def validate_pairing(
    flight_id: str,
    roster: Roster,
    crew_list: dict[str, Crew],
    flights: dict[str, Flight],
) -> list[RuleViolation]:
    violations: list[RuleViolation] = []

    flight = flights.get(flight_id)
    if flight is None:
        violations.append(
            RuleViolation(
                crew_id="N/A",
                flight_id=flight_id,
                description="Flight does not exist",
            )
        )
        # if there is no flight, retunr early
        return violations
    
    assigned_crew_ids = roster.get_flight_crew(flight_id)

    if not assigned_crew_ids:
        violations.append(
            RuleViolation(
                crew_id="N/A",
                flight_id=flight_id,
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
                    flight_id=flight_id,
                    description="Assigned crew member does not exist",
                )
            )
            continue

        assigned_crew.append(crew)

    captain_count = sum(1 for crew in assigned_crew if crew.role == "Captain")
    first_officer_count = sum(1 for crew in assigned_crew if crew.role == "FirstOfficer")

    if captain_count == 0 and first_officer_count > 0:
        violations.append(
            RuleViolation(
                crew_id="N/A",
                flight_id=flight_id,
                description="Incomplete Pairing: Captain missing",
            )
        )

    elif captain_count > 0 and first_officer_count == 0:
        violations.append(
            RuleViolation(
                crew_id="N/A",
                flight_id=flight_id,
                description="Incomplete Pairing: FirstOfficer missing",
            )
        )

    if captain_count > 1:
        violations.append(
            RuleViolation(
                crew_id="N/A",
                flight_id=flight_id,
                description=(
                    f"Invalid Pairing: expected exactly 1 Captain, "
                    f"found {captain_count}"
                ),
            )
        )

    for crew in assigned_crew:
        if flight.distance_miles > crew.max_range_miles:
            violations.append(
                RuleViolation(
                    crew_id=crew.crew_id,
                    flight_id=flight_id,
                    description=(
                        f"Range Certification failed: flight distance "
                        f"{flight.distance_miles} exceeds crew range "
                        f"{crew.max_range_miles}"
                    ),
                )
            )
        # to calc this we need a list of flights, because we need to check 
        # previous and next flights for the crew member to calculate rest time
        # thats why function takes flights as an argument
        rest_violation = _validate_dynamic_rest_for_single_flight(
            crew=crew,
            flight=flight,
            roster=roster,
            flights=flights,
        )

        if rest_violation:
            violations.append(rest_violation)

    return violations

def _validate_dynamic_rest_for_single_flight(
    crew: Crew,
    flight: Flight,
    roster: Roster,
    flights: dict[str, Flight],
) -> RuleViolation | None:
    
    schedule: list[Flight] = roster.get_crew_schedule(crew_id=crew.crew_id, flights=flights)
    
    flight_index = None

    for index, scheduled_flight in enumerate(schedule):
        if scheduled_flight.flight_id == flight.flight_id:
            flight_index = index
            break

    if flight_index is None:
        return None

    if flight_index > 0: # If this is not the first flight, check the flight before it
        previous_flight = schedule[flight_index - 1]
        required_rest = required_rest_minutes(previous_flight)
        actual_rest = (
            flight.departure_time - previous_flight.arrival_time
        ).total_seconds() / 60

        if actual_rest < required_rest:
            return RuleViolation(
                crew_id=crew.crew_id,
                flight_id=flight.flight_id,
                description=(
                    f"Insufficient rest before flight: "
                    f"{actual_rest:.0f} minutes available, "
                    f"{required_rest} required"
                ),
            )

    if flight_index < len(schedule) - 1: # If this is not the last flight, check the flight after it
        next_flight = schedule[flight_index + 1]
        required_rest = required_rest_minutes(flight)
        actual_rest = (
            next_flight.departure_time - flight.arrival_time
        ).total_seconds() / 60

        if actual_rest < required_rest:
            return RuleViolation(
                crew_id=crew.crew_id,
                flight_id=next_flight.flight_id,
                description=(
                    f"Insufficient rest after flight: "
                    f"{actual_rest:.0f} minutes available, "
                    f"{required_rest} required"
                ),
            )

    return None


from app.models.models import (
    Crew,
    Flight,
    Roster,
    RuleViolation,
)

def _validate_dynamic_rest_for_single_flight(
    crew: Crew,
    flight: Flight,
    roster: Roster,
    flights: dict[str, Flight],
) -> RuleViolation | None:
    schedule = roster.get_crew_schedule(
        crew_id=crew.crew_id,
        flights=flights,
    )

    flight_index = None

    for index, scheduled_flight in enumerate(schedule):
        if scheduled_flight.flight_id == flight.flight_id:
            flight_index = index
            break

    if flight_index is None:
        return None

    # Check previous flight -> current flight
    if flight_index > 0:
        previous_flight = schedule[flight_index - 1]

        required_rest = (
            60
            if previous_flight.duration_minutes < 180
            else 120
        )

        actual_rest = (
            flight.departure_time
            - previous_flight.arrival_time
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

    # Check current flight -> next flight
    if flight_index < len(schedule) - 1:
        next_flight = schedule[flight_index + 1]

        required_rest = (
            60
            if flight.duration_minutes < 180
            else 120
        )

        actual_rest = (
            next_flight.departure_time
            - flight.arrival_time
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
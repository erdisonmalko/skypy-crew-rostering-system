from app.models.models import (
    Crew,
    Flight,
    RuleViolation,
)

def _check_home_base(crew: Crew, schedule: list[Flight],violations: list[RuleViolation]) -> None:
    first_flight = schedule[0]
    if first_flight.origin != crew.home_base:
        violations.append(
            RuleViolation(
                crew_id=crew.crew_id,
                flight_id=first_flight.flight_id,
                description=(
                    f"First flight does not depart "
                    f"from home base {crew.home_base}"
                ),
            )
        )


def _check_range_certification(crew: Crew,schedule: list[Flight],violations: list[RuleViolation]) -> None:

    for flight in schedule:
        if flight.distance_miles > crew.max_range_miles:
            violations.append(
                RuleViolation(
                    crew_id=crew.crew_id,
                    flight_id=flight.flight_id,
                    description=(
                        f"Flight distance "
                        f"{flight.distance_miles} exceeds "
                        f"crew range certification "
                        f"{crew.max_range_miles}"
                    ),
                )
            )

def _check_route_continuity(crew: Crew,schedule: list[Flight],violations: list[RuleViolation]) -> None:
    for previous, current in zip(schedule, schedule[1:]):
        if previous.destination != current.origin:
            violations.append(
                RuleViolation(
                    crew_id=crew.crew_id,
                    flight_id=current.flight_id,
                    description=(
                        f"Route continuity broken: "
                        f"{previous.destination} != "
                        f"{current.origin}"
                    ),
                )
            )

def _check_dynamic_rest(crew: Crew,schedule: list[Flight],violations: list[RuleViolation]) -> None:
    for previous, current in zip(schedule, schedule[1:]):
        duration = previous.duration_minutes
        required_rest = (60 if duration < 180 else 120)
        # both fileds are datetime objects thats why we can use method total_seconds() 
        actual_rest = (current.departure_time - previous.arrival_time).total_seconds() / 60

        if actual_rest < required_rest:
            violations.append(
                RuleViolation(
                    crew_id=crew.crew_id,
                    flight_id=current.flight_id,
                    description=(
                        f"Insufficient rest: "
                        f"{actual_rest:.0f} minutes available, "
                        f"{required_rest} required"
                    ),
                )
            )
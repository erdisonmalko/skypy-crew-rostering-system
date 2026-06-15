from app.models.models import (
    Crew,
    Flight,
    Roster,
    RuleViolation,
)


def validate_roster(
    roster: Roster,
    flights: dict[str, Flight],
    crew_list: dict[str, Crew],
) -> list[RuleViolation]:
    """Validate every crew member's complete schedule."""
    violations: list[RuleViolation] = []

    for crew in crew_list.values():
        schedule: list[Flight] = roster.get_crew_schedule(crew.crew_id, flights)
        if not schedule:
            continue

        _check_home_base(crew, schedule, violations)
        _check_range_certification(crew, schedule, violations)
        _check_route_continuity(crew, schedule, violations)
        _check_dynamic_rest(crew, schedule, violations)

    return violations


def _check_home_base(
    crew: Crew,
    schedule: list[Flight],
    violations: list[RuleViolation],
) -> None:
    first_flight = schedule[0]
    if first_flight.origin != crew.home_base:
        violations.append(
            RuleViolation(
                crew_id=crew.crew_id,
                flight_id=first_flight.flight_id,
                description=(
                    f"First flight does not depart from home base {crew.home_base}"
                ),
            )
        )


def _check_range_certification(
    crew: Crew,
    schedule: list[Flight],
    violations: list[RuleViolation],
) -> None:
    for flight in schedule:
        if flight.distance_miles > crew.max_range_miles:
            violations.append(
                RuleViolation(
                    crew_id=crew.crew_id,
                    flight_id=flight.flight_id,
                    description=(
                        f"Flight distance {flight.distance_miles} exceeds "
                        f"crew range certification {crew.max_range_miles}"
                    ),
                )
            )


def _check_route_continuity(
    crew: Crew,
    schedule: list[Flight],
    violations: list[RuleViolation],
) -> None:
    # checks them like: f1,f2,f3,f4 with f2,f3,f4 and creates pairs
    #  (f1,f2), (f2,f3), (f3,f4) to check the continuity
    for previous, current in zip(schedule, schedule[1:]):
        if previous.destination != current.origin:
            violations.append(
                RuleViolation(
                    crew_id=crew.crew_id,
                    flight_id=current.flight_id,
                    description=(
                        f"Route continuity broken: "
                        f"{previous.destination} != {current.origin}"
                    ),
                )
            )


def _check_dynamic_rest(
    crew: Crew,
    schedule: list[Flight],
    violations: list[RuleViolation],
) -> None:
    # same as above, we check pairs of flights to calculate the rest time between them
    for previous, current in zip(schedule, schedule[1:]):
        required_rest = 60 if previous.duration_minutes < 180 else 120
        actual_rest = (
            current.departure_time - previous.arrival_time
        ).total_seconds() / 60

        if actual_rest < required_rest:
            violations.append(
                RuleViolation(
                    crew_id=crew.crew_id,
                    flight_id=current.flight_id,
                    description=(
                        f"Insufficient rest: {actual_rest:.0f} minutes available, "
                        f"{required_rest} required"
                    ),
                )
            )

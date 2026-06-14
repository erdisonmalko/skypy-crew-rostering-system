import heapq
from copy import deepcopy

from app.models.models import Crew, Flight, Roster, UnassignedFlight
from app.services.rules import validate_roster


def generate_schedule(
    flights: dict[str, Flight],
    crew_list: dict[str, Crew],
) -> tuple[Roster, list[UnassignedFlight]]:
    """Generate a legal crew roster using a greedy priority-based scheduler.

    Flights are processed by priority first, then departure time.
    Each flight requires exactly one Captain and one FirstOfficer.
    """

    roster = Roster()
    unassigned: list[UnassignedFlight] = []

    flight_heap: list[tuple[int, object, str]] = []

    for flight in flights.values():
        heapq.heappush(
            flight_heap,
            (
                flight.priority,
                flight.departure_time,
                flight.flight_id,
            ),
        )

    while flight_heap:
        _, _, flight_id = heapq.heappop(flight_heap)
        flight = flights[flight_id]

        valid_captains = [
            crew
            for crew in crew_list.values()
            if crew.role == "Captain"
            and _can_assign_crew_to_flight(
                crew=crew,
                flight=flight,
                roster=roster,
                flights=flights,
                crew_list=crew_list,
            )
        ]

        if not valid_captains:
            unassigned.append(
                UnassignedFlight(
                    flight_id=flight.flight_id,
                    reason="No Captain available",
                )
            )
            continue

        valid_first_officers = [
            crew
            for crew in crew_list.values()
            if crew.role == "FirstOfficer"
            and _can_assign_crew_to_flight(
                crew=crew,
                flight=flight,
                roster=roster,
                flights=flights,
                crew_list=crew_list,
            )
        ]

        if not valid_first_officers:
            unassigned.append(
                UnassignedFlight(
                    flight_id=flight.flight_id,
                    reason="No FirstOfficer available",
                )
            )
            continue

        assigned = False

        for captain in valid_captains:
            for first_officer in valid_first_officers:
                candidate_roster = deepcopy(roster)

                candidate_roster.assign(
                    flight_id=flight.flight_id,
                    crew_id=captain.crew_id,
                )
                candidate_roster.assign(
                    flight_id=flight.flight_id,
                    crew_id=first_officer.crew_id,
                )

                violations = validate_roster(
                    roster=candidate_roster,
                    flights=flights,
                    crew_list=crew_list,
                )

                if not violations:
                    roster.assign(
                        flight_id=flight.flight_id,
                        crew_id=captain.crew_id,
                    )
                    roster.assign(
                        flight_id=flight.flight_id,
                        crew_id=first_officer.crew_id,
                    )

                    assigned = True
                    break

            if assigned:
                break

        if not assigned:
            unassigned.append(
                UnassignedFlight(
                    flight_id=flight.flight_id,
                    reason="No valid pair found",
                )
            )

    return roster, unassigned



def _can_assign_crew_to_flight(
    crew: Crew,
    flight: Flight,
    roster: Roster,
    flights: dict[str, Flight],
    crew_list: dict[str, Crew],
) -> bool:
    """Check whether assigning one crew member to one flight keeps roster legal."""

    if flight.distance_miles > crew.max_range_miles:
        return False

    candidate_roster = deepcopy(roster)

    try:
        candidate_roster.assign(
            flight_id=flight.flight_id,
            crew_id=crew.crew_id,
        )
    except ValueError:
        return False

    violations = validate_roster(
        roster=candidate_roster,
        flights=flights,
        crew_list=crew_list,
    )

    crew_violations = [
        violation
        for violation in violations
        if violation.crew_id == crew.crew_id
    ]

    return not crew_violations
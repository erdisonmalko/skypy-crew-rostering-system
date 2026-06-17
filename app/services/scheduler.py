from datetime import datetime
import heapq

from app.models.models import (
    Crew, 
    Flight, 
    Roster, 
    UnassignedFlight
)
from app.services.utils import required_rest_minutes


def generate_schedule(
    flights: dict[str, Flight],
    crew_list: dict[str, Crew],
) -> tuple[Roster, list[UnassignedFlight]]:
    """Generate a legal crew roster using a greedy priority-based scheduler.

    Flights are processed by priority first, then departure time.
    Each flight requires exactly one Captain and one FirstOfficer.
    """

    roster = Roster()
    unassigned_flights: list[UnassignedFlight] = []
    # Heap entries are ordered by priority, then departure time.
    # flight_id is included as a deterministic tie-breaker and lookup key.
    flight_heap: list[tuple[int, datetime, str]] = []

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
            )
        ]

        if not valid_captains:
            unassigned_flights.append(
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
            )
        ]

        if not valid_first_officers:
            unassigned_flights.append(
                UnassignedFlight(
                    flight_id=flight.flight_id,
                    reason="No FirstOfficer available",
                )
            )
            continue

        roster.assign(
            flight_id=flight.flight_id,
            crew_id=valid_captains[0].crew_id,
        )
        roster.assign(
            flight_id=flight.flight_id,
            crew_id=valid_first_officers[0].crew_id,
        )

    return roster, unassigned_flights



def _can_assign_crew_to_flight(
    crew: Crew,
    flight: Flight,
    roster: Roster,
    flights: dict[str, Flight],
) -> bool:
    """Check whether assigning one crew member keeps that crew schedule legal."""

    current_schedule = roster.get_crew_schedule(crew_id=crew.crew_id, flights=flights)
    # make sure the crew member isn't already assigned to this flight
    if any(assigned.flight_id == flight.flight_id for assigned in current_schedule):
        return False

    #add candidate flight to current schedule and sort by departure time to check legality
    candidate_schedule = current_schedule + [flight] 
    candidate_schedule.sort(key=lambda f: f.departure_time)

    return _is_crew_schedule_legal(crew=crew, schedule=candidate_schedule)


def _is_crew_schedule_legal(crew: Crew, schedule: list[Flight]) -> bool:
    """Helper that implements similar logic as rules.py, but optimized for incremental checks during scheduling."""
    if not schedule:
        return True

    if schedule[0].origin != crew.home_base:
        return False

    for flight in schedule:
        if flight.distance_miles > crew.max_range_miles:
            return False

    for previous, current in zip(schedule, schedule[1:]):
        if previous.destination != current.origin:
            return False

        required_rest = required_rest_minutes(previous)
        actual_rest = (
            current.departure_time - previous.arrival_time
        ).total_seconds() / 60
        if actual_rest < required_rest:
            return False

    return True

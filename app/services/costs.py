from app.models.models import Crew, Flight, Roster


def calculate_layover_costs(
    roster: Roster,
    flights: dict[str, Flight],
    crew_list: dict[str, Crew],
) -> tuple[dict[str, float], float]:
    """Calculate layover costs for crew members who end away from home base."""
    layover_costs: dict[str, float] = {}

    for crew in crew_list.values():
        schedule = roster.get_crew_schedule(crew.crew_id, flights)
        if not schedule:
            continue

        last_flight = schedule[-1]
        if last_flight.destination != crew.home_base:
            layover_costs[crew.crew_id] = crew.hourly_cost * 8

    total_layover_cost = sum(layover_costs.values())
    return layover_costs, total_layover_cost

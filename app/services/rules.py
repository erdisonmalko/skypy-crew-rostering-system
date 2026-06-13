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
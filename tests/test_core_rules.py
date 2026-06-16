from datetime import datetime, timedelta

import pytest

from app.models.models import Crew, Flight, Roster
from app.services.costs import calculate_layover_costs
from app.services.pairing import validate_pairing
from app.services.rules import validate_roster


BASE_TIME = datetime(2026, 6, 20, 8, 0, 0)


def make_flight(
    flight_id: str,
    origin: str,
    destination: str,
    departure_offset_minutes: int,
    duration_minutes: int,
    distance_miles: int = 500,
    priority: int = 1,
) -> Flight:
    departure_time = BASE_TIME + timedelta(minutes=departure_offset_minutes)
    return Flight(
        flight_id=flight_id,
        origin=origin,
        destination=destination,
        departure_time=departure_time,
        arrival_time=departure_time + timedelta(minutes=duration_minutes),
        distance_miles=distance_miles,
        priority=priority,
    )


def make_crew(
    crew_id: str,
    home_base: str = "JFK",
    max_range_miles: int = 5000,
    role: str = "Captain",
    hourly_cost: float = 100.0,
) -> Crew:
    return Crew(
        crew_id=crew_id,
        home_base=home_base,
        max_range_miles=max_range_miles,
        role=role,
        hourly_cost=hourly_cost,
    )


def test_range_limit_rejects_flight_beyond_crew_certification() -> None:
    flight = make_flight("F001", "JFK", "LHR", 0, 120, distance_miles=3500)
    crew = make_crew("C001", max_range_miles=2000)
    roster = Roster()
    roster.assign("F001", "C001")

    violations = validate_roster(roster, {"F001": flight}, {"C001": crew})

    assert any("range certification" in v.description.lower() for v in violations)


def test_dynamic_rest_short_flight_accepts_60_minutes() -> None:
    first = make_flight("F001", "JFK", "LHR", 0, 120)
    second = make_flight("F002", "LHR", "CDG", 180, 60)
    crew = make_crew("C001")
    roster = Roster()
    roster.assign("F001", "C001")
    roster.assign("F002", "C001")

    violations = validate_roster(
        roster,
        {"F001": first, "F002": second},
        {"C001": crew},
    )

    assert not violations


def test_dynamic_rest_short_flight_rejects_59_minutes() -> None:
    first = make_flight("F001", "JFK", "LHR", 0, 120)
    second = make_flight("F002", "LHR", "CDG", 179, 60)
    crew = make_crew("C001")
    roster = Roster()
    roster.assign("F001", "C001")
    roster.assign("F002", "C001")

    violations = validate_roster(
        roster,
        {"F001": first, "F002": second},
        {"C001": crew},
    )

    assert any("Insufficient rest" in v.description for v in violations)


def test_dynamic_rest_long_flight_accepts_120_minutes() -> None:
    first = make_flight("F001", "JFK", "LHR", 0, 180)
    second = make_flight("F002", "LHR", "CDG", 300, 60)
    crew = make_crew("C001")
    roster = Roster()
    roster.assign("F001", "C001")
    roster.assign("F002", "C001")

    violations = validate_roster(
        roster,
        {"F001": first, "F002": second},
        {"C001": crew},
    )

    assert not violations


def test_dynamic_rest_long_flight_rejects_119_minutes() -> None:
    first = make_flight("F001", "JFK", "LHR", 0, 180)
    second = make_flight("F002", "LHR", "CDG", 299, 60)
    crew = make_crew("C001")
    roster = Roster()
    roster.assign("F001", "C001")
    roster.assign("F002", "C001")

    violations = validate_roster(
        roster,
        {"F001": first, "F002": second},
        {"C001": crew},
    )

    assert any("Insufficient rest" in v.description for v in violations)


def test_pairing_validation_rejects_two_captains_without_first_officer() -> None:
    flight = make_flight("F001", "JFK", "LHR", 0, 120)
    crew = {
        "C001": make_crew("C001", role="Captain"),
        "C002": make_crew("C002", role="Captain"),
    }
    roster = Roster()
    roster.assign("F001", "C001")
    roster.assign("F001", "C002")

    violations = validate_pairing(
        flight_id=flight.flight_id,
        roster=roster,
        crew_list=crew,
        flights={"F001": flight},
    )

    assert any("expected exactly 1 Captain" in v.description for v in violations)
    assert any("FirstOfficer" in v.description for v in violations)


def test_conflict_guard_rejects_duplicate_crew_flight_assignment() -> None:
    roster = Roster()
    roster.assign("F001", "C001")

    with pytest.raises(ValueError):
        roster.assign("F001", "C001")


def test_layover_costs_include_only_crew_away_from_home_base() -> None:
    flights = {
        "F001": make_flight("F001", "JFK", "LHR", 0, 120),
        "F002": make_flight("F002", "JFK", "LHR", 0, 120),
    }
    crew = {
        "C001": make_crew("C001", home_base="JFK", hourly_cost=100.0),
        "C002": make_crew("C002", home_base="LHR", hourly_cost=80.0),
        "C003": make_crew("C003", home_base="JFK", hourly_cost=75.0),
    }
    roster = Roster()
    roster.assign("F001", "C001")
    roster.assign("F002", "C002")

    layover_costs, total_layover_cost = calculate_layover_costs(
        roster,
        flights,
        crew,
    )

    assert layover_costs == {"C001": 800.0}
    assert total_layover_cost == 800.0


def test_pairing_dynamic_rest_checks_each_assigned_crew_member() -> None:
    previous = make_flight("F001", "JFK", "LHR", 0, 120)
    current = make_flight("F002", "LHR", "CDG", 179, 60)
    flights = {"F001": previous, "F002": current}
    crew = {
        "C001": make_crew("C001", role="Captain"),
        "C002": make_crew("C002", role="FirstOfficer", home_base="LHR"),
    }
    roster = Roster()
    roster.assign("F001", "C001")
    roster.assign("F002", "C001")
    roster.assign("F002", "C002")

    violations = validate_pairing(
        flight_id=current.flight_id,
        roster=roster,
        crew_list=crew,
        flights=flights,
    )

    assert any(v.crew_id == "C001" and "Insufficient rest" in v.description for v in violations)

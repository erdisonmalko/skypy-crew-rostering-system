from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Constants | Rules
DATETIME_FMT = "%Y-%m-%dT%H:%M:%SZ"  # ISO 8601: 2024-02-01T08:00:00Z
VALID_ROLES = {"Captain", "FirstOfficer"}
VALID_PRIORITIES = {1, 2, 3}


# RuleViolation class(used on the services/rules.py file to track rule violations)
@dataclass
class RuleViolation:
    crew_id: str
    flight_id: str
    description: str

# UnassignedFlight class(used to track flights that are not yet assigned to a crew member - services/scheduler.py)
@dataclass
class UnassignedFlight:
    flight_id: str
    reason: str

# Flight class
@dataclass
class Flight:
    flight_id: str
    origin: str         
    destination: str 
    departure_time: datetime
    arrival_time: datetime
    distance_miles: int
    priority: int

    def __post_init__(self) -> None:
        if self.arrival_time <= self.departure_time:
            raise ValueError(
                f"Flight {self.flight_id}: arrival must be after departure "
                f"({self.departure_time} → {self.arrival_time})"
            )
        if not isinstance(self.distance_miles, int) or self.distance_miles <= 0:
            raise ValueError(
                f"Flight {self.flight_id}: distance_miles must be a positive integer, "
                f"got {self.distance_miles!r}"
            )
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Flight {self.flight_id}: priority must be 1, 2, or 3, "
                f"got {self.priority!r}"
            )

    @property
    def duration_minutes(self) -> int:
        return int((self.arrival_time - self.departure_time).total_seconds() // 60)

    @classmethod
    def from_row(cls, row: dict[str, str]) -> Flight:
        return cls(
            flight_id=row["flight_id"].strip(),
            origin=row["origin"].strip(),
            destination=row["destination"].strip(), 
            departure_time=datetime.strptime(row["departure_time"].strip(), DATETIME_FMT),
            arrival_time=datetime.strptime(row["arrival_time"].strip(), DATETIME_FMT),
            distance_miles=int(row["distance_miles"].strip()),
            priority=int(row["priority"].strip()),
        )

    @classmethod
    def load_csv(cls, path: str | Path) -> dict[str, Flight]:
        flights: dict[str, Flight] = {}
        with open(path, newline="", encoding="utf-8") as fh:
            for i, row in enumerate(csv.DictReader(fh), start=2):
                try:
                    f = cls.from_row(row)
                except (ValueError, KeyError) as exc:
                    raise ValueError(f"flights CSV row {i}: {exc}") from exc
                flights[f.flight_id] = f
        return flights



# Crew class

@dataclass
class Crew:
    crew_id: str
    home_base: str
    max_range_miles: int
    role: str
    hourly_cost: float

    def __post_init__(self) -> None:
        if self.role not in VALID_ROLES:
            raise ValueError(
                f"Crew {self.crew_id}: role must be 'Captain' or 'FirstOfficer', "
                f"got {self.role!r}"
            )
        if not isinstance(self.hourly_cost, (int, float)) or self.hourly_cost <= 0:
            raise ValueError(
                f"Crew {self.crew_id}: hourly_cost must be a positive float, "
                f"got {self.hourly_cost!r}"
            )

    @classmethod
    def from_row(cls, row: dict[str, str]) -> Crew:
        return cls(
            crew_id=row["crew_id"].strip(),
            home_base=row["home_base"].strip(),
            max_range_miles=int(row["max_range_miles"].strip()),
            role=row["role"].strip(),
            hourly_cost=float(row["hourly_cost"].strip()),
        )

    @classmethod
    def load_csv(cls, path: str | Path) -> dict[str, Crew]:
        """Load all crew members from a CSV file. Returns {crew_id: Crew}."""
        crew: dict[str, Crew] = {}
        with open(path, newline="", encoding="utf-8") as fh:
            for i, row in enumerate(csv.DictReader(fh), start=2):
                try:
                    c = cls.from_row(row)
                except (ValueError, KeyError) as exc:
                    raise ValueError(f"crew CSV row {i}: {exc}") from exc
                crew[c.crew_id] = c
        return crew



# Roster class

@dataclass
class Roster:
    """Tracks crew assignments per flight.

    Internal structure: {flight_id: [crew_id, ...]}
    """
    _assignments: dict[str, list[str]] = field(default_factory=dict, init=False, repr=False)

    def assign(self, flight_id: str, crew_id: str) -> None:
        """Assign a crew member to a flight.

        Raises ValueError if the same (flight_id, crew_id) pair is added twice.
        """
        crew_list = self._assignments.setdefault(flight_id, [])
        if crew_id in crew_list:
            raise ValueError(
                f"Crew member {crew_id!r} is already assigned to flight {flight_id!r}"
            )
        crew_list.append(crew_id)

    def get_flight_crew(self, flight_id: str) -> list[str]:
        """Return the list of crew_ids assigned to a given flight."""
        return list(self._assignments.get(flight_id, []))

    def get_crew_schedule(self, crew_id: str, flights: dict[str, Flight]) -> list[Flight]:
        """Return all flights for a crew member, sorted by departure time."""
        assigned = [
            flights[fid]
            for fid, crew_list in self._assignments.items()
            if crew_id in crew_list and fid in flights
        ]
        return sorted(assigned, key=lambda f: f.departure_time)

    def all_flight_ids(self) -> list[str]:
        """Return all flight IDs that have at least one crew member assigned."""
        return list(self._assignments.keys())

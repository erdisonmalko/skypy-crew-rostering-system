from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, StrictInt, StrictStr, field_validator

from app.models.models import  Crew, Flight


class FlightInput(BaseModel):
    flight_id: StrictStr = Field(min_length=1)
    origin: StrictStr = Field(min_length=1)
    destination: StrictStr = Field(min_length=1)
    departure: datetime
    arrival: datetime
    distance_miles: StrictInt = Field(gt=0)
    priority: StrictInt

    @field_validator("flight_id", "origin", "destination")
    @classmethod
    def strip_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must be a non-empty string")
        return stripped


    def to_domain(self) -> Flight:
        return Flight(
            flight_id=self.flight_id,
            origin=self.origin,
            destination=self.destination,
            departure_time=self.departure,
            arrival_time=self.arrival,
            distance_miles=self.distance_miles,
            priority=self.priority,
        )


class CrewInput(BaseModel):
    crew_id: StrictStr = Field(min_length=1)
    home_base: StrictStr = Field(min_length=1)
    max_range_miles: StrictInt = Field(gt=0)
    role: StrictStr
    hourly_cost: float = Field(gt=0)

    @field_validator("crew_id", "home_base", "role")
    @classmethod
    def strip_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must be a non-empty string")
        return stripped

    def to_domain(self) -> Crew:
        return Crew(
            crew_id=self.crew_id,
            home_base=self.home_base,
            max_range_miles=self.max_range_miles,
            role=self.role,
            hourly_cost=self.hourly_cost,
        )


class ScheduleRequest(BaseModel):
    flights: list[FlightInput]
    crew: list[CrewInput]

    @field_validator("flights")
    @classmethod
    def validate_unique_flight_ids(cls, flights: list[FlightInput]) -> list[FlightInput]:
        seen: set[str] = set()
        for flight in flights:
            if flight.flight_id in seen:
                raise ValueError(f"duplicate flight_id {flight.flight_id!r}")
            seen.add(flight.flight_id)
        return flights

    @field_validator("crew")
    @classmethod
    def validate_unique_crew_ids(cls, crew: list[CrewInput]) -> list[CrewInput]:
        seen: set[str] = set()
        for member in crew:
            if member.crew_id in seen:
                raise ValueError(f"duplicate crew_id {member.crew_id!r}")
            seen.add(member.crew_id)
        return crew

    def to_domain(self) -> tuple[dict[str, Flight], dict[str, Crew]]:
        flights = {
            flight.flight_id: flight.to_domain()
            for flight in self.flights
        }
        crew = {
            member.crew_id: member.to_domain()
            for member in self.crew
        }
        return flights, crew

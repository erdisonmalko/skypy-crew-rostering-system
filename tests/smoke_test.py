from app.models.models import Crew, Flight
from app.services.scheduler import generate_schedule
from app.services.pairing import validate_pairing
from app.services.rules import validate_roster


def main() -> None:
    flights = Flight.load_csv("data/csv/small/flights.csv")
    crew = Crew.load_csv("data/csv/small/crew.csv")

    print("Loaded flights:")
    for flight in flights.values():
        print(
            flight.flight_id,
            flight.origin,
            "->",
            flight.destination,
            flight.duration_minutes,
            "min",
            "priority",
            flight.priority,
        )

    print("\nLoaded crew:")
    for member in crew.values():
        print(
            member.crew_id,
            member.role,
            "base:",
            member.home_base,
            "range:",
            member.max_range_miles,
        )

    roster, unassigned = generate_schedule(flights, crew)

    print("\nRoster assignments:")
    for flight_id in flights:
        print(flight_id, "=>", roster.get_flight_crew(flight_id))

    print("\nUnassigned flights:")
    for item in unassigned:
        print(item.flight_id, "-", item.reason)

    print("\nRoster violations:")
    violations = validate_roster(roster, flights, crew)
    if not violations:
        print("No violations found.")
    else:
        for violation in violations:
            print(
                violation.crew_id,
                violation.flight_id,
                violation.description,
            )

    print("\nPairing validation:")
    for flight in flights.values():
        pairing_violations = validate_pairing(
            flight=flight,
            roster=roster,
            crew_list=crew,
            flights=flights,
        )

        if not pairing_violations:
            print(flight.flight_id, "pairing valid")
        else:
            print(flight.flight_id, "pairing invalid:")
            for violation in pairing_violations:
                print(" ", violation.description)


if __name__ == "__main__":
    main()

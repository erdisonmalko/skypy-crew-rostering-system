"""Script to generate a crew roster from CSV inputs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

#to avoid module not found errror when running this script directly
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.models.models import Crew, Flight
from app.services.export import build_roster_output
from app.services.scheduler import generate_schedule


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a crew roster from CSV inputs.")
    parser.add_argument(
        "--flights",
        default="data/csv/flights.csv",
        help="Path to flights CSV",
    )
    parser.add_argument(
        "--crew",
        default="data/csv/crew.csv",
        help="Path to crew CSV",
    )
    parser.add_argument(
        "--output",
        default="data/output/roster_output.json",
        help="Path for generated roster JSON",
    )
    args = parser.parse_args()

    flights = Flight.load_csv(args.flights)
    crew = Crew.load_csv(args.crew)
    roster, unassigned = generate_schedule(flights=flights, crew_list=crew)
    output = build_roster_output(
        roster=roster,
        flights=flights,
        crew_list=crew,
        unassigned=unassigned,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

    scheduled_count = len(flights) - len(unassigned)
    print(f"Scheduled {scheduled_count}/{len(flights)} flights")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()

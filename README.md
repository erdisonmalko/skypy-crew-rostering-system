# SkyPy Crew Rostering System

Backend scheduling engine for assigning legal crew pairs to flights. It loads
flight and crew data, applies range, home-base, route-continuity, rest, pairing,
and layover-cost rules, and exposes the scheduler through both CSV and Flask API
entry points.

## What Is Included

- Dataclass domain models for `Flight`, `Crew`, `Roster`, violations, and unassigned flights.
- Rule validation for range certification, home-base start, route continuity, and dynamic rest.
- Pairing validation for exactly one Captain and at least one First Officer.
- Greedy priority scheduler using `heapq`.
- Layover-cost calculation.
- Flask API with JSON request validation through Pydantic schemas.
- CSV runner that writes `data/output/roster_output.json`.
- Dockerfile and Makefile for local onboarding.

## Setup

```bash
python3 -m venv .venv
pip3 install -r requirements.txt
```

Run all tests:

```bash
python3 -m pytest tests/ -v
```

## Generate Roster From CSV

Default input is the small sample dataset:

```bash
python3 scripts/generate_roster.py
```

Custom input:

```bash
python3 scripts/generate_roster.py \
  --flights data/csv/large/flights.csv \
  --crew data/csv/large/crew.csv \
  --output data/output/roster_output.json
```

## Run Flask API

```bash
flask --app app:create_app run
```

Endpoints:

- `POST /schedule`
- `GET /roster/<crew_id>`
- `GET /report`
- `GET /health`

Example schedule request:

```bash
curl -X POST http://127.0.0.1:5000/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "flights": [
      {
        "flight_id": "F001",
        "origin": "JFK",
        "destination": "LHR",
        "departure": "2026-06-20T08:00:00Z",
        "arrival": "2026-06-20T10:00:00Z",
        "distance_miles": 3500,
        "priority": 1
      }
    ],
    "crew": [
      {
        "crew_id": "C001",
        "home_base": "JFK",
        "max_range_miles": 5000,
        "role": "Captain",
        "hourly_cost": 100.0
      },
      {
        "crew_id": "C002",
        "home_base": "JFK",
        "max_range_miles": 5000,
        "role": "FirstOfficer",
        "hourly_cost": 80.0
      }
    ]
  }'
```

## Docker

```bash
docker build -t skypy-crew-rostering .
docker run --rm -p 5000:5000 skypy-crew-rostering
```

Detached mode:

```bash
docker run --rm -d --name skypy-crew-rostering -p 5000:5000 skypy-crew-rostering
docker stop skypy-crew-rostering
```

## Make Targets

```bash
make build
make run
make stop
make delete
make test
make generate
```

## Notes

- The scheduler processes flights by priority first, then departure time.
- Assignments are all-or-nothing: a flight is assigned only when a valid Captain and First Officer pair is found.
- The API stores the latest schedule in memory only; no database is used.
- `departure` and `arrival` are external CSV/API fields. Internally they map to `departure_time` and `arrival_time`.

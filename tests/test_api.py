from app import create_app


def _payload() -> dict:
    return {
        "flights": [
            {
                "flight_id": "F001",
                "origin": "JFK",
                "destination": "LHR",
                "departure": "2026-06-20T08:00:00Z",
                "arrival": "2026-06-20T10:00:00Z",
                "distance_miles": 3500,
                "priority": 1,
            }
        ],
        "crew": [
            {
                "crew_id": "C001",
                "home_base": "JFK",
                "max_range_miles": 5000,
                "role": "Captain",
                "hourly_cost": 100.0,
            },
            {
                "crew_id": "C002",
                "home_base": "JFK",
                "max_range_miles": 5000,
                "role": "FirstOfficer",
                "hourly_cost": 80.0,
            },
        ],
    }


def test_schedule_roster_and_report_endpoints() -> None:
    client = create_app().test_client()

    schedule_response = client.post("/schedule", json=_payload())

    assert schedule_response.status_code == 200
    assert schedule_response.get_json() == {
        "roster": {"F001": ["C001", "C002"]},
        "unassigned": [],
    }

    roster_response = client.get("/roster/C001")

    assert roster_response.status_code == 200
    assert roster_response.get_json() == {
        "crew_id": "C001",
        "flight_ids": ["F001"],
        "total_flight_hours": 2.0,
        "layover_cost": 800.0,
    }

    report_response = client.get("/report")
    report = report_response.get_json()

    assert report_response.status_code == 200
    assert report["total_flights_scheduled"] == 1
    assert report["total_unassigned_flights"] == 0
    assert report["total_layover_cost"] == 1440.0
    assert report["crew"]["C001"]["flights"] == ["F001"]
    assert report["crew"]["C002"]["flights"] == ["F001"]


def test_schedule_rejects_invalid_payload() -> None:
    client = create_app().test_client()

    response = client.post("/schedule", json={"flights": "bad", "crew": []})

    assert response.status_code == 400
    assert "error" in response.get_json()

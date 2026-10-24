"""
Decisions API Integration & Cross-User Security Tests
Verifies full CRUD lifecycle, calculation, What-if simulation, CSV export,
and strict multi-user data isolation.
"""


def create_sample_decision_payload():
    return {
        "title": "Which Laptop to Buy?",
        "description": "Evaluating MacBook Pro vs ThinkPad X1 vs Dell XPS",
        "options": [
            {"id": "opt_mac", "name": "MacBook Pro 14", "attributes": {"price": 1999, "battery_hours": 16}},
            {"id": "opt_think", "name": "ThinkPad X1 Carbon", "attributes": {"price": 1450, "battery_hours": 13}},
            {"id": "opt_dell", "name": "Dell XPS 13", "attributes": {"price": 1200, "battery_hours": 9}},
        ],
        "criteria": [
            {"id": "crit_perf", "name": "Build & Performance", "weight": 50.0},
            {"id": "crit_port", "name": "Portability & Battery", "weight": 30.0},
            {"id": "crit_value", "name": "Value for Money", "weight": 20.0},
        ],
        "ratings": [
            # MacBook Pro ratings
            {"option_id": "opt_mac", "criterion_id": "crit_perf", "rating": 9.5},
            {"option_id": "opt_mac", "criterion_id": "crit_port", "rating": 9.0},
            {"option_id": "opt_mac", "criterion_id": "crit_value", "rating": 6.0},
            # ThinkPad ratings
            {"option_id": "opt_think", "criterion_id": "crit_perf", "rating": 8.5},
            {"option_id": "opt_think", "criterion_id": "crit_port", "rating": 8.5},
            {"option_id": "opt_think", "criterion_id": "crit_value", "rating": 8.0},
            # Dell XPS ratings
            {"option_id": "opt_dell", "criterion_id": "crit_perf", "rating": 7.5},
            {"option_id": "opt_dell", "criterion_id": "crit_port", "rating": 7.0},
            {"option_id": "opt_dell", "criterion_id": "crit_value", "rating": 8.5},
        ],
        "constraints": [
            {"name": "Min Battery", "attribute_key": "battery_hours", "operator": ">=", "threshold": 10.0}
        ]
    }


def test_create_and_get_decision(user_a_client):
    payload = create_sample_decision_payload()
    res = user_a_client.post("/api/decisions", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Which Laptop to Buy?"
    assert len(data["options"]) == 3
    assert len(data["criteria"]) == 3
    assert len(data["constraints"]) == 1

    dec_id = data["id"]

    # Retrieve decision
    get_res = user_a_client.get(f"/api/decisions/{dec_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == dec_id


def test_list_decisions_and_search(user_a_client):
    # List decisions
    res = user_a_client.get("/api/decisions")
    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 1

    # Search filter matching
    res_search = user_a_client.get("/api/decisions?q=Laptop")
    assert res_search.status_code == 200
    assert len(res_search.json()) >= 1

    # Search filter non-matching
    res_empty = user_a_client.get("/api/decisions?q=NonExistentKeywordXYZ")
    assert res_empty.status_code == 200
    assert len(res_empty.json()) == 0


def test_calculate_and_what_if_simulation(user_a_client):
    # Create decision
    payload = create_sample_decision_payload()
    dec = user_a_client.post("/api/decisions", json=payload).json()
    dec_id = dec["id"]

    # Calculate baseline
    calc_res = user_a_client.post(f"/api/decisions/{dec_id}/calculate")
    assert calc_res.status_code == 200
    results = calc_res.json()
    assert results["total_options_evaluated"] == 3
    # Dell XPS has battery_hours = 9, constraint requires >= 10 -> Ineligible
    assert results["eligible_count"] == 2
    assert results["ineligible_count"] == 1

    dell_opt = next(o for o in results["options"] if "Dell" in o["option_name"])
    assert dell_opt["is_eligible"] is False
    assert any("battery_hours is 9" in r for r in dell_opt["failed_constraints"])

    # What-if Simulation: Shift weights temporarily
    # Get criteria IDs
    perf_id = next(c["id"] for c in dec["criteria"] if "Build" in c["name"])
    port_id = next(c["id"] for c in dec["criteria"] if "Portability" in c["name"])
    val_id = next(c["id"] for c in dec["criteria"] if "Value" in c["name"])

    # Simulate: Value for Money becomes 90%, Build 5%, Portability 5%
    sim_payload = {
        "temporary_weights": {
            perf_id: 5.0,
            port_id: 5.0,
            val_id: 90.0
        }
    }
    sim_res = user_a_client.post(f"/api/decisions/{dec_id}/calculate", json=sim_payload)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["weights_total"] == 100.0

    # Verify that the original saved weights in database are STILL UNCHANGED
    refetched = user_a_client.get(f"/api/decisions/{dec_id}").json()
    saved_perf = next(c for c in refetched["criteria"] if c["id"] == perf_id)
    assert saved_perf["weight"] == 50.0  # Still 50%, NOT 5%


def test_cross_user_isolation(user_a_client, user_b_client):
    """
    CRITICAL SECURITY TEST:
    Verifies that User B cannot read, update, calculate, export, or delete User A's decisions.
    """
    # User A creates a private decision
    payload = create_sample_decision_payload()
    payload["title"] = "User A Private Confidential Evaluation"
    decision_a = user_a_client.post("/api/decisions", json=payload).json()
    decision_id = decision_a["id"]

    # 1. User B tries to GET User A's decision
    res_b_get = user_b_client.get(f"/api/decisions/{decision_id}")
    assert res_b_get.status_code == 404
    assert res_b_get.json()["detail"] == "Decision not found."

    # 2. User B tries to list decisions -> User A's decision must NOT appear in User B's list
    res_b_list = user_b_client.get("/api/decisions")
    assert res_b_list.status_code == 200
    user_b_ids = [d["id"] for d in res_b_list.json()]
    assert decision_id not in user_b_ids

    # 3. User B tries to PUT (update) User A's decision
    res_b_put = user_b_client.put(f"/api/decisions/{decision_id}", json={"title": "Hacked Title"})
    assert res_b_put.status_code == 404

    # 4. User B tries to calculate User A's decision
    res_b_calc = user_b_client.post(f"/api/decisions/{decision_id}/calculate")
    assert res_b_calc.status_code == 404

    # 5. User B tries to export User A's decision
    res_b_export = user_b_client.get(f"/api/decisions/{decision_id}/export")
    assert res_b_export.status_code == 404

    # 6. User B tries to delete User A's decision
    res_b_delete = user_b_client.delete(f"/api/decisions/{decision_id}")
    assert res_b_delete.status_code == 404

    # Confirm User A's decision is still intact and untampered
    confirm = user_a_client.get(f"/api/decisions/{decision_id}")
    assert confirm.status_code == 200
    assert confirm.json()["title"] == "User A Private Confidential Evaluation"


def test_csv_export(user_a_client):
    payload = create_sample_decision_payload()
    dec = user_a_client.post("/api/decisions", json=payload).json()
    dec_id = dec["id"]

    res = user_a_client.get(f"/api/decisions/{dec_id}/export")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "attachment" in res.headers["content-disposition"]
    csv_text = res.text
    assert "Which Laptop to Buy?" in csv_text
    assert "MacBook Pro 14" in csv_text
    assert "Rank" in csv_text


def test_delete_decision(user_a_client):
    payload = create_sample_decision_payload()
    dec = user_a_client.post("/api/decisions", json=payload).json()
    dec_id = dec["id"]

    # Delete
    del_res = user_a_client.delete(f"/api/decisions/{dec_id}")
    assert del_res.status_code == 204

    # Subsequent GET must return 404
    get_res = user_a_client.get(f"/api/decisions/{dec_id}")
    assert get_res.status_code == 404

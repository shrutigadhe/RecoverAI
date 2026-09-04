def test_batch_evaluation_endpoint(client):
    response = client.post("/api/evaluation/run")
    assert response.status_code == 200
    data = response.json()
    assert data["total_cases"] == 100
    assert data["total_revenue_at_risk"] > 0
    assert data["recovery_attempts"] > 0
    assert data["successful_recoveries"] > 0
    assert data["total_recovered_revenue"] > 0
    assert "recovery_rate_percentage" in data

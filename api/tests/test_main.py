import requests

def test_health_check():
    """
    Tests if the /health endpoint returns a 200 OK status.
    """
    try:
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    except requests.exceptions.ConnectionError as e:
        print(f"Could not connect to the API: {e}")
        print("Please make sure the GAD services are running with 'docker compose up -d' before running the tests.")
        assert False, "API connection failed"

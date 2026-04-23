from fastapi.testclient import TestClient


def _get_token(client: TestClient, username: str = "ci_testuser", password: str = "CiPass123!") -> str:
    """Register (or login if already exists) and return a bearer token."""
    resp = client.post("/api/register", json={
        "username": username,
        "email": f"{username}@example.com",
        "password": password,
    })
    if resp.status_code == 400:
        resp = client.post("/api/login", json={"username": username, "password": password})
    resp.raise_for_status()
    return resp.json()["access_token"]


def test_health(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}


def test_register_new_user(client: TestClient):
    resp = client.post("/api/register", json={
        "username": "brand_new_user",
        "email": "brand_new_user@example.com",
        "password": "NewUser123!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "brand_new_user"


def test_register_duplicate_rejected(client: TestClient):
    payload = {"username": "dup_user", "email": "dup_user@example.com", "password": "Dup123!"}
    client.post("/api/register", json=payload)
    resp = client.post("/api/register", json=payload)
    assert resp.status_code == 400


def test_login_success(client: TestClient):
    client.post("/api/register", json={
        "username": "login_ok",
        "email": "login_ok@example.com",
        "password": "Login123!",
    })
    resp = client.post("/api/login", json={"username": "login_ok", "password": "Login123!"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client: TestClient):
    client.post("/api/register", json={
        "username": "login_fail",
        "email": "login_fail@example.com",
        "password": "Correct123!",
    })
    resp = client.post("/api/login", json={"username": "login_fail", "password": "Wrong123!"})
    assert resp.status_code == 401


def test_get_patients_returns_list(client: TestClient):
    resp = client.get("/api/patients")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 5


def test_get_patients_pagination(client: TestClient):
    resp = client.get("/api/patients?skip=0&limit=2")
    assert resp.status_code == 200
    assert len(resp.json()) <= 2


def test_get_single_patient(client: TestClient):
    resp = client.get("/api/patients/MG-4829-X")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Elena Vance"


def test_get_patient_not_found(client: TestClient):
    resp = client.get("/api/patients/DOES-NOT-EXIST")
    assert resp.status_code == 404


def test_search_patients_by_name(client: TestClient):
    resp = client.get("/api/patients/search?query=Elena")
    assert resp.status_code == 200
    results = resp.json()
    assert any("Elena" in p["name"] for p in results)


def test_search_patients_risk_filter(client: TestClient):
    resp = client.get("/api/patients/search?risk_min=85&risk_max=100")
    assert resp.status_code == 200
    for p in resp.json():
        assert p["risk_score"] >= 85


def test_create_patient_requires_auth(client: TestClient):
    resp = client.post("/api/patients", json={
        "name": "No Auth Patient",
        "age": 30,
        "risk_score": 50.0,
        "dna_marker": "T+1",
        "initials": "NP",
    })
    assert resp.status_code == 401


def test_create_patient_with_auth(client: TestClient):
    token = _get_token(client)
    resp = client.post(
        "/api/patients",
        json={"name": "Auth Patient", "age": 35, "risk_score": 65.0, "dna_marker": "A+3", "initials": "AP"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Auth Patient"


def test_get_inventory_returns_list(client: TestClient):
    resp = client.get("/api/inventory")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 8


def test_get_inventory_pagination(client: TestClient):
    resp = client.get("/api/inventory?skip=0&limit=3")
    assert resp.status_code == 200
    assert len(resp.json()) <= 3


def test_search_inventory_by_category(client: TestClient):
    resp = client.get("/api/inventory/search?category=Reagents")
    assert resp.status_code == 200
    for item in resp.json():
        assert item["category"] == "Reagents"


def test_adjust_inventory_requires_auth(client: TestClient):
    resp = client.put("/api/inventory/INV-001/adjust", json={"qty_on_hand": 100})
    assert resp.status_code == 401


def test_adjust_inventory_with_auth(client: TestClient):
    token = _get_token(client)
    resp = client.put(
        "/api/inventory/INV-001/adjust",
        json={"qty_on_hand": 75},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["qty_on_hand"] == 75


def test_export_report_csv(client: TestClient):
    resp = client.get("/api/export/report")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]


def test_export_analytics_csv(client: TestClient):
    resp = client.get("/api/analytics/export")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]

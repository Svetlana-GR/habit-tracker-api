from fastapi.testclient import TestClient
from app_final import app
from datetime import date, timedelta

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_and_list():
    response = client.post("/habits", json={"name": "Read"})
    assert response.status_code == 200
    
    response = client.get("/habits")
    data = response.json()
    assert len(data) == 1
    # Теперь проверяем первый (и единственный) элемент списка по индексу 0
    assert data[0]["name"] == "Read"

def test_streak_logic_with_dates():
    # Создаем привычку
    resp = client.post("/habits", json={"name": "Yoga"})
    habit_id = resp.json()["id"]
    
    # Чекаем 24 октября (стал 1)
    start_date = date(2025, 10, 24).isoformat()
    client.post(f"/habits/{habit_id}/check", json={"check_date": start_date})
    
    # Чекаем 25 октября (стал 2)
    next_day = (date(2025, 10, 24) + timedelta(days=1)).isoformat()
    resp = client.post(f"/habits/{habit_id}/check", json={"check_date": next_day})
    assert resp.json()["streak"] == 2

def test_check_same_day():
    resp = client.post("/habits", json={"name": "Meditate"})
    habit_id = resp.json()["id"]
    
    today = date.today().isoformat()
    client.post(f"/habits/{habit_id}/check", json={"check_date": today})
    
    # Пытаемся чекнуть еще раз
    resp = client.post(f"/habits/{habit_id}/check", json={"check_date": today})
    assert resp.json()["message"] == "Already checked for this date"


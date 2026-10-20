from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    assert client.get('/health').json() == {'status': 'ok'}

def test_nearby_empty_until_import():
    resp = client.get('/api/facilities/nearby', params={'latitude': 36.35, 'longitude': 127.38})
    assert resp.status_code == 200
    assert resp.json() == {'facilities': [], 'count': 0}

def test_invalid_facility_type_rejected():
    assert client.get('/api/facilities/nearby', params={'latitude': 36.35, 'longitude': 127.38, 'facility_type': 'hospital'}).status_code == 422

def test_recommendation_unconfigured():
    resp = client.post('/api/aeds/recommendations', json={'start': {'latitude': 36.35, 'longitude': 127.38}, 'departure_at': '2026-10-20T15:00:00+09:00'})
    assert resp.status_code == 503

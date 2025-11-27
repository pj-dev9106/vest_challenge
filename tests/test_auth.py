def test_missing_api_key(client):
    response = client.get('/api/blotter?date=2025-01-15')
    assert response.status_code == 401
    assert b'API key is missing' in response.data


def test_invalid_api_key(client):
    headers = {'X-API-Key': 'invalid-key'}
    response = client.get('/api/blotter?date=2025-01-15', headers=headers)
    assert response.status_code == 403
    assert b'Invalid API key' in response.data


def test_valid_api_key(client, api_headers):
    response = client.get('/api/blotter?date=2025-01-15', headers=api_headers)
    assert response.status_code != 401
    assert response.status_code != 403


from datetime import date
from app.models import db, Trade


def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'database' in data


def test_blotter_missing_date(client, api_headers):
    response = client.get('/api/blotter', headers=api_headers)
    assert response.status_code == 400
    data = response.get_json()
    assert 'Date parameter is required' in data['error']


def test_blotter_invalid_date(client, api_headers):
    response = client.get('/api/blotter?date=invalid', headers=api_headers)
    assert response.status_code == 400
    data = response.get_json()
    assert 'Invalid date format' in data['error']


def test_blotter_empty_data(client, api_headers):
    response = client.get('/api/blotter?date=2025-01-15', headers=api_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 0
    assert data['data'] == []


def test_blotter_with_data(app, client, api_headers):
    with app.app_context():
        trade1 = Trade(
            trade_date=date(2025, 1, 15),
            account_id='ACC001',
            ticker='AAPL',
            shares=100,
            price=185.50,
            trade_type='BUY',
            settlement_date=date(2025, 1, 17),
            file_format='format1'
        )
        trade2 = Trade(
            trade_date=date(2025, 1, 15),
            account_id='ACC001',
            ticker='MSFT',
            shares=50,
            market_value=21012.50,
            source_system='CUSTODIAN_A',
            file_format='format2'
        )
        db.session.add(trade1)
        db.session.add(trade2)
        db.session.commit()
    
    response = client.get('/api/blotter?date=2025-01-15', headers=api_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['count'] == 2
    assert len(data['data']) == 2
    
    format1_trade = next(t for t in data['data'] if t['ticker'] == 'AAPL')
    assert format1_trade['shares'] == 100
    assert format1_trade['price'] == 185.50
    assert format1_trade['trade_type'] == 'BUY'
    
    format2_trade = next(t for t in data['data'] if t['ticker'] == 'MSFT')
    assert format2_trade['shares'] == 50
    assert format2_trade['market_value'] == 21012.50


def test_positions_with_data(app, client, api_headers):
    with app.app_context():
        trades = [
            Trade(
                trade_date=date(2025, 1, 15),
                account_id='ACC001',
                ticker='AAPL',
                shares=100,
                price=185.50,
                trade_type='BUY',
                file_format='format1'
            ),
            Trade(
                trade_date=date(2025, 1, 15),
                account_id='ACC001',
                ticker='MSFT',
                shares=50,
                price=420.25,
                trade_type='BUY',
                file_format='format1'
            ),
            Trade(
                trade_date=date(2025, 1, 15),
                account_id='ACC001',
                ticker='GOOGL',
                shares=100,
                price=142.80,
                trade_type='BUY',
                file_format='format1'
            ),
        ]
        for trade in trades:
            db.session.add(trade)
        db.session.commit()
    
    response = client.get('/api/positions?date=2025-01-15', headers=api_headers)
    assert response.status_code == 200
    data = response.get_json()
    
    acc001 = data['positions']['ACC001']
    
    assert 'AAPL' in acc001
    assert 'MSFT' in acc001
    assert 'GOOGL' in acc001
    
    assert 34 <= acc001['AAPL'] <= 35
    assert 39 <= acc001['MSFT'] <= 40
    assert 26 <= acc001['GOOGL'] <= 27
    
    total_percentage = sum(acc001.values())
    assert 99.9 <= total_percentage <= 100.1


def test_positions_multiple_accounts(app, client, api_headers):
    with app.app_context():
        trades = [
            Trade(
                trade_date=date(2025, 1, 15),
                account_id='ACC001',
                ticker='AAPL',
                shares=100,
                market_value=18550.00,
                source_system='CUSTODIAN_A',
                file_format='format2'
            ),
            Trade(
                trade_date=date(2025, 1, 15),
                account_id='ACC002',
                ticker='AAPL',
                shares=200,
                market_value=37100.00,
                source_system='CUSTODIAN_B',
                file_format='format2'
            ),
        ]
        for trade in trades:
            db.session.add(trade)
        db.session.commit()
    
    response = client.get('/api/positions?date=2025-01-15', headers=api_headers)
    assert response.status_code == 200
    data = response.get_json()
    
    assert 'ACC001' in data['positions']
    assert 'ACC002' in data['positions']
    
    assert data['positions']['ACC001']['AAPL'] == 100.0
    assert data['positions']['ACC002']['AAPL'] == 100.0


def test_alarms_no_violations(app, client, api_headers):
    with app.app_context():
        trades = [
            Trade(
                trade_date=date(2025, 1, 15),
                account_id='ACC001',
                ticker='AAPL',
                shares=100,
                price=100,
                file_format='format1'
            ),
            Trade(
                trade_date=date(2025, 1, 15),
                account_id='ACC001',
                ticker='MSFT',
                shares=100,
                price=100,
                file_format='format1'
            ),
            Trade(
                trade_date=date(2025, 1, 15),
                account_id='ACC001',
                ticker='GOOGL',
                shares=100,
                price=100,
                file_format='format1'
            ),
            Trade(
                trade_date=date(2025, 1, 15),
                account_id='ACC001',
                ticker='TSLA',
                shares=100,
                price=100,
                file_format='format1'
            ),
            Trade(
                trade_date=date(2025, 1, 15),
                account_id='ACC001',
                ticker='NVDA',
                shares=100,
                price=100,
                file_format='format1'
            ),
        ]
        for trade in trades:
            db.session.add(trade)
        db.session.commit()
    
    response = client.get('/api/alarms?date=2025-01-15', headers=api_headers)
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['alarms']['ACC001'] is False
    assert len(data['violations']) == 0


def test_alarms_with_violations(app, client, api_headers):
    with app.app_context():
        trades = [
            Trade(
                trade_date=date(2025, 1, 15),
                account_id='ACC004',
                ticker='AAPL',
                shares=500,
                market_value=92750.00,
                source_system='CUSTODIAN_C',
                file_format='format2'
            ),
            Trade(
                trade_date=date(2025, 1, 15),
                account_id='ACC004',
                ticker='MSFT',
                shares=300,
                market_value=126075.00,
                source_system='CUSTODIAN_C',
                file_format='format2'
            ),
        ]
        for trade in trades:
            db.session.add(trade)
        db.session.commit()
    
    response = client.get('/api/alarms?date=2025-01-15', headers=api_headers)
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['alarms']['ACC004'] is True
    assert len(data['violations']) == 1
    
    violation = data['violations'][0]
    assert violation['account_id'] == 'ACC004'
    assert len(violation['violations']) == 2
    
    tickers_violated = [v['ticker'] for v in violation['violations']]
    assert 'AAPL' in tickers_violated
    assert 'MSFT' in tickers_violated


def test_positions_empty_date(client, api_headers):
    response = client.get('/api/positions?date=2025-01-15', headers=api_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['positions'] == {}


def test_alarms_empty_date(client, api_headers):
    response = client.get('/api/alarms?date=2025-01-15', headers=api_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['alarms'] == {}

def test_alarms_triggers_alerts(app, client, api_headers, monkeypatch):
    """Ensure that send_violation_alert is called when there are violations."""
    called = []

    def fake_send_violation_alert(account_id, violations):
        called.append((account_id, violations))

    monkeypatch.setattr('app.routes.api.send_violation_alert', fake_send_violation_alert)

    with app.app_context():
        trades = [
            Trade(
                trade_date=date(2025, 1, 15),
                account_id='ACC_ALERT',
                ticker='AAPL',
                shares=500,
                market_value=90000.00,
                source_system='CUSTODIAN_X',
                file_format='format2'
            ),
            Trade(
                trade_date=date(2025, 1, 15),
                account_id='ACC_ALERT',
                ticker='MSFT',
                shares=100,
                market_value=10000.00,
                source_system='CUSTODIAN_X',
                file_format='format2'
            ),
        ]
        db.session.add_all(trades)
        db.session.commit()

    response = client.get('/api/alarms?date=2025-01-15', headers=api_headers)
    assert response.status_code == 200

    assert len(called) == 1
    account_id, violations = called[0]
    assert account_id == 'ACC_ALERT'
    assert len(violations) >= 1
    tickers = {v['ticker'] for v in violations}
    assert 'AAPL' in tickers

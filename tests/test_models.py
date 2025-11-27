from datetime import date
from app.models import db, Trade


def test_trade_creation(app):
    with app.app_context():
        trade = Trade(
            trade_date=date(2025, 1, 15),
            account_id='ACC001',
            ticker='AAPL',
            shares=100,
            price=185.50,
            trade_type='BUY',
            settlement_date=date(2025, 1, 17),
            file_format='format1'
        )
        
        db.session.add(trade)
        db.session.commit()
        
        retrieved = Trade.query.filter_by(account_id='ACC001').first()
        assert retrieved is not None
        assert retrieved.ticker == 'AAPL'
        assert float(retrieved.shares) == 100
        assert float(retrieved.price) == 185.50


def test_trade_to_dict(app):
    with app.app_context():
        trade = Trade(
            trade_date=date(2025, 1, 15),
            account_id='ACC002',
            ticker='MSFT',
            shares=50,
            market_value=21012.50,
            source_system='CUSTODIAN_A',
            file_format='format2'
        )
        
        trade_dict = trade.to_dict()
        
        assert trade_dict['account_id'] == 'ACC002'
        assert trade_dict['ticker'] == 'MSFT'
        assert trade_dict['shares'] == 50
        assert trade_dict['market_value'] == 21012.50
        assert trade_dict['source_system'] == 'CUSTODIAN_A'


def test_negative_shares(app):
    with app.app_context():
        trade = Trade(
            trade_date=date(2025, 1, 15),
            account_id='ACC003',
            ticker='TSLA',
            shares=-150,
            market_value=-35767.50,
            source_system='CUSTODIAN_A',
            file_format='format2'
        )
        
        db.session.add(trade)
        db.session.commit()
        
        retrieved = Trade.query.filter_by(ticker='TSLA').first()
        assert float(retrieved.shares) == -150

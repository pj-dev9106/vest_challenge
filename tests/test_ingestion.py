from app.services.ingestion import parse_format1_file, parse_format2_file, ingest_file
from app.models import db, Trade


def test_parse_format1():
    file_content = """TradeDate,AccountID,Ticker,Quantity,Price,TradeType,SettlementDate
2025-01-15,ACC001,AAPL,100,185.50,BUY,2025-01-17
2025-01-15,ACC001,MSFT,50,420.25,SELL,2025-01-17"""
    
    trades = parse_format1_file(file_content)
    
    assert len(trades) == 2
    
    assert trades[0].account_id == 'ACC001'
    assert trades[0].ticker == 'AAPL'
    assert float(trades[0].shares) == 100
    assert float(trades[0].price) == 185.50
    assert trades[0].trade_type == 'BUY'
    
    assert trades[1].ticker == 'MSFT'
    assert float(trades[1].shares) == -50
    assert trades[1].trade_type == 'SELL'


def test_parse_format2():
    file_content = """20250115|ACC001|AAPL|100|18550.00|CUSTODIAN_A
20250115|ACC002|MSFT|50|21012.50|CUSTODIAN_B"""
    
    trades = parse_format2_file(file_content)
    
    assert len(trades) == 2
    
    assert trades[0].account_id == 'ACC001'
    assert trades[0].ticker == 'AAPL'
    assert float(trades[0].shares) == 100
    assert float(trades[0].market_value) == 18550.00
    assert trades[0].source_system == 'CUSTODIAN_A'
    
    assert trades[1].account_id == 'ACC002'
    assert trades[1].ticker == 'MSFT'


def test_parse_format2_negative_shares():
    file_content = """20250115|ACC003|TSLA|-150|-35767.50|CUSTODIAN_A"""
    
    trades = parse_format2_file(file_content)
    
    assert len(trades) == 1
    assert float(trades[0].shares) == -150
    assert float(trades[0].market_value) == -35767.50


def test_ingest_format1_file(app):
    file_content = """TradeDate,AccountID,Ticker,Quantity,Price,TradeType,SettlementDate
2025-01-15,ACC001,AAPL,100,185.50,BUY,2025-01-17
2025-01-15,ACC002,GOOGL,75,142.80,BUY,2025-01-17"""
    
    with app.app_context():
        success_count, error_count = ingest_file(file_content, 'format1')
        
        assert success_count == 2
        assert error_count == 0
        
        trades = Trade.query.all()
        assert len(trades) == 2
        
        aapl_trade = Trade.query.filter_by(ticker='AAPL').first()
        assert aapl_trade is not None
        assert aapl_trade.account_id == 'ACC001'


def test_ingest_format2_file(app):
    file_content = """20250115|ACC001|AAPL|100|18550.00|CUSTODIAN_A
20250115|ACC002|AAPL|200|37100.00|CUSTODIAN_B"""
    
    with app.app_context():
        success_count, error_count = ingest_file(file_content, 'format2')
        
        assert success_count == 2
        assert error_count == 0
        
        trades = Trade.query.all()
        assert len(trades) == 2


def test_parse_format1_malformed_data():
    file_content = """TradeDate,AccountID,Ticker,Quantity,Price,TradeType,SettlementDate
2025-01-15,ACC001,AAPL,100,185.50,BUY,2025-01-17
invalid-date,ACC002,GOOGL,75,142.80,BUY,2025-01-17
2025-01-15,ACC003,MSFT,50,420.25,BUY,2025-01-17"""
    
    trades = parse_format1_file(file_content)
    
    assert len(trades) == 2
    assert trades[0].ticker == 'AAPL'
    assert trades[1].ticker == 'MSFT'


def test_parse_format2_malformed_data():
    file_content = """20250115|ACC001|AAPL|100|18550.00|CUSTODIAN_A
invalid|data|here
20250115|ACC002|MSFT|50|21012.50|CUSTODIAN_B"""
    
    trades = parse_format2_file(file_content)
    
    assert len(trades) == 2
    assert trades[0].ticker == 'AAPL'
    assert trades[1].ticker == 'MSFT'

import csv
from datetime import datetime
from io import StringIO
from app.models import db, Trade


def parse_format1_file(file_content):
    trades = []
    reader = csv.DictReader(StringIO(file_content))
    
    for row in reader:
        try:
            trade_date = datetime.strptime(row['TradeDate'], '%Y-%m-%d').date()
            settlement_date = datetime.strptime(row['SettlementDate'], '%Y-%m-%d').date()
            
            shares = float(row['Quantity'])
            if row['TradeType'].upper() == 'SELL':
                shares = -abs(shares)
            
            trade = Trade(
                trade_date=trade_date,
                account_id=row['AccountID'],
                ticker=row['Ticker'],
                shares=shares,
                price=float(row['Price']),
                trade_type=row['TradeType'],
                settlement_date=settlement_date,
                file_format='format1'
            )
            trades.append(trade)
        except (KeyError, ValueError) as e:
            print(f"Error parsing Format 1 row: {row}. Error: {e}")
            continue
    
    return trades


def parse_format2_file(file_content):
    trades = []
    lines = file_content.strip().split('\n')
    
    for line in lines:
        if not line.strip():
            continue
            
        try:
            parts = line.split('|')
            if len(parts) != 6:
                print(f"Invalid Format 2 line (expected 6 fields): {line}")
                continue
            
            report_date_str = parts[0].strip()
            trade_date = datetime.strptime(report_date_str, '%Y%m%d').date()
            
            trade = Trade(
                trade_date=trade_date,
                account_id=parts[1].strip(),
                ticker=parts[2].strip(),
                shares=float(parts[3].strip()),
                market_value=float(parts[4].strip()),
                source_system=parts[5].strip(),
                file_format='format2'
            )
            trades.append(trade)
        except (ValueError, IndexError) as e:
            print(f"Error parsing Format 2 line: {line}. Error: {e}")
            continue
    
    return trades


def ingest_file(file_content, file_format):
    if file_format == 'format1':
        trades = parse_format1_file(file_content)
    elif file_format == 'format2':
        trades = parse_format2_file(file_content)
    else:
        raise ValueError(f"Unknown file format: {file_format}")
    
    success_count = 0
    error_count = 0
    
    for trade in trades:
        try:
            db.session.add(trade)
            success_count += 1
        except Exception as e:
            print(f"Error saving trade: {trade}. Error: {e}")
            error_count += 1
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error committing trades: {e}")
        return 0, len(trades)
    
    return success_count, error_count


def ingest_file_from_path(file_path, file_format):
    with open(file_path, 'r') as f:
        file_content = f.read()
    
    return ingest_file(file_content, file_format)


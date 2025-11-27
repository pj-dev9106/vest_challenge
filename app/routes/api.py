from flask import Blueprint, jsonify, request
from datetime import datetime
from app.models import db, Trade
from app.utils.auth import require_api_key
from app.services.alerts import send_violation_alert


api_bp = Blueprint('api', __name__, url_prefix='/api')


def parse_date(date_string):
    if not date_string:
        return None
    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except ValueError:
        return None


@api_bp.route('/blotter', methods=['GET'])
@require_api_key
def get_blotter():
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({'error': 'Date parameter is required'}), 400
    
    date_obj = parse_date(date_str)
    if not date_obj:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    trades = Trade.query.filter_by(trade_date=date_obj).all()
    
    blotter_data = []
    for trade in trades:
        item = {
            'date': trade.trade_date.isoformat(),
            'account_id': trade.account_id,
            'ticker': trade.ticker,
            'shares': float(trade.shares),
        }
        
        if trade.file_format == 'format1':
            item['price'] = float(trade.price) if trade.price else None
            item['trade_type'] = trade.trade_type
            item['settlement_date'] = trade.settlement_date.isoformat() if trade.settlement_date else None
        elif trade.file_format == 'format2':
            item['market_value'] = float(trade.market_value) if trade.market_value else None
            item['source_system'] = trade.source_system
        
        blotter_data.append(item)
    
    return jsonify({
        'date': date_str,
        'count': len(blotter_data),
        'data': blotter_data
    }), 200


@api_bp.route('/positions', methods=['GET'])
@require_api_key
def get_positions():
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({'error': 'Date parameter is required'}), 400
    
    date_obj = parse_date(date_str)
    if not date_obj:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    trades = Trade.query.filter_by(trade_date=date_obj).all()
    
    if not trades:
        return jsonify({'date': date_str, 'positions': {}}), 200
    
    account_positions = {}
    
    for trade in trades:
        account_id = trade.account_id
        ticker = trade.ticker
        
        if account_id not in account_positions:
            account_positions[account_id] = {}
        
        if trade.market_value is not None:
            market_value = float(trade.market_value)
        elif trade.price is not None and trade.shares is not None:
            market_value = float(trade.price) * float(trade.shares)
        else:
            market_value = 0
        
        if ticker in account_positions[account_id]:
            account_positions[account_id][ticker] += market_value
        else:
            account_positions[account_id][ticker] = market_value
    
    positions_result = {}
    
    for account_id, tickers in account_positions.items():
        total_value = sum(tickers.values())
        
        if total_value == 0:
            positions_result[account_id] = {ticker: 0.0 for ticker in tickers}
        else:
            positions_result[account_id] = {
                ticker: round((value / total_value) * 100, 2)
                for ticker, value in tickers.items()
            }
    
    return jsonify({
        'date': date_str,
        'positions': positions_result
    }), 200


@api_bp.route('/alarms', methods=['GET'])
@require_api_key
def get_alarms():
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({'error': 'Date parameter is required'}), 400
    
    date_obj = parse_date(date_str)
    if not date_obj:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    trades = Trade.query.filter_by(trade_date=date_obj).all()
    
    if not trades:
        return jsonify({'date': date_str, 'alarms': {}}), 200
    
    account_positions = {}
    
    for trade in trades:
        account_id = trade.account_id
        ticker = trade.ticker
        
        if account_id not in account_positions:
            account_positions[account_id] = {}
        
        if trade.market_value is not None:
            market_value = float(trade.market_value)
        elif trade.price is not None and trade.shares is not None:
            market_value = float(trade.price) * float(trade.shares)
        else:
            market_value = 0
        
        if ticker in account_positions[account_id]:
            account_positions[account_id][ticker] += market_value
        else:
            account_positions[account_id][ticker] = market_value
    
    alarms_result = {}
    violations = []
    
    for account_id, tickers in account_positions.items():
        total_value = sum(tickers.values())
        has_violation = False
        account_violations = []
        
        if total_value > 0:
            for ticker, value in tickers.items():
                percentage = (value / total_value) * 100
                if percentage > 20.0:
                    has_violation = True
                    account_violations.append({
                        'ticker': ticker,
                        'percentage': round(percentage, 2),
                        'market_value': round(value, 2)
                    })
        
        alarms_result[account_id] = has_violation
        
        if has_violation:
            violations.append({
                'account_id': account_id,
                'violations': account_violations
            })

            send_violation_alert(account_id, account_violations)
    
    return jsonify({
        'date': date_str,
        'alarms': alarms_result,
        'violations': violations
    }), 200


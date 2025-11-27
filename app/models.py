from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Trade(db.Model):
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    trade_date = db.Column(db.Date, nullable=False, index=True)
    account_id = db.Column(db.String(50), nullable=False, index=True)
    ticker = db.Column(db.String(20), nullable=False, index=True)
    shares = db.Column(db.Numeric(15, 4), nullable=False)
    
    price = db.Column(db.Numeric(15, 4), nullable=True)
    trade_type = db.Column(db.String(10), nullable=True)
    settlement_date = db.Column(db.Date, nullable=True)
    market_value = db.Column(db.Numeric(15, 2), nullable=True)
    source_system = db.Column(db.String(50), nullable=True)
    
    file_format = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_trade_date_account', 'trade_date', 'account_id'),
        db.Index('idx_trade_date_ticker', 'trade_date', 'ticker'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'trade_date': self.trade_date.isoformat() if self.trade_date else None,
            'account_id': self.account_id,
            'ticker': self.ticker,
            'shares': float(self.shares) if self.shares else 0,
            'price': float(self.price) if self.price else None,
            'trade_type': self.trade_type,
            'settlement_date': self.settlement_date.isoformat() if self.settlement_date else None,
            'market_value': float(self.market_value) if self.market_value else None,
            'source_system': self.source_system,
            'file_format': self.file_format,
        }
    
    def __repr__(self):
        return f'<Trade {self.account_id} {self.ticker} {self.shares}@{self.trade_date}>'


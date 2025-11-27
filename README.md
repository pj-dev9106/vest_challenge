# Portfolio Data Clearinghouse

A Flask-based API for ingesting and querying portfolio trade data with compliance monitoring.

## Features

- **Dual Format Ingestion**: Supports two different trade file formats
- **RESTful API**: Three endpoints for data access
- **Compliance Monitoring**: Automatic alerts for positions exceeding 20% threshold
- **Secure**: API key authentication
- **Robust Testing**: Comprehensive unit test coverage
- **Production Ready**: PostgreSQL with connection pooling

## Architecture

```
┌─────────────┐
│  Trade Files│
│ (2 formats) │
└──────┬──────┘
       │
       v
┌─────────────┐
│  Ingestion  │
│   Service   │
└──────┬──────┘
       │
       v
┌─────────────┐
│ PostgreSQL  │
│  Database   │
└──────┬──────┘
       │
       v
┌─────────────┐
│  Flask API  │
│ (3 endpoints)│
└─────────────┘
```

## Database Schema

**Table: `trades`**

- Unified schema supporting both file formats
- Indexed on `trade_date`, `account_id`, and `ticker`
- Supports negative shares for short positions/sells

## API Endpoints

All endpoints require `X-API-Key` header for authentication.

### 1. GET `/api/blotter?date=YYYY-MM-DD`

Returns all trade/position data for a given date in simplified format.

**Example Request:**

```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:5000/api/blotter?date=2025-01-15
```

**Example Response:**

```json
{
  "date": "2025-01-15",
  "count": 10,
  "data": [
    {
      "date": "2025-01-15",
      "account_id": "ACC001",
      "ticker": "AAPL",
      "shares": 100.0,
      "price": 185.5,
      "trade_type": "BUY",
      "settlement_date": "2025-01-17"
    }
  ]
}
```

### 2. GET `/api/positions?date=YYYY-MM-DD`

Returns percentage allocation by ticker for each account.

**Example Request:**

```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:5000/api/positions?date=2025-01-15
```

**Example Response:**

```json
{
  "date": "2025-01-15",
  "positions": {
    "ACC001": {
      "AAPL": 34.46,
      "MSFT": 39.03,
      "GOOGL": 26.52
    },
    "ACC002": {
      "AAPL": 34.28,
      "GOOGL": 9.89,
      "NVDA": 55.84
    }
  }
}
```

### 3. GET `/api/alarms?date=YYYY-MM-DD`

Returns compliance alarms for accounts with any position exceeding 20%.

**Example Request:**

```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:5000/api/alarms?date=2025-01-15
```

**Example Response:**

```json
{
  "date": "2025-01-15",
  "alarms": {
    "ACC001": false,
    "ACC002": true,
    "ACC003": true,
    "ACC004": true
  },
  "violations": [
    {
      "account_id": "ACC002",
      "violations": [
        {
          "ticker": "NVDA",
          "percentage": 55.84,
          "market_value": 60636.0
        }
      ]
    }
  ]
}
```

### 4. GET `/health`

Health check endpoint (no authentication required).

**Example Response:**

```json
{
  "status": "ok",
  "database": "healthy",
  "version": "1.0.0"
}
```

## Quick Start

### Prerequisites

- Python 3.11+ (tested with 3.13)
- PostgreSQL 12+ installed and running

### Setup

**1. Create PostgreSQL database:**

```bash
# Windows (using psql)
psql -U postgres
CREATE DATABASE portfolio_clearinghouse;
\q

# macOS/Linux
createdb -U postgres portfolio_clearinghouse
```

**2. Clone and set up Python environment:**

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**3. Configure database (optional):**

```bash
# Default: postgresql://postgres:postgres@localhost:5432/portfolio_clearinghouse
# To customize:

# Windows:
set DATABASE_URL=postgresql://user:password@localhost:5432/portfolio_clearinghouse
set API_KEY=your-api-key

# macOS/Linux:
export DATABASE_URL=postgresql://user:password@localhost:5432/portfolio_clearinghouse
export API_KEY=your-api-key
```

**4. Initialize and load data:**

```bash
python manage.py init_db
python manage.py load_sample
```

**5. Run the application:**

```bash
python run.py
```

The API will be available at `http://localhost:5000`

**6. Test the API:**

```bash
# Health check (no auth)
curl http://localhost:5000/health

# Blotter endpoint (requires API key)
curl -H "X-API-Key: dev-api-key-12345" \
  "http://localhost:5000/api/blotter?date=2025-01-15"
```

## Configuration

### Environment Variables

Set environment variables or edit `config.py`:

```bash
# Windows
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/portfolio_clearinghouse
set API_KEY=your-secure-api-key
set SECRET_KEY=your-secret-key
set FLASK_ENV=development

# macOS/Linux
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/portfolio_clearinghouse
export API_KEY=your-secure-api-key
export SECRET_KEY=your-secret-key
export FLASK_ENV=development
```

### Default Settings

Default values in `config.py`:

- **Database:** `postgresql://postgres:postgres@localhost:5432/portfolio_clearinghouse`
- **API Key:** `dev-api-key-12345`
- **Environment:** `development`

⚠️ **Important:** Change the default API key and secret key in production!

## Testing

Run the test suite:

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/test_api.py

# Run with verbose output
python -m pytest -v
```

All 24 tests should pass.

View coverage report:

```bash
# macOS
open htmlcov/index.html

# Windows
start htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

## Data Ingestion

### File Format 1: CSV

```csv
TradeDate,AccountID,Ticker,Quantity,Price,TradeType,SettlementDate
2025-01-15,ACC001,AAPL,100,185.50,BUY,2025-01-17
```

### File Format 2: Pipe-Delimited

```
REPORT_DATE|ACCOUNT_ID|SECURITY_TICKER|SHARES|MARKET_VALUE|SOURCE_SYSTEM
20250115|ACC001|AAPL|100|18550.00|CUSTODIAN_A
```

### Programmatic Ingestion

```python
from app import create_app
from app.services.ingestion import ingest_file_from_path

app = create_app()
with app.app_context():
    # Ingest Format 1
    success, errors = ingest_file_from_path('path/to/file.csv', 'format1')

    # Ingest Format 2
    success, errors = ingest_file_from_path('path/to/file.txt', 'format2')
```

## Management Commands

```bash
# Initialize database
python manage.py init_db

# Load sample data
python manage.py load_sample

# Clear all data
python manage.py clear_data
```

## Project Structure

```
hometask/
├── app/
│   ├── __init__.py           # Application factory
│   ├── models.py             # Database models
│   ├── routes/
│   │   ├── __init__.py
│   │   └── api.py            # API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── ingestion.py      # Data ingestion service
│   └── utils/
│       ├── __init__.py
│       └── auth.py           # Authentication utilities
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Test configuration
│   ├── test_api.py
│   ├── test_auth.py
│   ├── test_ingestion.py
│   └── test_models.py
├── sample_data/
│   ├── format1_sample.csv
│   └── format2_sample.txt
├── config.py                 # Configuration
├── run.py                    # Application entry point
├── manage.py                 # Management commands
├── requirements.txt          # Dependencies
├── pytest.ini                # Test configuration
└── README.md
```

## Security

- **API Key Authentication**: All endpoints (except `/health`) require `X-API-Key` header
- **Input Validation**: Date parameters are validated
- **SQL Injection Protection**: Using SQLAlchemy ORM
- **Error Handling**: Graceful error responses without exposing internals

## Compliance Rules

**20% Position Limit**: The system monitors and alerts when any single ticker position exceeds 20% of an account's total value.

**Calculation:**

```
Position % = (Ticker Market Value / Total Account Value) × 100
```

## Performance Considerations

- Database indexes on frequently queried columns
- Efficient aggregation queries
- Gunicorn with multiple workers for production
- Connection pooling via SQLAlchemy

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (missing API key)
- `403`: Forbidden (invalid API key)
- `404`: Not Found
- `500`: Internal Server Error

## Development

**Run in development mode:**

```bash
export FLASK_ENV=development
python run.py
```

## Production Deployment

1. **Set environment variables:**

```bash
export FLASK_ENV=production
export API_KEY=your-strong-api-key-here
export SECRET_KEY=your-strong-secret-key-here
export DATABASE_URL=postgresql://user:password@host:5432/dbname
```

2. **Install production server:**

```bash
pip install gunicorn
```

3. **Run with Gunicorn:**

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

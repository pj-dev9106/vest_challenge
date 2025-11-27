from app import create_app
from app.models import db, Trade
from app.services.ingestion import ingest_file_from_path
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_DIR = BASE_DIR / "sample_data"

def init_db():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Database initialized successfully!")


def load_sample_data():
    app = create_app()
    with app.app_context():
        format1_path = SAMPLE_DIR / "format1_sample.csv"
        format2_path = SAMPLE_DIR / "format2_sample.txt"

        success1, error1 = ingest_file_from_path(str(format1_path), 'format1')
        success2, error2 = ingest_file_from_path(str(format2_path), 'format2')

        print(f"Format1 ingestion: {success1} successes, {error1} errors")
        print(f"Format2 ingestion: {success2} successes, {error2} errors")

        print("Sample data loaded successfully!")


def clear_data():
    app = create_app()
    with app.app_context():
        confirm = input("Are you sure you want to delete all data? Type 'yes' to continue: ")
        if confirm.lower() == 'yes':
            Trade.query.delete()
            db.session.commit()
            print("All data has been cleared.")
        else:
            print("Operation cancelled.")

def ingest_file_cli(file_path: str, file_format: str):
    """
    CLI helper to ingest a single file into the database.

    Usage:
      python manage.py ingest_file /path/to/file.csv format1
      python manage.py ingest_file /path/to/file.txt format2
    """
    app = create_app()
    with app.app_context():
        success, error = ingest_file_from_path(file_path, file_format)
        print(f"Ingested {file_path} as {file_format}: {success} successes, {error} errors")



if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python manage.py [init_db|load_sample|clear_data|ingest_file]")
        sys.exit(1)

    command = sys.argv[1]

    if command == 'init_db':
        init_db()
    elif command == 'load_sample':
        load_sample_data()
    elif command == 'clear_data':
        clear_data()
    elif command == 'ingest_file':
        if len(sys.argv) != 4:
            print("Usage: python manage.py ingest_file <file_path> <format1|format2>")
            sys.exit(1)
        file_path = sys.argv[2]
        file_format = sys.argv[3]
        ingest_file_cli(file_path, file_format)
    else:
        print("Unknown command:", command)
        sys.exit(1)

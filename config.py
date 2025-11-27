import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/portfolio_clearinghouse'
    )
    API_KEY = os.environ.get('API_KEY', 'dev-api-key-12345')
    DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
    SFTP_HOST = os.environ.get('SFTP_HOST')
    SFTP_PORT = int(os.environ.get('SFTP_PORT', '22'))
    SFTP_USERNAME = os.environ.get('SFTP_USERNAME')
    SFTP_KEY_PATH = os.environ.get('SFTP_KEY_PATH')
    SFTP_REMOTE_PATH_FORMAT1 = os.environ.get('SFTP_REMOTE_PATH_FORMAT1', '/incoming/format1')
    SFTP_REMOTE_PATH_FORMAT2 = os.environ.get('SFTP_REMOTE_PATH_FORMAT2', '/incoming/format2')

class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


import os
import logging
from logging.config import dictConfig

from flask import Flask, jsonify
from app.models import db
from config import config


def create_app(config_name=None):
    app = Flask(__name__)

    dictConfig({
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            }
        },
        "root": {
            "level": os.environ.get("LOG_LEVEL", "INFO"),
            "handlers": ["wsgi"]
        },
    })
    app.logger.info("Starting Flask application")

    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app.config.from_object(config[config_name])
    
    db.init_app(app)
    
    from app.routes.api import api_bp
    app.register_blueprint(api_bp)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        try:
            db.session.execute(db.text('SELECT 1'))
            db_status = 'healthy'
        except Exception as e:
            db_status = f'unhealthy: {str(e)}'
            
        return jsonify({
            'status': 'ok' if db_status == 'healthy' else 'degraded',
            'database': db_status,
            'version': '1.0.0',
            'environment': app.config.get("ENV", os.environ.get("FLASK_ENV", "unknown"))
        }), 200 if db_status == 'healthy' else 503

    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    return app


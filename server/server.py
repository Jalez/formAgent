#!/usr/bin/env python3
"""
FormAgent Server

This module serves as the main entry point for the FormAgent server,
which provides the backend API for the FormAgent browser extension.

The server handles:
- User data storage and retrieval
- Form field mapping
- AI-assisted form interpretation (future)
"""

import os
import logging
import json
from pathlib import Path
import argparse
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from database.db_manager import DatabaseManager
from models.user_data import UserData
from services.data_service import DataService
from ai.interpreter import FormInterpreter
from api.routes import init_routes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("formAgent_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
CORS(app)  # Enable Cross-Origin Resource Sharing for the browser extension

# Initialize services
db_manager = None
data_service = None
form_interpreter = None

def initialize_services(db_path=None):
    """Initialize all services required by the server."""
    global db_manager, data_service, form_interpreter
    
    # Set database path
    if not db_path:
        db_path = os.environ.get('FORMAGENT_DB_PATH', 
                                Path.home() / '.formAgent' / 'formAgent.db')
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Initialize database manager
    db_manager = DatabaseManager(db_path)
    db_manager.initialize_database()
    
    # Initialize services
    data_service = DataService(db_manager)
    form_interpreter = FormInterpreter()
    
    # Register API routes
    api_blueprint = init_routes(data_service, form_interpreter)
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    logger.info(f"Services initialized with database at {db_path}")

# Keep these basic endpoints at root level for backward compatibility
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

@app.route('/data', methods=['GET'])
def get_user_data():
    """Retrieve user data."""
    try:
        user_id = request.args.get('user_id', 'default')
        user_data = data_service.get_user_data(user_id)
        return jsonify(user_data)
    except Exception as e:
        logger.error(f"Error getting user data: {str(e)}")
        return jsonify({"error": "Failed to retrieve user data"}), 500

@app.route('/data', methods=['POST'])
def save_user_data():
    """Save user data."""
    try:
        user_id = request.args.get('user_id', 'default')
        user_data = request.get_json()
        
        # Validate user data format
        if not isinstance(user_data, dict):
            return jsonify({"error": "Invalid data format"}), 400
        
        success = data_service.save_user_data(user_id, user_data)
        
        if success:
            return jsonify({"status": "success"})
        else:
            return jsonify({"error": "Failed to save user data"}), 500
    except Exception as e:
        logger.error(f"Error saving user data: {str(e)}")
        return jsonify({"error": "Failed to save user data"}), 500

def run_server(host, port, db_path=None):
    """Run the Flask server."""
    initialize_services(db_path)
    logger.info(f"Starting FormAgent server on {host}:{port}")
    app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FormAgent Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--db", help="Path to database file (default: ~/.formAgent/formAgent.db)")
    
    args = parser.parse_args()
    
    run_server(args.host, args.port, args.db)
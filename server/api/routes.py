"""
API Routes for FormAgent

This module defines the API routes for the FormAgent server,
separating route definitions from the main server logic.
"""

import logging
from flask import Blueprint, request, jsonify

from services.data_service import DataService
from ai.interpreter import FormInterpreter

logger = logging.getLogger(__name__)

# Create Blueprint for API routes
api_bp = Blueprint('api', __name__)

# Service instances to be injected from server.py
data_service = None
form_interpreter = None

def init_routes(ds: DataService, fi: FormInterpreter) -> Blueprint:
    """
    Initialize routes with required service instances.
    
    Args:
        ds: Data service instance
        fi: Form interpreter instance
        
    Returns:
        Blueprint: Flask blueprint with routes configured
    """
    global data_service, form_interpreter
    data_service = ds
    form_interpreter = fi
    return api_bp

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

@api_bp.route('/data', methods=['GET'])
def get_user_data():
    """Retrieve user data."""
    try:
        user_id = request.args.get('user_id', 'default')
        user_data = data_service.get_user_data(user_id)
        return jsonify(user_data)
    except Exception as e:
        logger.error(f"Error getting user data: {str(e)}")
        return jsonify({"error": "Failed to retrieve user data"}), 500

@api_bp.route('/data', methods=['POST'])
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

@api_bp.route('/interpret', methods=['POST'])
def interpret_form():
    """Use AI to interpret form structure and suggest field mappings."""
    try:
        form_data = request.get_json()
        
        # Validate form data
        if not form_data or not isinstance(form_data, dict):
            return jsonify({"error": "Invalid form data"}), 400
        
        # Use form interpreter service
        interpretation = form_interpreter.interpret_form(form_data)
        
        return jsonify(interpretation)
    except Exception as e:
        logger.error(f"Error interpreting form: {str(e)}")
        return jsonify({"error": "Failed to interpret form"}), 500

@api_bp.route('/mappings', methods=['GET'])
def get_form_mappings():
    """Retrieve form field mappings for a specific domain."""
    try:
        domain = request.args.get('domain')
        form_id = request.args.get('form_id')
        
        if not domain:
            return jsonify({"error": "Domain parameter is required"}), 400
        
        mappings = data_service.get_form_mappings(domain, form_id)
        return jsonify({"mappings": mappings})
    except Exception as e:
        logger.error(f"Error getting form mappings: {str(e)}")
        return jsonify({"error": "Failed to retrieve form mappings"}), 500

@api_bp.route('/mappings', methods=['POST'])
def save_form_mapping():
    """Save a form field mapping."""
    try:
        mapping_data = request.get_json()
        
        if not mapping_data:
            return jsonify({"error": "No mapping data provided"}), 400
        
        domain = mapping_data.get('domain')
        field_name = mapping_data.get('field_name')
        user_field = mapping_data.get('user_field')
        
        if not domain or not field_name or not user_field:
            return jsonify({"error": "Missing required fields"}), 400
        
        form_id = mapping_data.get('form_id')
        field_type = mapping_data.get('field_type')
        confidence = mapping_data.get('confidence', 1.0)
        
        success = data_service.save_form_mapping(
            domain, field_name, user_field, form_id, field_type, confidence
        )
        
        if success:
            return jsonify({"status": "success"})
        else:
            return jsonify({"error": "Failed to save mapping"}), 500
    except Exception as e:
        logger.error(f"Error saving form mapping: {str(e)}")
        return jsonify({"error": "Failed to save form mapping"}), 500

@api_bp.route('/mappings/bulk', methods=['POST'])
def save_bulk_mappings():
    """Save multiple form field mappings in bulk."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        domain = data.get('domain')
        mappings = data.get('mappings', [])
        form_id = data.get('form_id')
        
        if not domain or not mappings:
            return jsonify({"error": "Missing required fields"}), 400
        
        success = data_service.bulk_save_form_mappings(domain, mappings, form_id)
        
        if success:
            return jsonify({"status": "success"})
        else:
            return jsonify({"error": "Failed to save some mappings"}), 500
    except Exception as e:
        logger.error(f"Error saving bulk mappings: {str(e)}")
        return jsonify({"error": "Failed to save bulk mappings"}), 500
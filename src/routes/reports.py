from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, db
from src.models.tool import Tool, ToolInstance, ToolLog
from datetime import datetime

reports_bp = Blueprint('reports', __name__)

def require_admin():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    return None

@reports_bp.route('/tools', methods=['GET'])
@jwt_required()
def get_tools_report():
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    # Get query parameters for filtering
    tool_name = request.args.get('tool_name')
    status = request.args.get('status')
    user_name = request.args.get('user_name')
    
    # Build query
    query = db.session.query(
        Tool.name.label('tool_name'),
        ToolInstance.status,
        User.username,
        ToolInstance.assigned_at,
        ToolInstance.quantity
    ).join(ToolInstance, Tool.id == ToolInstance.tool_id)\
     .outerjoin(User, ToolInstance.current_user_id == User.id)
    
    # Apply filters
    if tool_name:
        query = query.filter(Tool.name.ilike(f'%{tool_name}%'))
    if status:
        query = query.filter(ToolInstance.status == status)
    if user_name:
        query = query.filter(User.username.ilike(f'%{user_name}%'))
    
    results = query.all()
    
    # Format results
    report_data = []
    for result in results:
        report_data.append({
            'tool_name': result.tool_name,
            'status': result.status,
            'username': result.username,
            'assigned_at': result.assigned_at.isoformat() if result.assigned_at else None,
            'quantity': result.quantity
        })
    
    return jsonify({'report': report_data}), 200

@reports_bp.route('/tools/pdf', methods=['GET'])
@jwt_required()
def get_tools_pdf_report():
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    # PDF generation not available in this environment
    return jsonify({'message': 'PDF generation not available in this environment'}), 200


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, db
from src.models.tool import Tool, ToolInstance, ToolLog
from datetime import datetime

returns_bp = Blueprint('returns', __name__)

def require_admin():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    return None

@returns_bp.route('', methods=['POST'])
@jwt_required()
def create_return():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('tool_instance_id'):
        return jsonify({'error': 'Tool instance ID is required'}), 400
    
    tool_instance_id = data['tool_instance_id']
    
    # Find the tool instance
    instance = ToolInstance.query.get(tool_instance_id)
    
    if not instance:
        return jsonify({'error': 'Tool instance not found'}), 404
    
    if instance.current_user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if instance.status != 'Emprestado':
        return jsonify({'error': 'Tool is not currently borrowed'}), 400
    
    # Initiate return
    instance.status = 'Em Devolução'
    
    # Log the return initiation
    log = ToolLog(
        tool_instance_id=instance.id,
        action='Devolução',
        from_user_id=current_user_id,
        quantity=1
    )
    db.session.add(log)
    
    db.session.commit()
    
    return jsonify({'message': 'Return initiated successfully'}), 201

@returns_bp.route('/<return_id>/accept', methods=['PUT'])
@jwt_required()
def accept_return(return_id):
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    # Find the tool instance
    instance = ToolInstance.query.get(return_id)
    
    if not instance:
        return jsonify({'error': 'Return not found'}), 404
    
    if instance.status != 'Em Devolução':
        return jsonify({'error': 'Return not pending acceptance'}), 400
    
    # Accept return
    instance.current_user_id = None
    instance.status = 'Disponível'
    instance.assigned_at = None
    
    # Log the return acceptance
    log = ToolLog(
        tool_instance_id=instance.id,
        action='Aceite Devolução',
        quantity=1
    )
    db.session.add(log)
    
    db.session.commit()
    
    return jsonify({'message': 'Return accepted successfully'}), 200

@returns_bp.route('/<return_id>/reject', methods=['PUT'])
@jwt_required()
def reject_return(return_id):
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    # Find the tool instance
    instance = ToolInstance.query.get(return_id)
    
    if not instance:
        return jsonify({'error': 'Return not found'}), 404
    
    if instance.status != 'Em Devolução':
        return jsonify({'error': 'Return not pending acceptance'}), 400
    
    # Reject return - return to user
    instance.status = 'Emprestado'
    
    # Log the return rejection
    log = ToolLog(
        tool_instance_id=instance.id,
        action='Recusa Devolução',
        to_user_id=instance.current_user_id,
        quantity=1
    )
    db.session.add(log)
    
    db.session.commit()
    
    return jsonify({'message': 'Return rejected successfully'}), 200

@returns_bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_returns():
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    # Get all pending returns
    pending_returns = ToolInstance.query.filter_by(
        status='Em Devolução'
    ).all()
    
    return jsonify({
        'pending_returns': [return_item.to_dict() for return_item in pending_returns]
    }), 200


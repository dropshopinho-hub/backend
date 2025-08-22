
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, db
from src.models.tool import Tool, ToolInstance, ToolLog
from datetime import datetime

assignments_bp = Blueprint('assignments', __name__)

# ...existing code...




from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, db
from src.models.tool import Tool, ToolInstance, ToolLog
from datetime import datetime

assignments_bp = Blueprint('assignments', __name__)

def require_admin():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    return None

@assignments_bp.route('', methods=['POST'])
@jwt_required()
def create_assignment():
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    data = request.get_json()
    
    if not data or not data.get('tool_id') or not data.get('user_id') or not data.get('quantity'):
        return jsonify({'error': 'Tool ID, user ID, and quantity are required'}), 400
    
    tool_id = data['tool_id']
    user_id = data['user_id']
    quantity = int(data['quantity'])
    
    # Check if tool exists
    tool = Tool.query.get(tool_id)
    if not tool:
        return jsonify({'error': 'Tool not found'}), 404
    
    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if enough available instances exist
    available_instances = ToolInstance.query.filter_by(
        tool_id=tool_id,
        status='Disponível'
    ).limit(quantity).all()
    
    if len(available_instances) < quantity:
        return jsonify({'error': 'Not enough available tools'}), 400
    
    # Assign tools to user
    for i in range(quantity):
        instance = available_instances[i]
        instance.current_user_id = user_id
        instance.status = 'Pendente de Confirmação'
        instance.assigned_at = datetime.utcnow()
        
        # Log the assignment
        log = ToolLog(
            tool_instance_id=instance.id,
            action='Atribuição',
            to_user_id=user_id,
            quantity=1
        )
        db.session.add(log)
    
    db.session.commit()
    
    return jsonify({'message': 'Assignment created successfully'}), 201

@assignments_bp.route('/<assignment_id>/confirm', methods=['PUT'])
@jwt_required()
def confirm_assignment(assignment_id):
    current_user_id = get_jwt_identity()
    
    # Find the tool instance
    instance = ToolInstance.query.get(assignment_id)
    
    if not instance:
        return jsonify({'error': 'Assignment not found'}), 404
    
    if instance.current_user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if instance.status != 'Pendente de Confirmação':
        return jsonify({'error': 'Assignment not pending confirmation'}), 400
    
    # Confirm assignment
    instance.status = 'Emprestado'
    
    # Log the confirmation
    log = ToolLog(
        tool_instance_id=instance.id,
        action='Confirmação',
        to_user_id=current_user_id,
        quantity=1
    )
    db.session.add(log)
    
    db.session.commit()
    
    return jsonify({'message': 'Assignment confirmed successfully'}), 200


@assignments_bp.route('/user/<user_id>', methods=['GET'])
@jwt_required()
def get_user_assignments(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Users can only see their own assignments, admins can see any user's assignments
    if current_user.role != 'admin' and current_user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get pending assignments
    pending_assignments = ToolInstance.query.filter_by(
        current_user_id=user_id,
        status='Pendente de Confirmação'
    ).all()
    
    # Get confirmed assignments
    confirmed_assignments = ToolInstance.query.filter_by(
        current_user_id=user_id,
        status='Emprestado'
    ).all()
    
    return jsonify({
        'pending': [assignment.to_dict() for assignment in pending_assignments],
        'confirmed': [assignment.to_dict() for assignment in confirmed_assignments]
    }), 200


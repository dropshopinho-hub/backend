from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, db
from src.models.tool import Tool, ToolInstance, ToolLog
from sqlalchemy import func

tools_bp = Blueprint('tools', __name__)

def require_admin():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    return None

@tools_bp.route('', methods=['POST'])
@jwt_required()
def create_tool():
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('quantity'):
        return jsonify({'error': 'Name and quantity are required'}), 400
    
    name = data['name']
    quantity = int(data['quantity'])
    
    # Create new tool
    tool = Tool(name=name, total_quantity=quantity)
    db.session.add(tool)
    db.session.flush()  # To get the tool ID
    
    # Create tool instances
    for _ in range(quantity):
        instance = ToolInstance(tool_id=tool.id, status='Disponível')
        db.session.add(instance)
    
    db.session.commit()
    
    return jsonify({'message': 'Tool created successfully', 'tool': tool.to_dict()}), 201

@tools_bp.route('', methods=['GET'])
@jwt_required()
def get_tools():
    # Get all tools with aggregated information
    tools_data = []
    
    # Query to get tool information with status counts
    tools = Tool.query.all()
    
    for tool in tools:
        # Get status counts for this tool
        status_counts = db.session.query(
            ToolInstance.status,
            ToolInstance.current_user_id,
            User.username,
            func.sum(ToolInstance.quantity).label('total_quantity'),
            func.min(ToolInstance.assigned_at).label('assigned_at')
        ).outerjoin(User, ToolInstance.current_user_id == User.id)\
         .filter(ToolInstance.tool_id == tool.id)\
         .group_by(ToolInstance.status, ToolInstance.current_user_id, User.username)\
         .all()
        
        # Group by status and user
        grouped_data = {}
        for status, user_id, username, quantity, assigned_at in status_counts:
            key = f"{status}_{user_id or 'none'}"
            if key not in grouped_data:
                grouped_data[key] = {
                    'tool_id': tool.id,
                    'tool_name': tool.name,
                    'status': status,
                    'user_id': user_id,
                    'username': username,
                    'quantity': 0,
                    'assigned_at': assigned_at.isoformat() if assigned_at else None
                }
            grouped_data[key]['quantity'] += quantity
        
        tools_data.extend(grouped_data.values())
    
    return jsonify({'tools': tools_data}), 200

@tools_bp.route('/<tool_id>', methods=['GET'])
@jwt_required()
def get_tool(tool_id):
    tool = Tool.query.get(tool_id)
    
    if not tool:
        return jsonify({'error': 'Tool not found'}), 404
    
    return jsonify({'tool': tool.to_dict()}), 200

@tools_bp.route('/<tool_id>', methods=['PUT'])
@jwt_required()
def update_tool(tool_id):
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    tool = Tool.query.get(tool_id)
    
    if not tool:
        return jsonify({'error': 'Tool not found'}), 404
    
    data = request.get_json()
    
    if data.get('name'):
        tool.name = data['name']

    if data.get('quantity'):
        new_quantity = int(data['quantity'])
        current_instances = ToolInstance.query.filter_by(tool_id=tool.id).count()

        if new_quantity > current_instances:
            # Add more instances
            for _ in range(new_quantity - current_instances):
                instance = ToolInstance(tool_id=tool.id, status='Disponível')
                db.session.add(instance)
        elif new_quantity < current_instances:
            # Remove instances (only available ones)
            available_instances = ToolInstance.query.filter_by(
                tool_id=tool.id,
                status='Disponível'
            ).limit(current_instances - new_quantity).all()
            for instance in available_instances:
                db.session.delete(instance)

        tool.total_quantity = new_quantity


    db.session.commit()

    return jsonify({'message': 'Tool updated successfully', 'tool': tool.to_dict()}), 200

@tools_bp.route('/<tool_id>', methods=['DELETE'])
@jwt_required()
def delete_tool(tool_id):
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    tool = Tool.query.get(tool_id)
    
    if not tool:
        return jsonify({'error': 'Tool not found'}), 404
    
    # Check if any instances are not available
    non_available_instances = ToolInstance.query.filter(
        ToolInstance.tool_id == tool.id,
        ToolInstance.status != 'Disponível'
    ).count()
    
    if non_available_instances > 0:
        return jsonify({'error': 'Cannot delete tool with non-available instances'}), 400
    
    # Delete all instances and logs
    ToolInstance.query.filter_by(tool_id=tool.id).delete()
    db.session.delete(tool)
    db.session.commit()
    
    return jsonify({'message': 'Tool deleted successfully'}), 200

@tools_bp.route('/recusadas', methods=['GET'])
@jwt_required()
def get_recusadas():
    # Lista todas as ferramentas e quantidades com status 'Recusada'
    recusadas = ToolInstance.query.filter_by(status='Recusada').all()
    result = []
    for ti in recusadas:
        result.append({
            'tool_name': ti.tool.name if ti.tool else None,
            'quantity': ti.quantity
        })
    return jsonify({'recusadas': result}), 200


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src import supabase
from src.models.tool import Tool, ToolInstance, ToolLog
from datetime import datetime

assignments_bp = Blueprint('assignments', __name__)

def require_admin():
    current_user_id = get_jwt_identity()
    response = supabase.table("users").select("*").eq("id", current_user_id).execute()
    user = response.data[0] if response.data else None
    if not user or user.get("role") != "admin":
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
    tool_resp = supabase.table("tool").select("*").eq("id", tool_id).execute()
    tool = tool_resp.data[0] if tool_resp.data else None
    if not tool:
        return jsonify({'error': 'Tool not found'}), 404

    # Check if user exists
    user_resp = supabase.table("users").select("*").eq("id", user_id).execute()
    user = user_resp.data[0] if user_resp.data else None
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Busca instâncias disponíveis (cada unidade = 1 linha)
    instances_resp = supabase.table("tool_instance").select("*").eq("tool_id", tool_id).eq("status", "Disponível").eq("quantity", 1).limit(quantity).execute()
    available_instances = instances_resp.data
    if len(available_instances) < quantity:
        return jsonify({'error': 'Not enough available tools'}), 400

    # Atribui as ferramentas ao usuário (uma por linha)
    for i in range(quantity):
        instance = available_instances[i]
        update_data = {
            "current_user_id": user_id,
            "status": "Pendente de Confirmação",
            "assigned_at": datetime.utcnow().isoformat()
        }
        supabase.table("tool_instance").update(update_data).eq("id", instance["id"]).execute()

        # Log da atribuição
        log = ToolLog(
            tool_instance_id=instance["id"],
            action='Atribuição',
            to_user_id=user_id,
            quantity=1
        )
        supabase.table("tool_log").insert(log.to_dict()).execute()

    return jsonify({'message': 'Assignment created successfully'}), 201

@assignments_bp.route('/<assignment_id>/confirm', methods=['PUT'])
@jwt_required()
def confirm_assignment(assignment_id):
    current_user_id = get_jwt_identity()

    # Busca a instância da ferramenta
    instance_resp = supabase.table("tool_instance").select("*").eq("id", assignment_id).execute()
    instance = instance_resp.data[0] if instance_resp.data else None

    if not instance:
        return jsonify({'error': 'Assignment not found'}), 404

    if instance.get("current_user_id") != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    if instance.get("status") != 'Pendente de Confirmação':
        return jsonify({'error': 'Assignment not pending confirmation'}), 400

    # Confirma a atribuição
    supabase.table("tool_instance").update({"status": "Emprestado"}).eq("id", assignment_id).execute()

    # Log da confirmação
    log = ToolLog(
        tool_instance_id=assignment_id,
        action='Confirmação',
        to_user_id=current_user_id,
        quantity=1
    )
    supabase.table("tool_log").insert(log.to_dict()).execute()

    return jsonify({'message': 'Assignment confirmed successfully'}), 200

@assignments_bp.route('/user/<user_id>', methods=['GET'])
@jwt_required()
def get_user_assignments(user_id):
    current_user_id = get_jwt_identity()
    user_resp = supabase.table("users").select("*").eq("id", current_user_id).execute()
    current_user = user_resp.data[0] if user_resp.data else None

    # Usuários só podem ver suas próprias atribuições, admins veem todas
    if current_user.get("role") != 'admin' and current_user_id != user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Atribuições pendentes
    pending_resp = supabase.table("tool_instance").select("*").eq("current_user_id", user_id).eq("status", "Pendente de Confirmação").execute()
    pending_assignments = pending_resp.data
    
    # Buscar nome da ferramenta separadamente para cada atribuição pendente
    for assignment in pending_assignments:
        if assignment.get('tool_id'):
            tool_resp = supabase.table("tool").select("name").eq("id", assignment['tool_id']).execute()
            if tool_resp.data:
                assignment['name'] = tool_resp.data[0]['name']

    # Atribuições confirmadas
    confirmed_resp = supabase.table("tool_instance").select("*").eq("current_user_id", user_id).eq("status", "Emprestado").execute()
    confirmed_assignments = confirmed_resp.data
    
    # Buscar nome da ferramenta separadamente para cada atribuição confirmada
    for assignment in confirmed_assignments:
        if assignment.get('tool_id'):
            tool_resp = supabase.table("tool").select("name").eq("id", assignment['tool_id']).execute()
            if tool_resp.data:
                assignment['name'] = tool_resp.data[0]['name']

    return jsonify({
        'pending': pending_assignments,
        'confirmed': confirmed_assignments
    }), 200
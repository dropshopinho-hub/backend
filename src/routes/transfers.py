from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import supabase
from src.models.tool import ToolLog
from datetime import datetime

transfers_bp = Blueprint('transfers', __name__)

# ------------------------------
# Iniciar transferência
# ------------------------------
@transfers_bp.route('', methods=['POST'])
@jwt_required()
def create_transfer():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('tool_instance_id') or not data.get('to_user_id'):
        return jsonify({'error': 'Tool instance ID and target user ID are required'}), 400
    
    tool_instance_id = data['tool_instance_id']
    to_user_id = data['to_user_id']
    
    if to_user_id == current_user_id:
        return jsonify({'error': 'Cannot transfer tool to yourself'}), 400
    
    # Buscar a instância da ferramenta
    instance_resp = supabase.table("tool_instance").select("*").eq("id", tool_instance_id).execute()
    instance = instance_resp.data[0] if instance_resp.data else None
    
    if not instance:
        return jsonify({'error': 'Tool instance not found'}), 404
    
    if instance.get('current_user_id') != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if instance.get('status') != 'Emprestado':
        return jsonify({'error': 'Tool is not currently borrowed'}), 400
    
    # Verificar se o usuário destino existe
    target_user_resp = supabase.table("users").select("*").eq("id", to_user_id).execute()
    target_user = target_user_resp.data[0] if target_user_resp.data else None
    if not target_user:
        return jsonify({'error': 'Target user not found'}), 404
    
    # Iniciar a transferência
    supabase.table("tool_instance").update({
        "status": "Aguardando Confirmação de Transferência",
        "transferred_to_user_id": to_user_id,
        "transfer_initiated_at": datetime.utcnow().isoformat()
    }).eq("id", tool_instance_id).execute()
    
    # Registrar log
    log = ToolLog(
        tool_instance_id=tool_instance_id,
        action='Transferência',
        from_user_id=current_user_id,
        to_user_id=to_user_id,
        quantity=1
    )
    supabase.table("tool_log").insert(log.to_dict()).execute()
    
    return jsonify({'message': 'Transfer initiated successfully'}), 201

# ------------------------------
# Confirmar transferência
# ------------------------------
@transfers_bp.route('/<transfer_id>/confirm', methods=['PUT'])
@jwt_required()
def confirm_transfer(transfer_id):
    current_user_id = get_jwt_identity()
    
    instance_resp = supabase.table("tool_instance").select("*").eq("id", transfer_id).execute()
    instance = instance_resp.data[0] if instance_resp.data else None
    
    if not instance:
        return jsonify({'error': 'Transfer not found'}), 404
    
    if instance.get('transferred_to_user_id') != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if instance.get('status') != 'Aguardando Confirmação de Transferência':
        return jsonify({'error': 'Transfer not pending confirmation'}), 400
    
    # Confirmar
    supabase.table("tool_instance").update({
        "current_user_id": current_user_id,
        "status": "Emprestado",
        "transferred_to_user_id": None,
        "transfer_initiated_at": None,
        "assigned_at": datetime.utcnow().isoformat()
    }).eq("id", transfer_id).execute()
    
    log = ToolLog(
        tool_instance_id=transfer_id,
        action='Confirmação de Transferência',
        to_user_id=current_user_id,
        quantity=1
    )
    supabase.table("tool_log").insert(log.to_dict()).execute()
    
    return jsonify({'message': 'Transfer confirmed successfully'}), 200

# ------------------------------
# Rejeitar transferência
# ------------------------------
@transfers_bp.route('/<transfer_id>/reject', methods=['PUT'])
@jwt_required()
def reject_transfer(transfer_id):
    current_user_id = get_jwt_identity()
    
    instance_resp = supabase.table("tool_instance").select("*").eq("id", transfer_id).execute()
    instance = instance_resp.data[0] if instance_resp.data else None
    
    if not instance:
        return jsonify({'error': 'Transfer not found'}), 404
    
    if instance.get('transferred_to_user_id') != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if instance.get('status') != 'Aguardando Confirmação de Transferência':
        return jsonify({'error': 'Transfer not pending confirmation'}), 400
    
    # Buscar o log de transferência para pegar o usuário original
    log_resp = supabase.table("tool_log").select("*").eq("tool_instance_id", transfer_id).eq("action", "Transferência").order("timestamp", desc=True).limit(1).execute()
    transfer_log = log_resp.data[0] if log_resp.data else None
    original_user_id = transfer_log['from_user_id'] if transfer_log else None
    if not original_user_id:
        return jsonify({'error': 'Original user not found for this transfer'}), 400
    
    # Rejeitar
    supabase.table("tool_instance").update({
        "current_user_id": original_user_id,
        "status": "Emprestado",
        "transferred_to_user_id": None,
        "transfer_initiated_at": None
    }).eq("id", transfer_id).execute()
    
    log = ToolLog(
        tool_instance_id=transfer_id,
        action='Recusa de Transferência',
        from_user_id=current_user_id,
        to_user_id=original_user_id,
        quantity=1
    )
    supabase.table("tool_log").insert(log.to_dict()).execute()
    
    return jsonify({'message': 'Transfer rejected successfully'}), 200

# ------------------------------
# Listar transferências pendentes
# ------------------------------
@transfers_bp.route('/pending/<user_id>', methods=['GET'])
@jwt_required()
def get_pending_transfers(user_id):
    current_user_id = get_jwt_identity()
    user_resp = supabase.table("users").select("*").eq("id", current_user_id).execute()
    current_user = user_resp.data[0] if user_resp.data else None
    
    # Somente admin pode ver de outros usuários
    if current_user.get("role") != 'admin' and str(current_user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    pending_resp = supabase.table("tool_instance").select("*").eq("transferred_to_user_id", user_id).eq("status", "Aguardando Confirmação de Transferência").execute()
    pending_transfers = pending_resp.data if pending_resp.data else []
    
    return jsonify({
        'pending_transfers': pending_transfers
    }), 200
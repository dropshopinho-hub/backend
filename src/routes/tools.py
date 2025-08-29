from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import supabase
from src.models.tool import ToolLog
from datetime import datetime

returns_bp = Blueprint('returns', __name__)

def require_admin():
    current_user_id = get_jwt_identity()
    response = supabase.table("users").select("*").eq("id", current_user_id).execute()
    user = response.data[0] if response.data else None
    if not user or user.get("role") != "admin":
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
    instance_resp = supabase.table("tool_instance").select("*").eq("id", tool_instance_id).execute()
    instance = instance_resp.data[0] if instance_resp.data else None
    
    if not instance:
        return jsonify({'error': 'Tool instance not found'}), 404
    
    if instance.get('current_user_id') != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if instance.get('status') != 'Emprestado':
        return jsonify({'error': 'Tool is not currently borrowed'}), 400
    
    # Initiate return
    supabase.table("tool_instance").update({"status": "Em Devolução"}).eq("id", tool_instance_id).execute()
    
    # Log the return initiation
    log = ToolLog(
        tool_instance_id=tool_instance_id,
        action='Devolução',
        from_user_id=current_user_id,
        quantity=1
    )
    supabase.table("tool_log").insert(log.to_dict()).execute()
    
    return jsonify({'message': 'Return initiated successfully'}), 201

@returns_bp.route('/<return_id>/accept', methods=['PUT'])
@jwt_required()
def accept_return(return_id):
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    # Find the tool instance
    instance_resp = supabase.table("tool_instance").select("*").eq("id", return_id).execute()
    instance = instance_resp.data[0] if instance_resp.data else None
    
    if not instance:
        return jsonify({'error': 'Return not found'}), 404
    
    if instance.get('status') != 'Em Devolução':
        return jsonify({'error': 'Return not pending acceptance'}), 400
    
    # Accept return
    supabase.table("tool_instance").update({
        "current_user_id": None,
        "status": "Disponível",
        "assigned_at": None
    }).eq("id", return_id).execute()
    
    # Log the return acceptance
    log = ToolLog(
        tool_instance_id=return_id,
        action='Aceite Devolução',
        quantity=1
    )
    supabase.table("tool_log").insert(log.to_dict()).execute()
    
    return jsonify({'message': 'Return accepted successfully'}), 200

@returns_bp.route('/<return_id>/reject', methods=['PUT'])
@jwt_required()
def reject_return(return_id):
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    # Find the tool instance
    instance_resp = supabase.table("tool_instance").select("*").eq("id", return_id).execute()
    instance = instance_resp.data[0] if instance_resp.data else None
    
    if not instance:
        return jsonify({'error': 'Return not found'}), 404
    
    if instance.get('status') != 'Em Devolução':
        return jsonify({'error': 'Return not pending acceptance'}), 400
    
    # Reject return - return to user
    supabase.table("tool_instance").update({"status": "Emprestado"}).eq("id", return_id).execute()
    
    # Log the return rejection
    log = ToolLog(
        tool_instance_id=return_id,
        action='Recusa Devolução',
        to_user_id=instance.get('current_user_id'),
        quantity=1
    )
    supabase.table("tool_log").insert(log.to_dict()).execute()
    
    return jsonify({'message': 'Return rejected successfully'}), 200

@returns_bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_returns():
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    # Get all pending returns
    pending_resp = supabase.table("tool_instance").select("*").eq("status", "Em Devolução").execute()
    pending_returns = pending_resp.data if pending_resp.data else []
    
    return jsonify({
        'pending_returns': pending_returns
    }), 200
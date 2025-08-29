from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import supabase
from datetime import datetime

reports_bp = Blueprint('reports', __name__)

def require_admin():
    current_user_id = get_jwt_identity()
    response = supabase.table("users").select("*").eq("id", current_user_id).execute()
    user = response.data[0] if response.data else None
    if not user or user.get("role") != "admin":
        return jsonify({'error': 'Admin access required'}), 403
    return None

@reports_bp.route('/tools', methods=['GET'])
@jwt_required()
def get_tools_report():
    admin_check = require_admin()
    if admin_check:
        return admin_check

    tool_name = request.args.get('tool_name')
    status = request.args.get('status')
    user_name = request.args.get('user_name')

    # Busca todas as instâncias de ferramentas
    instances_resp = supabase.table("tool_instance").select("*").execute()
    instances = instances_resp.data if instances_resp.data else []

    # Busca todas as ferramentas
    tools_resp = supabase.table("tool").select("*").execute()
    tools = {tool['id']: tool for tool in tools_resp.data} if tools_resp.data else {}

    # Busca todos os usuários
    users_resp = supabase.table("users").select("*").execute()
    users = {user['id']: user for user in users_resp.data} if users_resp.data else {}

    report_data = []
    for instance in instances:
        tool = tools.get(instance.get('tool_id'))
        user = users.get(instance.get('current_user_id'))

        # Filtros
        if tool_name and (not tool or tool_name.lower() not in tool['name'].lower()):
            continue
        if status and instance.get('status') != status:
            continue
        if user_name and (not user or user_name.lower() not in user['username'].lower()):
            continue

        report_data.append({
            'tool_name': tool['name'] if tool else None,
            'status': instance.get('status'),
            'username': user['username'] if user else None,
            'assigned_at': instance.get('assigned_at'),
            'quantity': instance.get('quantity', 1)
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
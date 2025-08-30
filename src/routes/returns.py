from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src import supabase
from datetime import datetime
from src.models.tool import ToolLog

returns_bp = Blueprint('returns', __name__)

def require_admin():
    current_user_id = get_jwt_identity()
    response = supabase.table("users").select("*").eq("id", current_user_id).execute()
    user = response.data[0] if response.data else None
    if not user or user.get("role") != "admin":
        return jsonify({'error': 'Admin access required'}), 403
    return None

@returns_bp.route('/tools/return/<tool_instance_id>', methods=['POST'])
@jwt_required()
def return_tool(tool_instance_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Buscar a instância da ferramenta
        instance_resp = supabase.table("tool_instance").select("*").eq("id", tool_instance_id).execute()
        instance = instance_resp.data[0] if instance_resp.data else None
        
        if not instance:
            return jsonify({'error': 'Tool instance not found'}), 404
        
        # Verificar se o usuário atual é o dono da ferramenta
        if instance.get('current_user_id') != current_user_id:
            return jsonify({'error': 'Unauthorized - you do not own this tool'}), 403
        
        # Verificar se a ferramenta está emprestada
        if instance.get('status') != 'Emprestado':
            return jsonify({'error': 'Tool is not currently borrowed'}), 400
        
        # Atualizar status para disponível
        supabase.table("tool_instance").update({
            'status': 'Disponível',
            'current_user_id': None,
            'assigned_at': None
        }).eq("id", tool_instance_id).execute()
        
        # Registrar log da devolução (opcional - não falha se der erro)
        try:
            from datetime import datetime
            log_data = {
                'tool_instance_id': tool_instance_id,
                'action': 'Devolução',
                'from_user_id': current_user_id,
                'to_user_id': None,
                'timestamp': datetime.now().isoformat()
            }
            supabase.table("tool_log").insert(log_data).execute()
        except Exception as log_error:
            print(f"Warning: Could not log return action: {log_error}")
        
        return jsonify({'message': 'Tool returned successfully'}), 200
        
    except Exception as e:
        print(f"Error in return_tool: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@returns_bp.route('/tools', methods=['GET'])
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

@returns_bp.route('/tools/pdf', methods=['GET'])
@jwt_required()
def get_tools_pdf_report():
    admin_check = require_admin()
    if admin_check:
        return admin_check

    # PDF generation not available in this environment
    return jsonify({'message': 'PDF generation not available in this environment'}), 200
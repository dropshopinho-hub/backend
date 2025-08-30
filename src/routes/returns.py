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
        
        # Atualizar status para pendente de devolução
        supabase.table("tool_instance").update({
            'status': 'Pendente de Devolução'
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
        
        return jsonify({'message': 'Return request submitted successfully. Waiting for admin approval.'}), 200
        
    except Exception as e:
        print(f"Error in return_tool: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Endpoint para listar devoluções pendentes (admin)
@returns_bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_returns():
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    try:
        # Buscar todas as ferramentas pendentes de devolução
        pending_resp = supabase.table("tool_instance").select("*").eq("status", "Pendente de Devolução").execute()
        pending_returns = pending_resp.data
        
        # Para cada ferramenta, buscar nome da ferramenta e nome do usuário
        for item in pending_returns:
            # Buscar nome da ferramenta
            if item.get('tool_id'):
                tool_resp = supabase.table("tool").select("name").eq("id", item['tool_id']).execute()
                if tool_resp.data:
                    item['tool_name'] = tool_resp.data[0]['name']
            
            # Buscar nome do usuário
            if item.get('current_user_id'):
                user_resp = supabase.table("users").select("name").eq("id", item['current_user_id']).execute()
                if user_resp.data:
                    item['user_name'] = user_resp.data[0]['name']
        
        return jsonify(pending_returns), 200
        
    except Exception as e:
        print(f"Error getting pending returns: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Endpoint para aceitar devolução (admin)
@returns_bp.route('/approve/<tool_instance_id>', methods=['POST'])
@jwt_required()
def approve_return(tool_instance_id):
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    try:
        current_user_id = get_jwt_identity()
        
        # Buscar a instância da ferramenta
        instance_resp = supabase.table("tool_instance").select("*").eq("id", tool_instance_id).execute()
        instance = instance_resp.data[0] if instance_resp.data else None
        
        if not instance:
            return jsonify({'error': 'Tool instance not found'}), 404
        
        if instance.get('status') != 'Pendente de Devolução':
            return jsonify({'error': 'Tool is not pending return'}), 400
        
        # Aprovar devolução - tornar disponível
        supabase.table("tool_instance").update({
            'status': 'Disponível',
            'current_user_id': None,
            'assigned_at': None
        }).eq("id", tool_instance_id).execute()
        
        # Log da aprovação
        try:
            from datetime import datetime
            log_data = {
                'tool_instance_id': tool_instance_id,
                'action': 'Devolução Aprovada',
                'from_user_id': instance.get('current_user_id'),
                'to_user_id': current_user_id,
                'timestamp': datetime.now().isoformat()
            }
            supabase.table("tool_log").insert(log_data).execute()
        except Exception as log_error:
            print(f"Warning: Could not log approval: {log_error}")
        
        return jsonify({'message': 'Return approved successfully'}), 200
        
    except Exception as e:
        print(f"Error approving return: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Endpoint para recusar devolução (admin)
@returns_bp.route('/reject/<tool_instance_id>', methods=['POST'])
@jwt_required()
def reject_return(tool_instance_id):
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    try:
        current_user_id = get_jwt_identity()
        
        # Buscar a instância da ferramenta
        instance_resp = supabase.table("tool_instance").select("*").eq("id", tool_instance_id).execute()
        instance = instance_resp.data[0] if instance_resp.data else None
        
        if not instance:
            return jsonify({'error': 'Tool instance not found'}), 404
        
        if instance.get('status') != 'Pendente de Devolução':
            return jsonify({'error': 'Tool is not pending return'}), 400
        
        # Recusar devolução - volta para emprestado
        supabase.table("tool_instance").update({
            'status': 'Emprestado'
        }).eq("id", tool_instance_id).execute()
        
        # Log da rejeição
        try:
            from datetime import datetime
            log_data = {
                'tool_instance_id': tool_instance_id,
                'action': 'Devolução Rejeitada',
                'from_user_id': instance.get('current_user_id'),
                'to_user_id': current_user_id,
                'timestamp': datetime.now().isoformat()
            }
            supabase.table("tool_log").insert(log_data).execute()
        except Exception as log_error:
            print(f"Warning: Could not log rejection: {log_error}")
        
        return jsonify({'message': 'Return rejected successfully'}), 200
        
    except Exception as e:
        print(f"Error rejecting return: {e}")
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
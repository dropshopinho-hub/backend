from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src import supabase
from datetime import datetime

tools_bp = Blueprint('tools', __name__)

def require_admin():
    current_user_id = get_jwt_identity()
    response = supabase.table("users").select("*").eq("id", current_user_id).execute()
    user = response.data[0] if response.data else None
    if not user or user.get("role") != "admin":
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
        return jsonify({'error': 'Nome e quantidade são obrigatórios'}), 400

    nome = data['name']
    quantidade = data['quantity']

    # Cria a ferramenta na tabela tool
    response = supabase.table("tool").insert({
        "name": nome,
        "quantity": quantidade,
        "total_quantity": quantidade  # Campo obrigatório preenchido
    }).execute()

    if not response.data:
        return jsonify({'error': 'Erro ao cadastrar ferramenta'}), 400

    tool_id = response.data[0]["id"]

    # Cria uma instância para cada unidade (cada linha = 1 unidade)
    for _ in range(int(quantidade)):
        instance_response = supabase.table("tool_instance").insert({
            "tool_id": tool_id,
            "status": "Disponível",
            "quantity": 1
        }).execute()
        if not instance_response.data:
            return jsonify({'error': 'Erro ao criar instância da ferramenta'}), 400

    return jsonify({'message': 'Ferramenta cadastrada com sucesso'}), 201

@tools_bp.route('', methods=['GET'])
@jwt_required()
def get_tools():
    admin_check = require_admin()
    if admin_check:
        return admin_check

    # Busca ferramentas da tabela principal
    tools_response = supabase.table("tool").select("*").execute()
    tools_data = tools_response.data if tools_response.data else []
    
    # Para cada ferramenta, conta as instâncias por status
    formatted_tools = []
    for tool in tools_data:
        instances_response = supabase.table("tool_instance").select("*").eq("tool_id", tool['id']).execute()
        instances = instances_response.data if instances_response.data else []
        
        # Conta instâncias por status
        status_count = {}
        for instance in instances:
            status = instance['status']
            status_count[status] = status_count.get(status, 0) + 1
        
        # Determina status principal da ferramenta
        if status_count.get('Disponível', 0) > 0:
            main_status = 'Disponível'
        elif status_count.get('Emprestado', 0) > 0:
            main_status = 'Emprestado'
        else:
            main_status = 'Indisponível'
        
        formatted_tools.append({
            'tool_id': tool['id'],
            'name': tool['name'],
            'total_quantity': tool.get('total_quantity', len(instances)),
            'available_quantity': status_count.get('Disponível', 0),
            'borrowed_quantity': status_count.get('Emprestado', 0),
            'status': main_status,
            'instances': len(instances)
        })
    
    return jsonify({'tools': formatted_tools}), 200

@tools_bp.route('/instances', methods=['GET'])
@jwt_required()
def get_tool_instances():
    # Endpoint para atribuições - retorna instâncias individuais
    response = supabase.table("tool_instance").select("""
        *,
        tool:tool_id (
            id,
            name
        )
    """).execute()
    
    instances = response.data if response.data else []
    
    formatted_instances = []
    for instance in instances:
        if instance.get('tool'):
            formatted_instances.append({
                'id': instance['id'],
                'tool_id': instance['tool_id'],
                'tool_name': instance['tool']['name'],
                'status': instance['status'],
                'quantity': instance['quantity'],
                'current_user_id': instance.get('current_user_id'),
                'assigned_at': instance.get('assigned_at')
            })
    
    return jsonify({'tools': formatted_instances}), 200
# Adicione outros endpoints conforme necessário
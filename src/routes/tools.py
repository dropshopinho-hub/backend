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

    response = supabase.table("tool").select("*").execute()
    tools = response.data if response.data else []
    return jsonify({'tools': tools}), 200

@tools_bp.route('/instances', methods=['GET'])
@jwt_required()
def get_available_tool_instances():
    status = request.args.get('status', None)
    query = supabase.table("tool_instance").select("*")
    if status:
        query = query.eq("status", status)
    response = query.execute()
    instances = response.data if response.data else []
    return jsonify(instances), 200
# Adicione outros endpoints conforme necessário
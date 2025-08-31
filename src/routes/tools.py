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
    
    # Para cada ferramenta, busca instâncias com informações de usuário
    formatted_tools = []
    for tool in tools_data:
        instances_response = supabase.table("tool_instance").select("*").eq("tool_id", tool['id']).execute()
        instances = instances_response.data if instances_response.data else []
        
        # Se não há instâncias, cria instâncias automaticamente
        if not instances:
            quantity = tool.get('quantity', tool.get('total_quantity', 1))
            for _ in range(int(quantity)):
                instance_response = supabase.table("tool_instance").insert({
                    "tool_id": tool['id'],
                    "status": "Disponível",
                    "quantity": 1
                }).execute()
                if instance_response.data:
                    instances.append(instance_response.data[0])
        
        # Conta instâncias por status
        status_count = {}
        for instance in instances:
            status = instance['status']
            status_count[status] = status_count.get(status, 0) + 1
        
        # Se ainda não há instâncias, mostra a ferramenta como disponível
        if not instances:
            formatted_tools.append({
                'tool_id': tool['id'],
                'name': tool['name'],
                'quantity': tool.get('quantity', tool.get('total_quantity', 1)),
                'total_quantity': tool.get('quantity', tool.get('total_quantity', 1)),
                'available_quantity': tool.get('quantity', tool.get('total_quantity', 1)),
                'borrowed_quantity': 0,
                'status': 'Disponível',
                'username': None,
                'assigned_at': None,
                'current_user_id': None,
                'instance_id': None
            })
        else:
            # Para cada instância, cria uma entrada na lista
            for instance in instances:
                username = None
                if instance.get('current_user_id'):
                    # Busca o nome do usuário separadamente
                    user_response = supabase.table("users").select("username").eq("id", instance['current_user_id']).execute()
                    if user_response.data:
                        username = user_response.data[0]['username']
                
                formatted_tools.append({
                    'tool_id': tool['id'],
                    'name': tool['name'],
                    'quantity': instance.get('quantity', 1),
                    'total_quantity': tool.get('total_quantity', len(instances)),
                    'available_quantity': status_count.get('Disponível', 0),
                    'borrowed_quantity': status_count.get('Emprestado', 0),
                    'status': instance['status'],
                    'username': username,
                    'assigned_at': instance.get('assigned_at'),
                    'current_user_id': instance.get('current_user_id'),
                    'instance_id': instance['id']
                })
    
    # Agrupa ferramentas por nome e usuário
    grouped_tools = {}
    for tool in formatted_tools:
        key = f"{tool['name']}_{tool['username'] or 'sem_usuario'}"
        
        if key in grouped_tools:
            # Soma as quantidades
            grouped_tools[key]['quantity'] += tool['quantity']
            # Mantém a data mais recente
            if tool['assigned_at'] and (not grouped_tools[key]['assigned_at'] or tool['assigned_at'] > grouped_tools[key]['assigned_at']):
                grouped_tools[key]['assigned_at'] = tool['assigned_at']
        else:
            grouped_tools[key] = tool.copy()
    
    # Converte de volta para lista
    final_tools = list(grouped_tools.values())
    
    return jsonify({'tools': final_tools}), 200

@tools_bp.route('/instances', methods=['GET'])
@jwt_required()
def get_tool_instances():
    # Endpoint para atribuições - retorna apenas instâncias disponíveis
    
    # Primeiro busca todas as ferramentas
    tools_response = supabase.table("tool").select("*").execute()
    tools_data = tools_response.data if tools_response.data else []
    
    available_instances = []
    
    for tool in tools_data:
        # Busca instâncias desta ferramenta
        instances_response = supabase.table("tool_instance").select("*").eq("tool_id", tool['id']).execute()
        instances = instances_response.data if instances_response.data else []
        
        # Se não há instâncias, cria automaticamente
        if not instances:
            quantity = tool.get('quantity', tool.get('total_quantity', 1))
            for _ in range(int(quantity)):
                instance_response = supabase.table("tool_instance").insert({
                    "tool_id": tool['id'],
                    "status": "Disponível",
                    "quantity": 1
                }).execute()
                if instance_response.data:
                    instances.append(instance_response.data[0])
        
        # Adiciona apenas instâncias disponíveis
        for instance in instances:
            if instance['status'] == 'Disponível':
                available_instances.append({
                    'id': instance['id'],
                    'tool_id': instance['tool_id'],
                    'tool_name': tool['name'],
                    'status': instance['status'],
                    'quantity': instance.get('quantity', 1),
                    'current_user_id': instance.get('current_user_id'),
                    'assigned_at': instance.get('assigned_at')
                })
    
    return jsonify({'tools': available_instances}), 200

@tools_bp.route('/<int:tool_id>', methods=['PUT'])
@jwt_required()
def update_tool(tool_id):
    admin_check = require_admin()
    if admin_check:
        return admin_check

    data = request.get_json()
    if not data or not data.get('quantity'):
        return jsonify({'error': 'Quantidade é obrigatória'}), 400

    new_quantity = int(data['quantity'])
    
    try:
        # Busca a ferramenta
        tool_response = supabase.table("tool").select("*").eq("id", tool_id).execute()
        if not tool_response.data:
            return jsonify({'error': 'Ferramenta não encontrada'}), 404
        
        tool = tool_response.data[0]
        
        # Busca instâncias atuais
        instances_response = supabase.table("tool_instance").select("*").eq("tool_id", tool_id).execute()
        current_instances = instances_response.data if instances_response.data else []
        current_quantity = len(current_instances)
        
        # Verifica se há instâncias emprestadas
        borrowed_instances = [i for i in current_instances if i['status'] != 'Disponível']
        if new_quantity < len(borrowed_instances):
            return jsonify({'error': f'Não é possível reduzir para {new_quantity}. Há {len(borrowed_instances)} unidade(s) emprestada(s)'}), 400
        
        # Atualiza a ferramenta principal
        supabase.table("tool").update({
            "quantity": new_quantity,
            "total_quantity": new_quantity
        }).eq("id", tool_id).execute()
        
        if new_quantity > current_quantity:
            # Adiciona novas instâncias
            for _ in range(new_quantity - current_quantity):
                supabase.table("tool_instance").insert({
                    "tool_id": tool_id,
                    "status": "Disponível",
                    "quantity": 1
                }).execute()
        
        elif new_quantity < current_quantity:
            # Remove instâncias disponíveis (apenas as disponíveis)
            available_instances = [i for i in current_instances if i['status'] == 'Disponível']
            instances_to_remove = current_quantity - new_quantity
            
            for i in range(min(instances_to_remove, len(available_instances))):
                supabase.table("tool_instance").delete().eq("id", available_instances[i]['id']).execute()
        
        return jsonify({'message': 'Ferramenta atualizada com sucesso'}), 200
        
    except Exception as e:
        print(f"Error updating tool: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@tools_bp.route('/<int:tool_id>', methods=['DELETE'])
@jwt_required()
def delete_tool(tool_id):
    admin_check = require_admin()
    if admin_check:
        return admin_check
    
    try:
        # Busca a ferramenta
        tool_response = supabase.table("tool").select("*").eq("id", tool_id).execute()
        if not tool_response.data:
            return jsonify({'error': 'Ferramenta não encontrada'}), 404
        
        # Busca instâncias
        instances_response = supabase.table("tool_instance").select("*").eq("tool_id", tool_id).execute()
        instances = instances_response.data if instances_response.data else []
        
        # Verifica se há instâncias emprestadas
        borrowed_instances = [i for i in instances if i['status'] != 'Disponível']
        if borrowed_instances:
            return jsonify({'error': f'Não é possível excluir. Há {len(borrowed_instances)} unidade(s) emprestada(s)'}), 400
        
        # Remove todas as instâncias
        for instance in instances:
            supabase.table("tool_instance").delete().eq("id", instance['id']).execute()
        
        # Remove a ferramenta
        supabase.table("tool").delete().eq("id", tool_id).execute()
        
        return jsonify({'message': 'Ferramenta excluída com sucesso'}), 200
        
    except Exception as e:
        print(f"Error deleting tool: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
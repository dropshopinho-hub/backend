from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import supabase
from werkzeug.security import generate_password_hash

user_bp = Blueprint('user', __name__)

# ------------------------------
# Listar usuários (exceto o próprio)
# ------------------------------
@user_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    current_user_id = get_jwt_identity()
    resp = supabase.table("users").select("*").neq("id", current_user_id).execute()
    users = resp.data if resp.data else []
    return jsonify({'users': users}), 200

# ------------------------------
# Criar usuário (aberto - sem login)
# ------------------------------
@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    # Impede usernames duplicados
    check_resp = supabase.table("users").select("*").eq("username", username).execute()
    if check_resp.data:
        return jsonify({'error': 'Username already exists'}), 400

    import uuid
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "username": username,
        "password_hash": generate_password_hash(password),
        "role": role
    }
    supabase.table("users").insert(user).execute()

    return jsonify(user), 201

# ------------------------------
# Obter perfil de usuário
# ------------------------------
@user_bp.route('/users/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table("users").select("*").eq("id", current_user_id).execute()
    current_user = resp.data[0] if resp.data else None

    # Restrição: usuário só vê o próprio perfil, admin vê qualquer um
    if current_user.get("role") != 'admin' and str(current_user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    user_resp = supabase.table("users").select("*").eq("id", user_id).execute()
    user = user_resp.data[0] if user_resp.data else None
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user}), 200

# ------------------------------
# Atualizar usuário
# ------------------------------
@user_bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table("users").select("*").eq("id", current_user_id).execute()
    current_user = resp.data[0] if resp.data else None

    # Somente o próprio ou admin podem atualizar
    if current_user.get("role") != 'admin' and str(current_user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    user_resp = supabase.table("users").select("*").eq("id", user_id).execute()
    user = user_resp.data[0] if user_resp.data else None
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.json
    update_data = {}

    # Atualiza username
    if 'username' in data:
        # Verifica se novo username já existe
        check_resp = supabase.table("users").select("*").eq("username", data['username']).neq("id", user_id).execute()
        if check_resp.data:
            return jsonify({'error': 'Username already taken'}), 400
        update_data['username'] = data['username']
    
    # Atualiza senha
    if 'password' in data and data['password']:
        from werkzeug.security import generate_password_hash
        update_data['password_hash'] = generate_password_hash(data['password'])
    
    # Admin pode alterar role
    if current_user.get("role") == 'admin' and 'role' in data:
        update_data['role'] = data['role']

    if update_data:
        supabase.table("users").update(update_data).eq("id", user_id).execute()

    updated_resp = supabase.table("users").select("*").eq("id", user_id).execute()
    updated_user = updated_resp.data[0] if updated_resp.data else None
    return jsonify(updated_user), 200

# ------------------------------
# Deletar usuário
# ------------------------------
@user_bp.route('/users/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    resp = supabase.table("users").select("*").eq("id", current_user_id).execute()
    current_user = resp.data[0] if resp.data else None

    # Restrição: apenas admin pode excluir outros usuários
    if current_user.get("role") != 'admin' and str(current_user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    user_resp = supabase.table("users").select("*").eq("id", user_id).execute()
    user = user_resp.data[0] if user_resp.data else None
    if not user:
        return jsonify({'error': 'User not found'}), 404

    supabase.table("users").delete().eq("id", user_id).execute()

    return jsonify({'message': 'User deleted successfully'}), 200
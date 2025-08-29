from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from src.models.user import supabase

auth_bp = Blueprint('auth', __name__)

def require_admin(user_id):
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    user = response.data[0] if response.data else None
    if not user or user.get("role") != "admin":
        return False
    return True

@auth_bp.route('/admin/edit-user/<user_id>', methods=['PUT'])
@jwt_required()
def admin_edit_user(user_id):
    current_user_id = get_jwt_identity()
    if not require_admin(current_user_id):
        return jsonify({'error': 'Acesso negado: apenas administradores podem editar usuários.'}), 403

    response = supabase.table("users").select("*").eq("id", user_id).execute()
    user = response.data[0] if response.data else None
    if not user:
        return jsonify({'error': 'Usuário não encontrado.'}), 404

    data = request.get_json()
    update_data = {}

    if data.get('username'):
        # Verifica se já existe outro usuário com esse username
        check_resp = supabase.table("users").select("*").eq("username", data['username']).neq("id", user_id).execute()
        if check_resp.data:
            return jsonify({'error': 'Nome de usuário já existe.'}), 400
        update_data['username'] = data['username']
    if data.get('password'):
        update_data['password_hash'] = generate_password_hash(data['password'])
    if data.get('role'):
        update_data['role'] = data['role']

    if update_data:
        supabase.table("users").update(update_data).eq("id", user_id).execute()

    # Retorna usuário atualizado
    updated_resp = supabase.table("users").select("*").eq("id", user_id).execute()
    updated_user = updated_resp.data[0] if updated_resp.data else None
    return jsonify({'message': 'Usuário atualizado com sucesso.', 'user': updated_user}), 200

@auth_bp.route('/admin/delete-user/<user_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_user(user_id):
    current_user_id = get_jwt_identity()
    if not require_admin(current_user_id):
        return jsonify({'error': 'Acesso negado: apenas administradores podem deletar usuários.'}), 403

    response = supabase.table("users").select("*").eq("id", user_id).execute()
    user = response.data[0] if response.data else None
    if not user:
        return jsonify({'error': 'Usuário não encontrado.'}), 404

    supabase.table("users").delete().eq("id", user_id).execute()
    return jsonify({'message': 'Usuário deletado com sucesso.'}), 200

@auth_bp.route('/admin/create-user', methods=['POST'])
@jwt_required()
def admin_create_user():
    current_user_id = get_jwt_identity()
    if not require_admin(current_user_id):
        return jsonify({'error': 'Acesso negado: apenas administradores podem criar usuários.'}), 403

    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']
    role = data.get('role', 'user')

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
    return jsonify({'message': 'User created successfully', 'user': user}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']

    response = supabase.table("users").select("*").eq("username", username).execute()
    user = response.data[0] if response.data else None

    if user and check_password_hash(user['password_hash'], password):
        access_token = create_access_token(identity=user['id'])
        return jsonify({
            'access_token': access_token,
            'user': user
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    response = supabase.table("users").select("*").eq("id", current_user_id).execute()
    user = response.data[0] if response.data else None

    if user:
        return jsonify({'user': user}), 200
    else:
        return jsonify({'error': 'User not found'}), 404
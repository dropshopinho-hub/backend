from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from src.models.user import User, db

auth_bp = Blueprint('auth', __name__)

# Endpoint para editar usuário (apenas admin)
@auth_bp.route('/admin/edit-user/<user_id>', methods=['PUT'])
@jwt_required()
def admin_edit_user(user_id):
    current_user_id = get_jwt_identity()
    admin_user = User.query.get(current_user_id)
    if not admin_user or admin_user.role != 'admin':
        return jsonify({'error': 'Acesso negado: apenas administradores podem editar usuários.'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado.'}), 404

    data = request.get_json()
    if data.get('username'):
        # Verifica se já existe outro usuário com esse username
        if User.query.filter(User.username == data['username'], User.id != user_id).first():
            return jsonify({'error': 'Nome de usuário já existe.'}), 400
        user.username = data['username']
    if data.get('password'):
        user.set_password(data['password'])
    if data.get('role'):
        user.role = data['role']
    db.session.commit()
    return jsonify({'message': 'Usuário atualizado com sucesso.', 'user': user.to_dict()}), 200

 # ...existing code...
# Endpoint para deletar usuário (apenas admin)
@auth_bp.route('/admin/delete-user/<user_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_user(user_id):
    current_user_id = get_jwt_identity()
    admin_user = User.query.get(current_user_id)
    if not admin_user or admin_user.role != 'admin':
        return jsonify({'error': 'Acesso negado: apenas administradores podem deletar usuários.'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado.'}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Usuário deletado com sucesso.'}), 200

# Novo endpoint: cadastro de usuário apenas para administradores

@auth_bp.route('/admin/create-user', methods=['POST'])
@jwt_required()
def admin_create_user():
    current_user_id = get_jwt_identity()
    admin_user = User.query.get(current_user_id)
    if not admin_user or admin_user.role != 'admin':
        return jsonify({'error': 'Acesso negado: apenas administradores podem criar usuários.'}), 403

    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    username = data['username']
    password = data['password']
    role = data.get('role', 'user')  # Default to 'user' if not especificado

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    user = User(username=username, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User created successfully', 'user': user.to_dict()}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    username = data['username']
    password = data['password']
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user:
        return jsonify({'user': user.to_dict()}), 200
    else:
        return jsonify({'error': 'User not found'}), 404


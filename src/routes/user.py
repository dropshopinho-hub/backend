from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, db

user_bp = Blueprint('user', __name__)

# ------------------------------
# Listar usuários (exceto o próprio)
# ------------------------------
@user_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    current_user_id = get_jwt_identity()
    users = User.query.filter(User.id != current_user_id).all()
    return jsonify({'users': [user.to_dict() for user in users]}), 200


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
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    user = User(username=username, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify(user.to_dict()), 201


# ------------------------------
# Obter perfil de usuário
# ------------------------------
@user_bp.route('/users/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # Restrição: usuário só vê o próprio perfil, admin vê qualquer um
    if current_user.role != 'admin' and str(current_user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


# ------------------------------
# Atualizar usuário
# ------------------------------
@user_bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # Somente o próprio ou admin podem atualizar
    if current_user.role != 'admin' and str(current_user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get_or_404(user_id)
    data = request.json

    # Atualiza username
    if 'username' in data:
        # Verifica se novo username já existe
        if User.query.filter(User.username == data['username'], User.id != user_id).first():
            return jsonify({'error': 'Username already taken'}), 400
        user.username = data['username']
    
    # Atualiza senha
    if 'password' in data and data['password']:
        user.set_password(data['password'])
    
    # Admin pode alterar role
    if current_user.role == 'admin' and 'role' in data:
        user.role = data['role']

    db.session.commit()
    return jsonify(user.to_dict()), 200


# ------------------------------
# Deletar usuário
# ------------------------------
@user_bp.route('/users/<user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    # Restrição: apenas admin pode excluir outros usuários
    if current_user.role != 'admin' and str(current_user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'}), 200

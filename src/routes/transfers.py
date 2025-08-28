from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, db
from src.models.tool import Tool, ToolInstance, ToolLog
from datetime import datetime

transfers_bp = Blueprint('transfers', __name__)

# ------------------------------
# Iniciar transferência
# ------------------------------
@transfers_bp.route('', methods=['POST'])
@jwt_required()
def create_transfer():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or not data.get('tool_instance_id') or not data.get('to_user_id'):
        return jsonify({'error': 'Tool instance ID and target user ID are required'}), 400
    
    tool_instance_id = data['tool_instance_id']
    to_user_id = data['to_user_id']
    
    if to_user_id == current_user_id:
        return jsonify({'error': 'Cannot transfer tool to yourself'}), 400
    
    # Buscar a instância da ferramenta
    instance = ToolInstance.query.get(tool_instance_id)
    
    if not instance:
        return jsonify({'error': 'Tool instance not found'}), 404
    
    if instance.current_user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if instance.status != 'Emprestado':
        return jsonify({'error': 'Tool is not currently borrowed'}), 400
    
    # Verificar se o usuário destino existe
    target_user = User.query.get(to_user_id)
    if not target_user:
        return jsonify({'error': 'Target user not found'}), 404
    
    # Iniciar a transferência
    instance.status = 'Aguardando Confirmação de Transferência'
    instance.transferred_to_user_id = to_user_id
    instance.transfer_initiated_at = datetime.utcnow()
    
    # Registrar log
    log = ToolLog(
        tool_instance_id=instance.id,
        action='Transferência',
        from_user_id=current_user_id,
        to_user_id=to_user_id,
        quantity=1
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'message': 'Transfer initiated successfully'}), 201


# ------------------------------
# Confirmar transferência
# ------------------------------
@transfers_bp.route('/<transfer_id>/confirm', methods=['PUT'])
@jwt_required()
def confirm_transfer(transfer_id):
    current_user_id = get_jwt_identity()
    
    instance = ToolInstance.query.get(transfer_id)
    
    if not instance:
        return jsonify({'error': 'Transfer not found'}), 404
    
    if instance.transferred_to_user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if instance.status != 'Aguardando Confirmação de Transferência':
        return jsonify({'error': 'Transfer not pending confirmation'}), 400
    
    # Confirmar
    instance.current_user_id = current_user_id
    instance.status = 'Emprestado'
    instance.transferred_to_user_id = None
    instance.transfer_initiated_at = None
    instance.assigned_at = datetime.utcnow()
    
    log = ToolLog(
        tool_instance_id=instance.id,
        action='Confirmação de Transferência',
        to_user_id=current_user_id,
        quantity=1
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'message': 'Transfer confirmed successfully'}), 200


# ------------------------------
# Rejeitar transferência
# ------------------------------
@transfers_bp.route('/<transfer_id>/reject', methods=['PUT'])
@jwt_required()
def reject_transfer(transfer_id):
    current_user_id = get_jwt_identity()
    
    instance = ToolInstance.query.get(transfer_id)
    
    if not instance:
        return jsonify({'error': 'Transfer not found'}), 404
    
    if instance.transferred_to_user_id != current_user_id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if instance.status != 'Aguardando Confirmação de Transferência':
        return jsonify({'error': 'Transfer not pending confirmation'}), 400
    
    # Pegar usuário original do log
    transfer_log = ToolLog.query.filter_by(
        tool_instance_id=instance.id,
        action='Transferência'
    ).order_by(ToolLog.timestamp.desc()).first()
    
    original_user_id = transfer_log.from_user_id if transfer_log else None
    if not original_user_id:
        return jsonify({'error': 'Original user not found for this transfer'}), 400
    
    # Rejeitar
    instance.current_user_id = original_user_id
    instance.status = 'Emprestado'
    instance.transferred_to_user_id = None
    instance.transfer_initiated_at = None
    
    log = ToolLog(
        tool_instance_id=instance.id,
        action='Recusa de Transferência',
        from_user_id=current_user_id,
        to_user_id=original_user_id,
        quantity=1
    )
    db.session.add(log)
    db.session.commit()
    
    return jsonify({'message': 'Transfer rejected successfully'}), 200


# ------------------------------
# Listar transferências pendentes
# ------------------------------
@transfers_bp.route('/pending/<user_id>', methods=['GET'])
@jwt_required()
def get_pending_transfers(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    # Somente admin pode ver de outros usuários
    if current_user.role != 'admin' and str(current_user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    pending_transfers = ToolInstance.query.filter_by(
        transferred_to_user_id=user_id,
        status='Aguardando Confirmação de Transferência'
    ).all()
    
    return jsonify({
        'pending_transfers': [transfer.to_dict() for transfer in pending_transfers]
    }), 200

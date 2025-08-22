from src.models.user import db
import uuid
from datetime import datetime

class Tool(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    total_quantity = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f'<Tool {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'total_quantity': self.total_quantity
        }

class ToolInstance(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = db.Column(db.String(36), db.ForeignKey('tool.id'), nullable=False)
    current_user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Disponível')
    last_user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)  # Usuário que recusou
    assigned_at = db.Column(db.DateTime, nullable=True)
    transferred_to_user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)
    transfer_initiated_at = db.Column(db.DateTime, nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    # Relationships
    tool = db.relationship('Tool', backref='instances')
    current_user = db.relationship('User', foreign_keys=[current_user_id], backref='assigned_tools')
    transferred_to_user = db.relationship('User', foreign_keys=[transferred_to_user_id])

    def __repr__(self):
        return f'<ToolInstance {self.tool.name} - {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tool_id': self.tool_id,
            'tool_name': self.tool.name if self.tool else None,
            'current_user_id': self.current_user_id,
            'current_user_name': self.current_user.username if self.current_user else None,
            'status': self.status,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'transferred_to_user_id': self.transferred_to_user_id,
            'transferred_to_user_name': self.transferred_to_user.username if self.transferred_to_user else None,
            'transfer_initiated_at': self.transfer_initiated_at.isoformat() if self.transfer_initiated_at else None,
            'quantity': self.quantity
        }

class ToolLog(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_instance_id = db.Column(db.String(36), db.ForeignKey('tool_instance.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    from_user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)
    to_user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    tool_instance = db.relationship('ToolInstance', backref='logs')
    from_user = db.relationship('User', foreign_keys=[from_user_id])
    to_user = db.relationship('User', foreign_keys=[to_user_id])

    def __repr__(self):
        return f'<ToolLog {self.action} - {self.timestamp}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tool_instance_id': self.tool_instance_id,
            'action': self.action,
            'from_user_id': self.from_user_id,
            'from_user_name': self.from_user.username if self.from_user else None,
            'to_user_id': self.to_user_id,
            'to_user_name': self.to_user.username if self.to_user else None,
            'quantity': self.quantity,
            'timestamp': self.timestamp.isoformat()
        }


import uuid
from datetime import datetime
from supabase import create_client, Client

# -------------------------
# 🔧 Conexão com o Supabase
# -------------------------
url = "https://yglyswztimbvkipsbeux.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlnbHlzd3p0aW1idmtpcHNiZXV4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYzOTcwNTksImV4cCI6MjA3MTk3MzA1OX0.0sM6gpMicEc-sM7vjEWlnEEyGIvSbju9nln94dcPAm0"

supabase: Client = create_client(url, key)

# -------------------------
# 📦 Modelo: Ferramenta
# -------------------------
class Tool:
    def __init__(self, name, total_quantity=0, id=None):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.total_quantity = total_quantity

    def __repr__(self):
        return f'<Tool {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'total_quantity': self.total_quantity
        }

    def save(self):
        supabase.table("tool").insert(self.to_dict()).execute()

# -------------------------
# 🛠️ Modelo: Instância da Ferramenta
# -------------------------
class ToolInstance:
    def __init__(self, tool_id, status='Disponível', current_user_id=None, last_user_id=None,
                 assigned_at=None, transferred_to_user_id=None, transfer_initiated_at=None, quantity=1, id=None):
        self.id = id or str(uuid.uuid4())
        self.tool_id = tool_id
        self.current_user_id = current_user_id
        self.status = status
        self.last_user_id = last_user_id
        self.assigned_at = assigned_at
        self.transferred_to_user_id = transferred_to_user_id
        self.transfer_initiated_at = transfer_initiated_at
        self.quantity = quantity

    def __repr__(self):
        return f'<ToolInstance {self.tool_id} - {self.status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tool_id': self.tool_id,
            'current_user_id': self.current_user_id,
            'status': self.status,
            'last_user_id': self.last_user_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'transferred_to_user_id': self.transferred_to_user_id,
            'transfer_initiated_at': self.transfer_initiated_at.isoformat() if self.transfer_initiated_at else None,
            'quantity': self.quantity
        }

    def save(self):
        supabase.table("tool_instance").insert(self.to_dict()).execute()

# -------------------------
# 📜 Modelo: Log de Ferramentas
# -------------------------
class ToolLog:
    def __init__(self, tool_instance_id, action, from_user_id=None, to_user_id=None,
                 quantity=1, timestamp=None, id=None):
        self.id = id or str(uuid.uuid4())
        self.tool_instance_id = tool_instance_id
        self.action = action
        self.from_user_id = from_user_id
        self.to_user_id = to_user_id
        self.quantity = quantity
        self.timestamp = timestamp or datetime.utcnow()

    def __repr__(self):
        return f'<ToolLog {self.action} - {self.timestamp}>'

    def to_dict(self):
        return {
            'id': self.id,
            'tool_instance_id': self.tool_instance_id,
            'action': self.action,
            'from_user_id': self.from_user_id,
            'to_user_id': self.to_user_id,
            'quantity': self.quantity,
            'timestamp': self.timestamp.isoformat()
        }

    def save(self):
        supabase.table("tool_log").insert(self.to_dict()).execute()

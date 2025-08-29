"""
Inicialização do pacote src
(Removido SQLAlchemy, agora usamos Supabase direto)
"""

from supabase import create_client, Client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")  # Busca do ambiente
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Busca do ambiente

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL ou SUPABASE_SERVICE_KEY não definida no ambiente.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
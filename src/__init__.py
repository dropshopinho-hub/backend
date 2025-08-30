"""
Inicialização do pacote src
(Removido SQLAlchemy, agora usamos Supabase direto)
"""

from supabase import create_client, Client
import os

# Configuração do Supabase - prioriza variáveis de ambiente, fallback para valores diretos
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://yglyswztimbvkipsbeux.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlnbHlzd3p0aW1idmtpcHNiZXV4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYzOTcwNTksImV4cCI6MjA3MTk3MzA1OX0.0sM6gpMicEc-sM7vjEWlnEEyGIvSbju9nln94dcPAm0")

# Cliente Supabase configurado

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
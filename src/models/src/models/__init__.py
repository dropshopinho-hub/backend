# src/models/__init__.py
"""
Models centralizados.
Agora usamos Supabase (não mais SQLAlchemy).
"""

# 🔹 importa a conexão e funções utilitárias
from .user import supabase, ensure_admin

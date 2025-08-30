#!/usr/bin/env python3
"""
Script para testar a conexão com o Supabase
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from src import supabase
    print("✅ Importação do Supabase bem-sucedida")
    
    # Teste básico de conexão
    response = supabase.table("users").select("count").execute()
    print(f"✅ Conexão com banco OK - Tabela users acessível")
    print(f"📊 Dados retornados: {response.data}")
    
except Exception as e:
    print(f"❌ Erro na conexão: {e}")
    print("\n🔍 Verificações necessárias:")
    print("1. SUPABASE_URL está definida?", os.getenv("SUPABASE_URL") is not None)
    print("2. SUPABASE_SERVICE_KEY está definida?", os.getenv("SUPABASE_SERVICE_KEY") is not None)
    
    if os.getenv("SUPABASE_URL"):
        print(f"   URL: {os.getenv('SUPABASE_URL')}")
    if os.getenv("SUPABASE_SERVICE_KEY"):
        print(f"   KEY: {os.getenv('SUPABASE_SERVICE_KEY')[:20]}...")

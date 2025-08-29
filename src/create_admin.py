import os
from supabase import create_client, Client
import uuid
import hashlib
import sys

# Dados do Supabase
url = "https://yglyswztimbvkipsbeux.supabase.co"
key = os.getenv("SUPABASE_SERVICE_KEY")  # ⚠️ use a service role key em variável de ambiente

if not key:
    print("Erro: SUPABASE_SERVICE_KEY não definida no ambiente.")
    sys.exit(1)

supabase: Client = create_client(url, key)

# Defina o usuário admin
ADMIN_USERNAME = "RafaelPinho"
ADMIN_PASSWORD = "@21314100"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def ensure_admin_user():
    # Verifica se já existe
    response = supabase.table("users").select("*").eq("username", ADMIN_USERNAME).execute()

    if response.data and len(response.data) > 0:
        print("Usuário admin já existe.")
        return

    # Cria novo admin
    admin_user = {
        "id": str(uuid.uuid4()),
        "username": ADMIN_USERNAME,
        "password_hash": hash_password(ADMIN_PASSWORD),
        "role": "admin"
    }

    supabase.table("users").insert(admin_user).execute()
    print(f"Usuário admin criado: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")

if __name__ == "__main__":
    ensure_admin_user()
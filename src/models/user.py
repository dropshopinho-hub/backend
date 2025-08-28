import uuid
from supabase import create_client, Client
from werkzeug.security import generate_password_hash

# Conexão com Supabase
url = "https://yglyswztimbvkipsbeux.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlnbHlzd3p0aW1idmtpcHNiZXV4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYzOTcwNTksImV4cCI6MjA3MTk3MzA1OX0.0sM6gpMicEc-sM7vjEWlnEEyGIvSbju9nln94dcPAm0"
supabase: Client = create_client(url, key)

# Defina o usuário admin
ADMIN_USERNAME = "RafaelPinho"
ADMIN_PASSWORD = "@21314100"

def ensure_admin():
    # Verifica se o usuário já existe
    response = supabase.table("users").select("*").eq("username", ADMIN_USERNAME).execute()

    if response.data and len(response.data) > 0:
        print("Usuário admin já existe.")
        return

    # Se não existir, cria
    admin_user = {
        "id": str(uuid.uuid4()),
        "username": ADMIN_USERNAME,
        "password_hash": generate_password_hash(ADMIN_PASSWORD),
        "role": "admin"
    }
    supabase.table("users").insert(admin_user).execute()
    print(f"Usuário admin criado: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")

if __name__ == "__main__":
    ensure_admin()


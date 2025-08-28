from supabase import create_client, Client

# Conexão com o Supabase
url = "https://yglyswztimbvkipsbeux.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlnbHlzd3p0aW1idmtpcHNiZXV4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYzOTcwNTksImV4cCI6MjA3MTk3MzA1OX0.0sM6gpMicEc-sM7vjEWlnEEyGIvSbju9nln94dcPAm0"
supabase: Client = create_client(url, key)


def listar_ferramentas_recusadas():
    response = (
        supabase.table("tool_instances")
        .select("id, quantity, tools(name)")  # pega o nome da ferramenta relacionada
        .eq("status", "Recusada")
        .execute()
    )

    if not response.data:
        print("Nenhuma ferramenta com status Recusada.")
    else:
        for ti in response.data:
            tools = ti.get("tools")
            nome = tools["name"] if tools and "name" in tools else "N/A"
            quantidade = ti.get("quantity", 0)
            print(f"Ferramenta: {nome}, Quantidade: {quantidade}")


if __name__ == "__main__":
    listar_ferramentas_recusadas()

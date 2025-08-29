from src.models.user import supabase

tools = supabase.table("tool").select("*").execute().data

for tool in tools:
    # Verifica quantas instâncias já existem para esta ferramenta
    existing = supabase.table("tool_instance").select("id").eq("tool_id", tool["id"]).execute().data
    to_create = tool["quantity"] - len(existing)
    if to_create > 0:
        for _ in range(to_create):
            supabase.table("tool_instance").insert({
                "tool_id": tool["id"],
                "status": "Disponível"
            }).execute()
    else:
        print(f"Já existem {len(existing)} instâncias para a ferramenta {tool['name']} (id: {tool['id']})")
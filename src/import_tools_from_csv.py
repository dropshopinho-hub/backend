import csv
from supabase import create_client, Client

# Dados do Supabase
url = "https://yglyswztimbvkipsbeux.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlnbHlzd3p0aW1idmtpcHNiZXV4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYzOTcwNTksImV4cCI6MjA3MTk3MzA1OX0.0sM6gpMicEc-sM7vjEWlnEEyGIvSbju9nln94dcPAm0"
supabase: Client = create_client(url, key)


def import_csv_to_supabase(csv_file_path: str, table_name: str):
    try:
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

            if not rows:
                print("⚠️ O arquivo CSV está vazio ou não possui cabeçalho.")
                return

            for row in rows:
                # Se a coluna "id" não for UUID válido, remove e deixa o Supabase gerar automaticamente
                if "id" in row:
                    if not row["id"].strip() or "-" not in row["id"]:
                        row.pop("id")

                response = supabase.table(table_name).insert(row).execute()

                if response.data:
                    print(f"✅ Linha inserida: {row}")
                else:
                    print(f"❌ Erro ao inserir linha: {row}\nResposta: {response}")

        print("🚀 Importação concluída com sucesso!")

    except Exception as e:
        print(f"❌ Erro inesperado: {e}")


if __name__ == "__main__":
    # Importa usuários
    import_csv_to_supabase("users.csv", "users")



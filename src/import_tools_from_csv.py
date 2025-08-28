import csv
from supabase import create_client, Client

# Dados do Supabase
url = "https://yglyswztimbvkipsbeux.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlnbHlzd3p0aW1idmtpcHNiZXV4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYzOTcwNTksImV4cCI6MjA3MTk3MzA1OX0.0sM6gpMicEc-sM7vjEWlnEEyGIvSbju9nln94dcPAm0"
supabase: Client = create_client(url, key)

def import_csv_to_supabase(csv_file_path, table_name):
    try:
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            if not rows:
                print("O arquivo CSV está vazio ou não possui cabeçalho.")
                return
            for row in rows:
                response = supabase.table(table_name).insert(row).execute()
                if response.status_code != 201:
                    print(f"Erro ao inserir: {row}\nResposta: {response.data}")
        print("Importação concluída!")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    import_csv_to_supabase("tools.csv", "tools")  # Ajuste o nome do arquivo e da tabela
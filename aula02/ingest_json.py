import json
import psycopg2

DB_HOST = "localhost"
DB_NAME = "aula02"
DB_USER = "postgres"
DB_PASSWORD = "libia"

def ingest_json_to_postgres(json_file_path, table_name):
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()

        # Criar tabela para dados JSON (usando tipo JSONB para flexibilidade)
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                dados JSONB
            );
        """)
        conn.commit()

        with open(json_file_path, 'r') as f:
            data = json.load(f)
            for record in data:
                cur.execute(f"INSERT INTO {table_name} (dados) VALUES (%s)", (json.dumps(record),))
        conn.commit()
        print(f"Dados do JSON '{json_file_path}' ingeridos com sucesso na tabela '{table_name}'.")

    except Exception as e:
        print(f"Erro ao ingerir dados JSON: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

if __name__ == "__main__":
    ingest_json_to_postgres('pedidos.json', 'pedidos_json')

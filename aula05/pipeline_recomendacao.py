import csv
import json
import psycopg2
import random
# Configurações do Banco de Dados
DB_HOST = "localhost"
DB_NAME = "meu_banco_de_dados"
DB_USER = "seu_usuario"
DB_PASSWORD = "sua_senha"
def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER,
password=DB_PASSWORD)
def ingest_produtos_csv(csv_file_path):
    conn = get_db_connection()
    cur = conn.cursor()
    with open(csv_file_path, 'r') as f:
        reader = csv.reader(f)
        next(csv.reader) # Pula o cabeçalho
        for row in csv.reader:
            product_id, nome, descricao, categoria = row
        # Simula a geração de um embedding de 3 dimensões
            embedding = [round(random.uniform(-1, 1), 3) for _ in range(3)] 
            cur.execute(
            "INSERT INTO produtos_master (id, nome, descricao, categoria, embedding) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET nome = EXCLUDED.nome, descricao = EXCLUDED.descricao, categoria = EXCLUDED.categoria, embedding = EXCLUDED.embedding",
        (product_id, nome, descricao, categoria, str(embedding)))
    conn.commit()
    cur.close()
    conn.close()
    print(f"Produtos de '{csv_file_path}' ingeridos e embeddings gerados.")
def ingest_avaliacoes_json(json_file_path):
    conn = get_db_connection()
    cur = conn.cursor()
    with open(json_file_path, 'r') as f:
        avaliacoes_data = json.load(f)
        for avaliacao in avaliacoes_data:
            cur.execute(
            "INSERT INTO avaliacoes_raw (dados) VALUES (%s)", (json.dumps(avaliacao),))
        conn.commit()
    cur.close()
    conn.close()
    print(f"Avaliações de '{json_file_path}' ingeridas.")
def process_avaliacoes():
    conn = get_db_connection()
    cur = conn.cursor()
# Limpa a tabela de avaliações processadas para reprocessamento
    cur.execute("TRUNCATE TABLE avaliacoes_processadas;")
    cur.execute("SELECT dados FROM avaliacoes_raw;")
    raw_avaliacoes = cur.fetchall()
for raw_avaliacao in raw_avaliacoes:
    avaliacao_json = raw_avaliacao[0]
    produto_id = avaliacao_json.get("produto_id")
    cliente_id = avaliacao_json.get("cliente_id")
    nota_avaliacao = avaliacao_json.get("avaliacao")
    comentario = avaliacao_json.get("comentario")
        # Simples lógica de sentimento
    if nota_avaliacao >= 4:
            sentimento = "positivo"
    elif nota_avaliacao <= 2:
        sentimento = "negativo"
    else:
        sentimento = "neutro"
    cur.execute(
        "INSERT INTO avaliacoes_processadas (produto_id, cliente_id, avaliacao, comentario, sentimento) VALUES (%s, %s, %s, %s, %s)",
(produto_id, cliente_id, nota_avaliacao, comentario, sentimento)
)
    conn.commit()
    cur.close()
    conn.close()
    print("Avaliações processadas e armazenadas.")
def get_product_embedding(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT embedding FROM produtos_master WHERE id = %s", (product_id,))
    embedding_str = cur.fetchone()
    cur.close()
    conn.close()
    if embedding_str and embedding_str[0]:
# Converte a string do vetor de volta para uma lista de floats
return [float(x) for x in embedding_str[0][1:-1].split(',')]
return None
def recommend_products(seed_product_id, limit=3):
seed_embedding = get_product_embedding(seed_product_id)
if not seed_embedding:
print(f"Produto com ID {seed_product_id} não encontrado ou sem embedding.")
return []
conn = get_db_connection()
cur = conn.cursor()
# Busca por similaridade cosseno (quanto mais próximo de 0, mais similar)
cur.execute(
"""
SELECT
pm.id, pm.nome, pm.categoria,
pm.embedding <=> %s AS distancia_cosseno,
AVG(ap.avaliacao) AS media_avaliacoes,
COUNT(CASE WHEN ap.sentimento = 'positivo' THEN 1 END) AS avaliacoes_positivas
FROM produtos_master pm
LEFT JOIN avaliacoes_processadas ap ON pm.id = ap.produto_id
WHERE pm.id != %s
GROUP BY pm.id, pm.nome, pm.categoria, pm.embedding
ORDER BY distancia_cosseno ASC
LIMIT %s;
""",
(str(seed_embedding), seed_product_id, limit)
)
recommendations = cur.fetchall()
cur.close()
conn.close()
return recommendations
if __name__ == "__main__":
print("Iniciando pipeline de recomendação...")
# 1. Ingestão de Produtos
ingest_produtos_csv('produtos.csv')
# 2. Ingestão de Avaliações

ingest_avaliacoes_json('avaliacoes.json')
# 3. Processamento de Avaliações
process_avaliacoes()
print("\n--- Recomendações ---")
# Exemplo de recomendação para o Smartphone X (ID 1)
seed_product_id = 1
print(f"Buscando recomendações para o produto ID {seed_product_id} (Smartphone X):")
recs = recommend_products(seed_product_id)
if recs:
for r_id, r_nome, r_categoria, r_distancia, r_media_aval, r_pos_aval in recs:
print(f" - ID: {r_id}, Nome: {r_nome}, Categoria: {r_categoria}, Similaridade:
{1 - r_distancia:.2f}, Média Aval.: {r_media_aval:.1f}, Positivas: {r_pos_aval}")
else:
print(" Nenhuma recomendação encontrada.")
print("\n--- Recomendações ---")
# Exemplo de recomendação para o Laptop Gamer Z (ID 2)
seed_product_id = 2
print(f"Buscando recomendações para o produto ID {seed_product_id} (Laptop Gamer Z):")
recs = recommend_products(seed_product_id)
if recs:
for r_id, r_nome, r_categoria, r_distancia, r_media_aval, r_pos_aval in recs:
print(f" - ID: {r_id}, Nome: {r_nome}, Categoria: {r_categoria}, Similaridade:
{1 - r_distancia:.2f}, Média Aval.: {r_media_aval:.1f}, Positivas: {r_pos_aval}")
else:
print(" Nenhuma recomendação encontrada.")
print("Pipeline de recomendação concluído.")
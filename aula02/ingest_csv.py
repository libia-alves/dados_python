
import csv            # Importa o módulo nativo para manipulação e leitura de arquivos CSV
import psycopg2  # Importa a biblioteca de driver para conectar e executar comandos no PostgreSQL

# Bloco de configuração dos parâmetros de conexão com o banco de dados
DB_HOST = "localhost"             # Endereço onde o banco está rodando (na própria máquina local)
DB_NAME = "aula02"             # Nome do banco de dados a ser conectado (ajuste se necessário)
DB_USER = "postgres"             # Nome do usuário com permissão de escrita no banco
DB_PASSWORD = "libia"  # Senha do usuário do banco de dados

def ingest_csv_to_postgres(csv_file_path, table_name):  # Função que recebe o caminho do CSV e o nome da tabela
    conn = None                                                                  # Inicializa a variável de conexão como nula para controle de encerramento seguro
    try:                                                             # Inicia o bloco protegido para tratamento de exceções/erros
        conn = psycopg2.connect(                    # Estabelece a conexão com a instância do PostgreSQL
            host=DB_HOST,                                # Passa o host configurado
            database=DB_NAME,                       # Passa o nome do banco
            user=DB_USER,                               # Passa o usuário
            password=DB_PASSWORD             # Passa a senha
        )
        cur = conn.cursor()                                # Cria um cursor para enviar e executar instruções SQL no banco

        # Executa comando DDL para criar a tabela caso ela ainda não exista
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT PRIMARY KEY,
                nome VARCHAR(100),
                preco NUMERIC(10, 2)
            );
        """)
        conn.commit()                                         # Confirma (persiste) a criação da tabela no banco de dados

        with open(csv_file_path, 'r', encoding='utf-8') as f:  # Abre o arquivo CSV em modo leitura ('r')
            reader = csv.reader(f)                                          # Cria o leitor iterável que divide as linhas pelas vírgulas
            header = next(reader)                                          # Lê e avança a primeira linha (cabeçalho: id, nome, preco) sem inseri-la

            for row in reader:                                            # Itera sobre cada linha de dados restante do arquivo CSV
                cur.execute(                                               # Executa o comando de inserção parametrizado para evitar SQL Injection
                    f"INSERT INTO {table_name} (id, nome, preco) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",  # SQL de inserção ignorando duplicados
                    row                                                        # Tupla/lista com os valores extraídos da linha atual [id, nome, preco]
                )

        conn.commit()                                                    # Confirma a transação com todas as inserções realizadas
        print(f"✅ Dados do CSV '{csv_file_path}' ingeridos com sucesso na tabela '{table_name}'.")  # Mensagem de sucesso no terminal

    except Exception as e:                                     # Captura qualquer falha que ocorra durante o processo
        print(f"❌ Erro ao ingerir dados CSV: {e}")  # Exibe a mensagem de erro detalhada
    finally:                                                               # Bloco que sempre será executado ao final, com erro ou sem erro
        if conn:                                                          # Verifica se a conexão chegou a ser aberta
            cur.close()                                                 # Fecha o cursor de comandos SQL
            conn.close()                                              # Fecha a conexão com o banco de dados liberando os recursos

if __name__ == "__main__":                                # Ponto de entrada padrão quando o script é executado diretamente
    ingest_csv_to_postgres('produtos.csv', 'produtos_csv')  # Chama a função passando o arquivo e a tabela de destino


📂 Ingestão e Sincronização de Dados JSON em PostgreSQL

Projeto prático desenvolvido durante a aula de Sincronização de Dados com Python e Banco de Dados, com foco em inserção performática, tratamento de fontes e formatos (JSON) e boas práticas de conexão com PostgreSQL.
🎯 Objetivos da Aula

    [x] Ler e manipular arquivos estruturados no formato JSON.

    [x] Conectar o Python ao PostgreSQL usando a biblioteca psycopg2.

    [x] Implementar inserção performática em lote (batch insert) com execute_values.

    [x] Garantir segurança e sanitização de consultas SQL para evitar SQL Injection.

    [x] Armazenas dados flexíveis com a estrutura JSONB.

💻 Estrutura do Código

O script realiza o fluxo completo de ingestão de dados:

    Conexão Segura: Estabelece conexão com o PostgreSQL e trata o encerramento das conexões no bloco finally.

    Criação de Tabela: Garante a existência da tabela e sanitiza o nome informado via psycopg2.sql.Identifier.

    Leitura e Tratamento: Lê o arquivo .json utilizando a codificação utf-8.

    Inserção Performática: Prepara a lista de registros e executa um INSERT único em lote.

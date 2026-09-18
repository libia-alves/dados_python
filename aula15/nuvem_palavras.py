from datetime import datetime
import re
import psycopg2

# Texto base sobre tecnologia para gerar a nuvem de palavras (pode vir de logs, artigos, etc.)
TEXTO_TECNOLOGIA = """
A inteligência artificial e o aprendizado de máquina estão revolucionando o desenvolvimento de software. 
A computação em nuvem, a segurança da informação e a ciência de dados são essenciais para a transformação digital das empresas.
Sistemas modernos utilizam inteligência artificial para otimizar processos, análise de dados em tempo real e automação.
O Python, o PostgreSQL e o Apache Superset formam uma pilha excelente para análise de dados e criação de dashboards.
A tecnologia avança rápido com inovação, programação, algoritmos e infraestrutura de nuvem robusta.
"""

# Lista de conectivos / stop words em português para eliminar
STOP_WORDS = {
    "a",
    "o",
    "e",
    "de",
    "do",
    "da",
    "em",
    "um",
    "para",
    "é",
    "com",
    "não",
    "uma",
    "os",
    "no",
    "se",
    "na",
    "por",
    "mais",
    "as",
    "dos",
    "como",
    "mas",
    "ao",
    "ele",
    "das",
    "à",
    "seu",
    "sua",
    "ou",
    "quando",
    "muito",
    "nos",
    "já",
    "eu",
    "também",
    "só",
    "pelo",
    "pela",
    "até",
    "so",
    "isso",
    "ela",
    "entre",
    "depois",
    "sem",
    "mesmo",
    "aos",
    "seus",
    "quem",
    "nas",
    "me",
    "esse",
    "eles",
    "você",
    "essa",
    "num",
    "nem",
    "suas",
    "meu",
    "minha",
    "numa",
    "pelos",
    "elas",
    "qual",
    "nós",
    "lhe",
    "deles",
    "essas",
    "esses",
    "pelas",
    "este",
    "fosse",

    "dele",
    "tu",
    "te",
    "cês",
    "vos",
    "lhes",
    "meus",
    "minhas",
    "teu",
    "tua",
    "teus",
    "tuas",
    "nosso",
    "nossa",
    "nossos",
    "nossas",
    "dela",
    "delas",
    "esta",
    "estes",
    "estas",
    "quele",
    "quela",
    "queles",
    "quelas",
    "isto",
    "aquilo",
    "estou",
    "está",
    "estamos",
    "estão",
    "estive",
    "esteve",
    "estivemos",
    "estiveram",
    "estava",
    "estávamos",
    "estavam",
    "estivera",
    "estivéramos",
    "esteja",
    "estejamos",
    "estejam",
    "estivesse",
    "estivéssemos",
    "estivessem",
    "estiver",
    "estivermos",
    "estiverem",
    "hei",
    "há",
    "havemos",
    "hão",
    "houve",
    "houvemos",
    "houveram",
    "houvera",
    "houvéramos",
    "haja",
    "hajamos",
    "hajam",
    "houvesse",
    "houvéssemos",
    "houvessem",
    "houver",
    "houvermos",
    "houverem",
    "houverei",
    "houverá",
    "houveremos",
    "houverão",
    "houveria",
    "houveríamos",
    "houveriam",
    "sou",
    "somos",
    "são",
    "fui",
    "foi",
    "fomos",
    "foram",
    "fora",
    "fôramos",
    "seja",
    "sejamos",
    "sejam",
    "fosse",
    "fôssemos",
    "fossem",
    "for",
    "formos",
    "forem",
    "serei",
    "será",
    "seremos",
    "serão",
    "seria",
    "seríamos",
    "seriam",
    "tenho",
    "tem",
    "temos",
    "tém",
    "tinha",
    "tínhamos",
    "tinham",
    "tive",
    "teve",
    "tivemos",
    "tiveram",
    "tivera",
    "tivéramos",
    "tenha",
    "tenhamos",
    "tenham",
    "tivesse",
    "tivéssemos",
    "tivessem",
    "tiver",
    "tivermos",
    "tiverem",
    "terei",
    "terá",
    "teremos",
    "terão",
    "teria",
    "teríamos",
    "teriam",
}


def processar_e_salvar():
  # 1. Limpeza do texto e extração de palavras
  palavras_brutas = re.findall(r'\b[a-zA-Zá-úÁ-ÚçÇ]+\b', TEXTO_TECNOLOGIA.lower())

  # 2. Filtrar conectivos e palavras menores que 3 letras
  palavras_filtradas = [
      p for p in palavras_brutas if p not in STOP_WORDS and len(p) > 2
  ]

  # 3. Contar frequências
  frequencias = {}
  for palavra in palavras_filtradas:
    frequencias[palavra] = frequencias.get(palavra, 0) + 1

  # 4. Conectar ao banco PostgreSQL e atualizar a tabela
  try:
    conexao = psycopg2.connect(
        dbname='nuvem_palavras',
        user='postgres',
        password='postgres',  # Substitua pela senha real do seu usuário
        host='localhost',
        port='5432',
    )
    cursor = conexao.cursor()

    # Inserir ou atualizar (Upsert)
    for palavra, freq in frequencias.items():
      cursor.execute(
          """
                INSERT INTO nuvem_palavras_tecnologia (palavra, frequencia, ultima_atualizacao)
                VALUES (%s, %s, %s)
                ON CONFLICT (palavra) 
                DO UPDATE SET frequencia = EXCLUDED.frequencia, 
                              ultima_atualizacao = EXCLUDED.ultima_atualizacao;
            """,
          (palavra, freq, datetime.now()),
      )

    conexao.commit()
    cursor.close()
    conexao.close()
    print('Nuvem de palavras atualizada com sucesso no banco!')
  except Exception as e:
    print('Erro ao conectar ou gravar no banco:', e)


if __name__ == '__main__':
  processar_e_salvar()


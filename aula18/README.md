# Atividade aula 18 — Pipeline meteorológico (Apache Hop)

Projeto Apache Hop (mesmo formato da `aula17/`) que integra duas fontes meteorológicas,
separa os dados em camadas **bronze** e **silver**, coloca em **quarentena** os registros
com problema de qualidade e registra erros/eventos em log durante a execução.

Testado de ponta a ponta nesta sessão com `hop-run.sh` (motor local do Hop 2.19.0, o
mesmo instalado em `~/Downloads/apache-hop-client-2.19.0`) — não é só XML escrito à mão,
o workflow e os dois pipelines rodaram de verdade e produziram os arquivos que estão
em `repository/` e `logs/`. O projeto já está registrado no Hop deste computador com o
nome **aula18** (`hop-conf.sh -pl` mostra ele apontando para esta pasta), então basta
abrir o Hop GUI que ele já aparece em Tools > Projects.

## Como as 4 exigências da atividade foram atendidas

**a) Separação de dados com falha (quarentena)**
O pipeline `pipelines/silver_quarantine_split.hpl` marca cada registro com o motivo da
rejeição em `MOTIVO_QUARENTENA`:
- `missing_above_30_percent`: mais de 30% dos 3 campos meteorológicos (temperatura,
  umidade, vento) estão vazios.
- `constant_temperature_over_4_hours`: a mesma estação registrou a **mesma temperatura**
  por 5 ou mais leituras horárias seguidas (5 leituras de 1h = 4h entre a primeira e a
  última — "mais de 4h seguidas").

Quem não tem motivo vai para `repository/silver/`; quem tem, vai para
`repository/quarantine/` junto com `MISSING_PCT`, `CONSTANT_TEMP_4H` e o motivo.

**b) Segunda fonte meteorológica**
`data/raw/fonte_1_estacao.csv` (estação local) e `data/raw/fonte_2_weather.csv` (serviço
de terceiros) têm nomes de coluna diferentes. `pipelines/bronze_ingest.hpl` lê as duas
(cada uma com seu próprio passo **CSV Input**) e as une no mesmo esquema canônico
(`TIMESTAMP, STATION, TEMPERATURE_C, HUMIDITY_PCT, WIND_KMH, SOURCE`).

**c) Registro de erros e problemas no workflow**
- Cada pipeline grava seu próprio log de execução em `logs/bronze_ingest.log` e
  `logs/silver_quarantine_split.log` (configurado na ação do workflow).
- Linha sem estação ou sem timestamp válido é descartada e logada como `ERROR` pelo
  passo "validar e registrar erros" (visto de verdade no teste: `invalid_input_row
  origem=... motivo=estacao_ou_timestamp_ausente`).
- Cada registro quarentenado é logado (nível WARN/basic) pelo passo "filtrar quarentena":
  `record_quarantined estacao=... timestamp=... motivo=...`.
- No **workflow** (`workflows/main_weather_quality.hwf`), se qualquer um dos dois
  pipelines falhar, ele segue o ramo vermelho até uma ação **Write to log** (`registrar
  erro ingestao` / `registrar erro qualidade`) que grava o problema no log do workflow
  em nível ERROR. Testado de propósito apontando `RAW_DIR` para uma pasta inexistente:
  o pipeline falhou, o workflow pulou a etapa seguinte e caiu certinho no log de erro.

**d) Bronze e silver**
`repository/bronze/meteorologia_bronze.csv` (tudo, sem filtro de qualidade) e
`repository/silver/meteorologia_silver.csv` (só aprovados), com `repository/quarantine/`
como camada extra para os rejeitados.

## Estrutura do projeto

```
aula18/
├── data/raw/
│   ├── fonte_1_estacao.csv        (fonte a)
│   └── fonte_2_weather.csv        (fonte b)
├── pipelines/
│   ├── bronze_ingest.hpl              le as 2 fontes, valida, grava bronze
│   └── silver_quarantine_split.hpl    aplica as regras de qualidade, grava silver/quarentena
├── workflows/
│   └── main_weather_quality.hwf       orquestra os 2 pipelines + registro de erro
├── repository/
│   ├── bronze/meteorologia_bronze.csv
│   ├── silver/meteorologia_silver.csv
│   └── quarantine/meteorologia_quarentena.csv
├── logs/                               log de cada execucao (gerado pelo workflow)
├── metadata/                           run configurations exigidas pelo Hop
├── project-config.json
└── python_version/     (a versao em Python puro feita antes desta, mantida como
                          referencia/backup — nao faz parte da entrega em Hop)
```

## Como abrir e rodar no Hop GUI

O projeto **aula18** já está registrado neste computador (`Tools > Projects` no Hop GUI
já mostra ele). Se abrir em outra máquina: **Tools > Projects > New/Manage projects**,
Home folder = esta pasta `aula18/` (ele reconhece o `project-config.json`).

1. Abra `workflows/main_weather_quality.hwf` e rode com ▶. Ele executa `bronze_ingest`
   e depois `silver_quarantine_split`, em sequência.
2. Resultado em `repository/bronze/`, `repository/silver/`, `repository/quarantine/` e
   os logs em `logs/`.

Cada pipeline também roda sozinho (abra o `.hpl`, "Executar"). O passo "avaliar
qualidade" usa um **User Defined Java Class** (recurso nativo do Hop, não é script
externo) para a regra de temperatura constante, porque essa regra depende de olhar
várias linhas seguidas da mesma estação — não dá pra fazer só com passos de
arrasta-e-solta simples.

## Como rodar por linha de comando (o mesmo jeito usado para testar aqui)

```bash
cd ~/Downloads/apache-hop-client-2.19.0/hop
./hop-run.sh -j aula18 -r local -f ".../aula18/workflows/main_weather_quality.hwf" -l Basic
```

## Parametrização (migração entre ambientes)

Nenhum caminho está fixo dentro dos passos — tudo é `Named Parameter`/variável do
projeto, com padrão relativo a `${PROJECT_HOME}`: `RAW_DIR`, `BRONZE_DIR`, `SILVER_DIR`,
`QUARANTINE_DIR`, `LOG_DIR`. Para migrar de ambiente, basta sobrescrever essas variáveis
(linha de comando `-p`, tela de execução do Hop GUI, ou um `project-config.json`
diferente por ambiente) — igual ao esquema já usado na `aula17/`.

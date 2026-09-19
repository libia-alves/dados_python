# Atividade aula 18: pipeline meteorológico

Pipeline didático em Python puro que integra duas fontes meteorológicas e aplica regras de qualidade antes de publicar os dados na camada silver.

## Regras de qualidade

- Uma linha vai para a quarentena quando mais de 30% das medições meteorológicas (`temperature_c`, `humidity_pct` e `wind_kmh`) estão faltantes.
- Uma linha vai para a quarentena quando a temperatura da mesma estação fica igual por mais de 4 horas consecutivas. A regra exige 5 leituras horárias iguais e marca toda a sequência.
- Cada rejeição recebe `quarantine_reason` e um evento `record_quarantined` no log.
- Linhas inválidas na ingestão também são registradas como `invalid_input_row`.

## Camadas

- `data/raw`: entradas das fontes 1 e 2.
- `repository/bronze/meteorologia_bronze.csv`: todos os registros normalizados, preservando a origem.
- `repository/silver/meteorologia_silver.csv`: somente registros aprovados.
- `repository/quarantine/meteorologia_quarentena.csv`: registros rejeitados e seus motivos.
- `logs/pipeline.jsonl`: eventos estruturados do workflow.

## Executar

```bash
python pipeline.py
python -m unittest discover -s tests -v
```

A saída esperada do exemplo é `bronze=13`, `silver=6` e `quarantine=7`: cinco registros pela temperatura constante e dois pela falta de dados.

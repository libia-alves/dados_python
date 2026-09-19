"""Pipeline de qualidade meteorologica com camadas bronze, silver e quarentena."""

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
BRONZE_DIR = ROOT / "repository" / "bronze"
SILVER_DIR = ROOT / "repository" / "silver"
QUARANTINE_DIR = ROOT / "repository" / "quarantine"
LOG_DIR = ROOT / "logs"

MEASUREMENTS = ("temperature_c", "humidity_pct", "wind_kmh")
CANONICAL_FIELDS = ("timestamp", "station", *MEASUREMENTS, "source")
SOURCE_MAPPINGS = {
    "fonte_1_estacao.csv": {
        "timestamp": "timestamp",
        "station": "station",
        "temperature_c": "temperature_c",
        "humidity_pct": "humidity_pct",
        "wind_kmh": "wind_kmh",
    },
    "fonte_2_weather.csv": {
        "timestamp": "observed_at",
        "station": "location",
        "temperature_c": "temp_c",
        "humidity_pct": "humidity",
        "wind_kmh": "wind_speed_kmh",
    },
}


def configure_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("weather_pipeline")
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_DIR / "pipeline.jsonl", mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


def log_event(logger: logging.Logger, level: str, event: str, **details: object) -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "event": event,
        **details,
    }
    getattr(logger, level.lower())(json.dumps(payload, ensure_ascii=False))


def parse_number(value: str) -> float | None:
    value = value.strip()
    return None if value == "" else float(value)


def ingest_source(path: Path, logger: logging.Logger) -> list[dict[str, object]]:
    mapping = SOURCE_MAPPINGS[path.name]
    records: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as source_file:
        for line_number, raw in enumerate(csv.DictReader(source_file), start=2):
            try:
                timestamp = datetime.fromisoformat(raw[mapping["timestamp"]])
                record = {
                    "timestamp": timestamp.isoformat(timespec="seconds"),
                    "station": raw[mapping["station"]].strip(),
                    "temperature_c": parse_number(raw[mapping["temperature_c"]]),
                    "humidity_pct": parse_number(raw[mapping["humidity_pct"]]),
                    "wind_kmh": parse_number(raw[mapping["wind_kmh"]]),
                    "source": path.name,
                }
                if not record["station"]:
                    raise ValueError("station vazia")
                records.append(record)
            except (KeyError, TypeError, ValueError) as error:
                log_event(logger, "ERROR", "invalid_input_row", source=path.name,
                          line=line_number, error=str(error), row=raw)
    log_event(logger, "INFO", "source_ingested", source=path.name, records=len(records))
    return records


def write_csv(path: Path, records: Iterable[dict[str, object]], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: record.get(field, "") for field in fields} for record in records)


def missing_percentage(record: dict[str, object]) -> float:
    missing = sum(record[field] is None for field in MEASUREMENTS)
    return missing / len(MEASUREMENTS) * 100


def constant_temperature_records(records: list[dict[str, object]]) -> set[int]:
    flagged: set[int] = set()
    by_station: dict[str, list[tuple[int, dict[str, object]]]] = {}
    for index, record in enumerate(records):
        by_station.setdefault(str(record["station"]), []).append((index, record))

    for station_records in by_station.values():
        station_records.sort(key=lambda item: str(item[1]["timestamp"]))
        run: list[tuple[int, dict[str, object]]] = []
        for item in station_records + [(None, {"temperature_c": object(), "timestamp": ""})]:
            if run and (
                item[0] is None
                or item[1]["temperature_c"] != run[-1][1]["temperature_c"]
                or datetime.fromisoformat(str(item[1]["timestamp"]))
                - datetime.fromisoformat(str(run[-1][1]["timestamp"])) != timedelta(hours=1)
            ):
                if len(run) > 4 and run[0][1]["temperature_c"] is not None:
                    flagged.update(index for index, _ in run)
                run = []
            if item[0] is not None and item[1]["temperature_c"] is not None:
                run.append(item)
    return flagged


def validate_records(records: list[dict[str, object]], logger: logging.Logger) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    constant_indexes = constant_temperature_records(records)
    silver: list[dict[str, object]] = []
    quarantine: list[dict[str, object]] = []
    for index, record in enumerate(records):
        reasons: list[str] = []
        if missing_percentage(record) > 30:
            reasons.append("missing_above_30_percent")
        if index in constant_indexes:
            reasons.append("constant_temperature_over_4_hours")
        if reasons:
            rejected = {**record, "quarantine_reason": ";".join(reasons)}
            quarantine.append(rejected)
            log_event(logger, "WARNING", "record_quarantined", station=record["station"],
                      timestamp=record["timestamp"], reasons=reasons)
        else:
            silver.append(record)
    return silver, quarantine


def run_pipeline() -> dict[str, int]:
    logger = configure_logging()
    all_records: list[dict[str, object]] = []
    for source_name in SOURCE_MAPPINGS:
        all_records.extend(ingest_source(RAW_DIR / source_name, logger))

    write_csv(BRONZE_DIR / "meteorologia_bronze.csv", all_records, CANONICAL_FIELDS)
    silver, quarantine = validate_records(all_records, logger)
    write_csv(SILVER_DIR / "meteorologia_silver.csv", silver, CANONICAL_FIELDS)
    write_csv(QUARANTINE_DIR / "meteorologia_quarentena.csv", quarantine,
              (*CANONICAL_FIELDS, "quarantine_reason"))
    summary = {"bronze": len(all_records), "silver": len(silver), "quarantine": len(quarantine)}
    log_event(logger, "INFO", "pipeline_finished", **summary)
    return summary


if __name__ == "__main__":
    print(json.dumps(run_pipeline(), indent=2, ensure_ascii=False))

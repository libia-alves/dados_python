import unittest

from pipeline import constant_temperature_records, missing_percentage, run_pipeline


class PipelineTest(unittest.TestCase):
    def test_missing_percentage_is_calculated_from_measurements(self):
        record = {"temperature_c": None, "humidity_pct": None, "wind_kmh": 10}
        self.assertGreater(missing_percentage(record), 30)

    def test_constant_temperature_rule_requires_more_than_four_hours(self):
        records = [
            {"station": "A", "timestamp": f"2026-09-18T0{i}:00:00", "temperature_c": 20}
            for i in range(5)
        ]
        self.assertEqual(constant_temperature_records(records), {0, 1, 2, 3, 4})

    def test_pipeline_writes_all_layers(self):
        summary = run_pipeline()
        self.assertEqual(summary, {"bronze": 13, "silver": 6, "quarantine": 7})


if __name__ == "__main__":
    unittest.main()

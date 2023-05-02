import pytest
from datetime import datetime
from sqlite_to_influxdb import convert_value, convert_timestamp, convert_to_influxdb


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        ("1.5", "1.5"),
        ("3", "3i"),
        ("-2.8", "-2.8"),
        ("ON", "true"),
        ("true", "true"),
        ("yes", "true"),
        ("off", "false"),
        ("false", "false"),
        ("no", "false"),
        ("string with spaces", '"string with spaces"'),
    ],
)
def test_convert_value(input_value, expected_output):
    assert convert_value(input_value) == expected_output


def test_convert_timestamp():
    expected_output = 1577836800 - 3600
    assert convert_timestamp("2020-01-01T00:00:00") == expected_output


@pytest.mark.parametrize(
    "sensor_id, rows, tags, expected_output",
    [
        (
            "mySensor",
            [("12", "2020-01-01T00:00:00")],
            None,
            ["mySensor value=12i 1577833200"],
        ),
        (
            "mySensor",
            [("unknown", "2020-01-01T00:00:00"), ("10", "2020-01-01T00:00:10")],
            {"tag1": "value1"},
            [
                "mySensor,tag1=value1 value=10i 1577833210",
            ],
        ),
        (
            "mySensor",
            [("on", "2020-01-01T00:00:00"), ("off", "2020-01-01T00:00:01")],
            {"tag1": "value1", "tag2": "value2"},
            [
                "mySensor,tag1=value1,tag2=value2 value=true 1577833200",
                "mySensor,tag1=value1,tag2=value2 value=false 1577833201",
            ],
        ),
    ],
)
def test_convert_to_influxdb(sensor_id, rows, tags, expected_output):
    # input_rows = [
    #     (value, datetime.fromisoformat(timestamp_str)) for value, timestamp_str in rows
    # ]
    result = list(convert_to_influxdb(sensor_id, rows, tags))
    assert result == expected_output

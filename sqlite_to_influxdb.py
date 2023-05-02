import argparse
import logging
import sqlite3
import sys
from datetime import datetime

log = logging.getLogger(__name__)


def get_sensor_data(conn, sensor):
    cur = conn.cursor()
    cur.execute(
        f"SELECT state, last_updated FROM states WHERE entity_id = '{sensor}' AND state != 'unknown' ORDER BY last_updated DESC"
    )
    return cur.fetchall()


def get_conn(db_file):
    return sqlite3.connect(db_file)


def parse_tags(tag_string):
    tags = {}
    if tag_string:
        for tag in tag_string.split(","):
            key, value = tag.split("=")
            tags[key.strip()] = value.strip()
    return tags


from contextlib import suppress


def convert_value(value):
    with suppress(ValueError):
        if "." in value:
            num_value = float(value)
            return f"{num_value}"
        else:
            num_value = int(value)
            return f"{num_value}i"

    with suppress(ValueError):
        num_value = int(value)
        return f"{num_value}u"

    if value.lower() in {"on", "true", "yes"}:
        return "true"
    elif value.lower() in {"off", "false", "no"}:
        return "false"
    else:
        return f'"{value}"'


def convert_timestamp(timestamp_str):
    timestamp = datetime.fromisoformat(timestamp_str).timestamp()
    return int(timestamp)


def convert_to_influxdb(sensor_id, rows, tags=None):
    for value, timestamp_str in rows:
        if value.lower() == "unknown":
            continue
        converted_value = convert_value(value)
        timestamp = convert_timestamp(timestamp_str)
        if tags:
            tag_set = ",".join([f"{k}={v}" for k, v in tags.items()]) if tags else ""
            yield f"{sensor_id},{tag_set} value={converted_value} {timestamp}"
        else:
            yield f"{sensor_id} value={converted_value} {timestamp}"


def get_args():
    parser = argparse.ArgumentParser(
        description="Convert Home Assistant SQLite database to InfluxDB line format"
    )
    parser.add_argument("db_file", help="Path to the Home Assistant SQLite database")
    parser.add_argument(
        "sensors",
        metavar="sensor",
        nargs="*",
        help="Entity IDs of the sensors to convert",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase output verbosity"
    )
    parser.add_argument(
        "--tags",
        help="Add tags to the line protocol format. Use comma-separated key-value pairs, e.g., tag1=value1,tag2=value2",
    )
    return parser.parse_args()


def setup_logging(verbose):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()],
    )


def main(args):
    conn = get_conn(args.db_file)
    if not args.sensors:
        args.sensors = [sensor.strip() for sensor in sys.stdin.readlines()]
    if not args.sensors:
        logging.warning("Empty list of sensors")
    tags = parse_tags(args.tags)
    for sensor in args.sensors:
        rows = get_sensor_data(conn, sensor)
        log.info(f"Found {len(rows)} rows for sensor {sensor}")
        print("\n".join(convert_to_influxdb(sensor, rows, tags)))


if __name__ == "__main__":
    args = get_args()
    setup_logging(args.verbose)
    main(args)

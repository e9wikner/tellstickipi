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


def convert_to_influxdb(sensor_id, rows):
    for value, timestamp_str in rows:
        timestamp = datetime.fromisoformat(timestamp_str).strftime("%s%f")[:-3]
        yield f"{sensor_id} value={value} {timestamp}"


def get_args():
    parser = argparse.ArgumentParser(
        description="Convert Home Assistant SQLite database to Elasticsearch format"
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
    for sensor in args.sensors:
        rows = get_sensor_data(conn, sensor)
        log.info(f"Found {len(rows)} rows for sensor {sensor}")
        print("\n".join(convert_to_influxdb(sensor, rows)))


if __name__ == "__main__":
    args = get_args()
    setup_logging(args.verbose)
    main(args)

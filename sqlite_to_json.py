import argparse
import datetime
import json
import logging
import sqlite3
import sys

log = logging.getLogger(__name__)


def get_sensor_data(conn, sensor):
    cur = conn.cursor()
    cur.execute(
        f"SELECT state, last_updated FROM states WHERE entity_id = '{sensor}' ORDER BY last_updated DESC"
    )
    return cur.fetchall()


def get_conn(db_file):
    return sqlite3.connect(db_file)


def convert_row_to_dict(sensor, row):
    return {
        "sensor": sensor,
        "value": row[0],
        "timestamp": datetime.datetime.fromisoformat(row[1])
        .replace(microsecond=0)
        .isoformat()
        + "Z",
    }


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
        for d in (convert_row_to_dict(sensor, row) for row in rows):
            print(json.dumps(d))


if __name__ == "__main__":
    args = get_args()
    setup_logging(args.verbose)
    main(args)

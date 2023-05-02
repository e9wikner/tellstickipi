import argparse
import logging
import os
import sys
from influxdb_client import InfluxDBClient

log = logging.getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser(
        description="Upload InfluxDB line protocol data from stdin to a local InfluxDB server"
    )
    parser.add_argument(
        "--url",
        default=os.environ.get("INFLUXDB_URL", "http://localhost:8086"),
        help="InfluxDB server URL (default from environment variable INFLUXDB_URL or 'http://localhost:8086')",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("INFLUXDB_TOKEN", ""),
        help="InfluxDB API token (default from environment variable INFLUXDB_TOKEN)",
    )
    parser.add_argument(
        "--org",
        default=os.environ.get("INFLUXDB_ORG", ""),
        help="InfluxDB organization (default from environment variable INFLUXDB_ORG)",
    )
    parser.add_argument(
        "--bucket",
        default=os.environ.get("INFLUXDB_BUCKET", ""),
        help="InfluxDB bucket (default from environment variable INFLUXDB_BUCKET)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increase output verbosity",
    )
    return parser.parse_args()


def setup_logging(verbose):
    log_level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()],
    )


def main(args):
    with InfluxDBClient(url=args.url, token=args.token, org=args.org) as client:
        with client.write_api() as write_api:
            log.info("Reading line protocol data from stdin")
            data = sys.stdin.read()
            log.info("Writing data to InfluxDB")
            write_api.write(bucket=args.bucket, record=data, write_precision="s")
            log.info("Data upload complete")


if __name__ == "__main__":
    args = get_args()
    setup_logging(args.verbose)
    main(args)

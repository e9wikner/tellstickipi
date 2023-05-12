import argparse
import logging
import os
import sys
from pathlib import Path
from influxdb_client import InfluxDBClient

log = logging.getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser(
        description="Upload InfluxDB line protocol data from stdin or files to a local InfluxDB server"
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
        "--from-path",
        metavar="DIR",
        help="Read line protocol data from files with '.lineproto' suffix in a directory",
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


def upload_data(open_file, write_api, bucket):
    chunk_size = 5000
    while True:
        data = open_file.readlines(chunk_size)
        if not data:
            break
        data = "".join(data)
        write_api.write(bucket=bucket, record=data, write_precision="s")


def main(args):
    with InfluxDBClient(url=args.url, token=args.token, org=args.org) as client:
        with client.write_api() as write_api:
            if args.from_path:
                log.info(f"Reading line protocol data from {args.from_path}")
                path = Path(args.from_path)
                for file_path in path.glob("*.lineproto"):
                    with file_path.open() as file:
                        upload_data(file, write_api, args.bucket)
                        log.info(f"Data from {file_path} has been uploaded to InfluxDB")
            else:
                log.info("Reading line protocol data from stdin")
                upload_data(sys.stdin, write_api, args.bucket)
                log.info("Data from stdin has been uploaded to InfluxDB")


if __name__ == "__main__":
    args = get_args()
    setup_logging(args.verbose)
    main(args)

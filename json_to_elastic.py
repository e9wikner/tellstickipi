import argparse
import logging
import json
import sys
from elasticsearch import Elasticsearch

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)


def upload_to_elasticsearch(es, index_name, rows):
    for row in rows:
        doc = {
            "sensor": row["sensor"],
            "value": row["value"],
            "timestamp": row["timestamp"],
        }
        es.index(index=index_name, body=doc)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--index",
        default="homeassistant",
        help="Name of Elasticsearch index to upload data to",
    )
    parser.add_argument(
        "--host",
        default="http://localhost:9200",
        help="Host and port of Elasticsearch instance",
    )
    parser.add_argument("--user", default="elastic", help="Elasticsearch username")
    parser.add_argument("--password", required=True, help="Elasticsearch password")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Print verbose output"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    es = Elasticsearch(args.host, http_auth=(args.user, args.password))

    for line in json.load(sys.stdin):
        rows = line.strip()
        upload_to_elasticsearch(es, args.index, rows)

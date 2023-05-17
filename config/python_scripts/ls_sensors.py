import argparse
import sqlite3

def get_sensor_ids(db_path, sensor_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    if sensor_id is None:
        sensor_id = 'sensor.%'

    c.execute(f"SELECT DISTINCT entity_id FROM states WHERE entity_id LIKE '{sensor_id}'")
    rows = c.fetchall()
    sensor_ids = [row[0] for row in rows]

    conn.close()

    return sensor_ids

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('db_path', help='Path to Home Assistant sqlite database')
    parser.add_argument('--sensor-id', default='sensor.%', help='Sensor entity ID (default: sensor.%)')
    parser.add_argument('--to-file', help="Print to this file instead of stdout")
    args = parser.parse_args()

    sensor_ids = get_sensor_ids(args.db_path, args.sensor_id)

    if args.to_file:
        with open(args.to_file, mode="w") as f:
            f.write("\n".join(sensor_ids))
    else:
        print("\n".join(sensor_ids))


try:
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.write_api import SYNCHRONOUS
except:
    pass

from rpi_thermo_chick import logger

client = None

def init_influxdb_client(config):
    global client
    try:
        client = InfluxDBClient(url=config.get('url', 'http://localhost:8086'), 
            token=config.get('token', ''), 
            org=config.get('org', 'org'))
        logger.warning(f'influxdb client created')
    except Exception as e:
        logger.info(f'cannot create influxdb client, exception({e})')


def write_to_influxdb(point, bucket='rpi_thermo_chick', org='org'):
    try:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        name = point.get('name', 'tempSensors')
        tags = ','.join([f'{k}={v}' for k,v in point.get('tags').items()])
        fields = ','.join([f'{k}={v}' for k,v in point.get('fields').items()])
        write_api.write(bucket, org, f'{name},{tags} {fields}')
    except Exception as e:
        logger.warning(f'cannot write influxdb client, exception({e})')


import argparse
import atexit
import json
import happybase
import logging
import time

from kafka import KafkaProducer

logger_format = '%(asctime)-15s %(message)s'
logging.basicConfig(format=logger_format)
logger = logging.getLogger('data-storage-reader')
logger.setLevel(logging.DEBUG)

def shutdown_hook(producer,connection):
	"""
	a shutdown hook to be called before the shutdown
	"""
	try:
		logger.info('Closing Kafka producer.')
		producer.flush(10)
		producer.close()
		logger.info('Kafka producer closed.')
		logger.info('Closing Hbase connection.')
		connection.close()
		logger.info('Hbase connection closed.')
	except Exception as e:
		logger.warn('Failed to close producer, caused by: %s',str(e))
	finally:
		logger.info('Exiting program')

if __name__ == '__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('topic_name')
	parser.add_argument('kafka_broker')
	parser.add_argument('data_table')
	parser.add_argument('hbase_host')

	#Parse args
	args = parser.parse_args()
	topic_name = args.topic_name
	kafka_broker = args.kafka_broker
	data_table = args.data_table
	hbase_host = args.hbase_host

	#Initiate a simple Kafka producer
	kafka_producer = KafkaProducer(bootstrap_servers=kafka_broker)

	#Initiate a hbase connection
	hbase_connection = happybase.Connection(hbase_host)

	#Setup proper shutdown hook
	atexit.register(shutdown_hook, kafka_producer, hbase_connection)

	#Exit if the table is not found
	hbase_tables = [table.decode() for table in hbase_connection.tables()]
	if data_table not in hbase_tables:
		exit()

	# Scan table and push to Kafka
	table = hbase_connection.table(data_table)

	for key, data in table.scan():
		playload ={
			'Symbol':data[b'family:symbol'].decode(),
			'LastTradePrice':data[b'family:trade_price'].decode(),
			'Timestamp': data[b'family:trade_time'].decode()
		}
		logger.debug('Read dat from hbase: %s', playload)
		kafka_producer.send(topic= topic_name, value=json.dumps(playload).encode('utf-8'))

		time.sleep(1)

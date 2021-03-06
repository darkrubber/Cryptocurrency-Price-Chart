import json
import math

from unittest.mock import MagicMock
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from time import sleep

data_stream_module = __import__("data-stream")

topic = 'test_topic'

# testing case 1 
# 42000 / 3 = 14000
test_input = [
	json.dumps({'Timestamp': '1526900000001', 'Symbol': 'BTC-USD',
		'LastTradePrice':'10000'}),
	json.dumps({'Timestamp': '1526900000001', 'Symbol': 'BTC-USD',
		'LastTradePrice':'12000'}),
	json.dumps({'Timestamp': '1526900000001', 'Symbol': 'BTC-USD',
		'LastTradePrice':'20000'}),
]

def make_dstream_helper(sc, ssc, topic):
	input_rdds = [sc.parallelize(test_input, 1)]
	input_stream = ssc.queueStream(input_rdds)
	return input_stream

def test_data_stream(sc, ssc, topic):
	input_stream = make_dstream_helper(sc, ssc, test_input)	
	mock_kafka_producer = MagicMock()

	data_stream_module.process_stream(input_stream, mock_kafka_producer, topic)

	ssc.start()
	sleep(5)
	ssc.stop()

	mock_kafka_producer.send.assert_called_once()
	args, kwargs = mock_kafka_producer.send.call_args
	print(kwargs)

	assert math.isclose(json.loads(kwargs['value'])['Average'], 14000.0, rel_tol=1e-10) 

if __name__ == '__main__':
	sc = SparkContext('local[2]', 'local-testing')
	ssc = StreamingContext(sc, 10)

	test_data_stream(sc, ssc, topic)

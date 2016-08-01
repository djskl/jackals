import threading
import pika

def make_rabbitmq_channel(path_info):
    pass

class Channel(object):
    
    def __init__(self):
        self._conn = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
        self._chan = self._conn.channel()
        
    def subscribe(self, channel):
        self._chan.queue_declare(queue=channel, durable=True)
        
    def publish(self, channel, msg):
        self._chan.basic_publish(
            exchange='',
            routing_key=channel,
            body=msg,
            properties=pika.BasicProperties(
                delivery_mode = 2,
            )
        )
        
    def get_message(self):
        gen = self._chan.consume()
        return gen.next()


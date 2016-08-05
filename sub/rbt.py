import pika

def make_rabbitmq_channel(path_info):
    pass

class Channel(object):
    
    def __init__(self, cname):
        self._conn = pika.BlockingConnection(pika.ConnectionParameters(host="localhost"))
        self._chan = self._conn.channel()
        self.queue_name = cname
        self._chan.queue_declare(queue=self.queue_name, durable=True)
        self._gen = self._chan.consume(self.queue_name, inactivity_timeout=0)
        
    def publish(self, msg):
        self._chan.basic_publish(
            exchange='',
            routing_key=self.queue_name,
            body=msg,
            properties=pika.BasicProperties(
                delivery_mode = 2,
            )
        )
        
    def get_message(self):
        try:
            msg = self._gen.next()
            if msg:
                method, properties, body = msg
                self._chan.basic_ack(method.delivery_tag)
            return msg
        except:
            # Cancel the queue consumer created by `BlockingChannel.consume`,
            # rejecting all pending ackable messages.
            self._chan.cancel()
            return None
    
if __name__=="__main__":
    chan = Channel("hello")
    print chan.get_message()


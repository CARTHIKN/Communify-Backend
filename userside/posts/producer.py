import pika, json


connection = None

def get_channel():
    global connection
    if connection is None or connection.is_closed:
        # Create a new connection if not already present or if the existing one is closed
        params = pika.URLParameters('amqps://jowedhhd:Tg8MFcSu96ZcH71_10JqvcSkixgBWFtv@puffin.rmq2.cloudamqp.com/jowedhhd')

        connection = pika.BlockingConnection(params)
    try:
        return connection.channel()
    except pika.exceptions.StreamLostError:
        connection = None
        return get_channel()


def publish(method, body):
    channel = get_channel()
    properties = pika.BasicProperties(method)
    channel.basic_publish(exchange='', routing_key='notification', body=json.dumps(body), properties=properties)
#!/usr/bin/env python
"""import pika, sys, os

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='insult_canal')

def callback(ch, method, properties, body):
    print(f" [x] Received {body}")

channel.basic_consume(queue='insult_canal', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
"""
import pika

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare exchange
channel.exchange_declare(exchange='insult_canal', exchange_type='fanout')

# Create a new temporary queue (random name, auto-delete when consumer disconnects)
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue

# Bind the queue to the exchange
channel.queue_bind(exchange='insult_canal', queue=queue_name)

print(' [*] Waiting for messages. To exit, press CTRL+C')

# Define callback function
def callback(ch, method, properties, body):
    print(f" [x] Received {body.decode()}")

# Consume messages
channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
channel.start_consuming()

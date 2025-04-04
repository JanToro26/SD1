#!/usr/bin/env python
import pika
import time
import random

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
insults = ["Burro", "Retrasat", "Gilipolles"]
channel.queue_declare(queue='hello')

channel.basic_publish(exchange='', routing_key='hello', body='Hello World!')
print(" [x] Sent 'Hello World!'")

while True:
    insultRandom = random.choice(insults)
    channel.basic_publish(exchange='', routing_key='hello', body=insultRandom)
    print(" [x] Sent 'Hello World!'")
    time.sleep(5)
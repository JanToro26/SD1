#!/usr/bin/env python

import pika, redis, random, time

# Connect to the existing insults list using Redis
client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
insult_list = "insult_list"

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare a fanout exchange
channel.exchange_declare(exchange='insult_canal', exchange_type='fanout')

# Publish a message
while True:
    cua = client.lrange(insult_list, 0, -1)  # Obtenir la llista de Redis amb els insults
    message = random.choice(cua)
    channel.basic_publish(exchange='insult_canal', routing_key='', body=message)
    print(f" [x] Sent '{message}'")
    time.sleep(5)

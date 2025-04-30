#!/usr/bin/env python
import pika
import time
import random

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
insults = ["Burro", "Retrasat", "Gilipolles"]
channel.queue_declare(queue='insults')

while True:
    insultRandom = random.choice(insults)
    channel.basic_publish(exchange='', routing_key='insults', body=insultRandom)
    print(" [x] Sent '"+insultRandom+"'")
    time.sleep(5)
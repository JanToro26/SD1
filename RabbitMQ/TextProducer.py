#!/usr/bin/env python
import pika
import time
import random

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
frases = ["Com et trobes", "Un dia qualsevol", "Ja marxo"]
channel.queue_declare(queue='text')

while True:
    textRandom = random.choice(frases)
    channel.basic_publish(exchange='', routing_key='text', body=textRandom)
    print(" [x] Sent '"+textRandom+"'")
    time.sleep(5)
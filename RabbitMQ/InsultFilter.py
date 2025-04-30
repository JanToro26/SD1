#!/usr/bin/env python

import redis, pika

# Connect to the existing insults list using Redis
client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
insult_list = "insult_list"

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='text')
result = []
print("Consumer is waiting for text...")

# Define the callback function
def callback(ch, method, properties, body):
    text = body.decode('utf-8')  # Convertir de bytes a string
    cua = client.lrange(insult_list, 0, -1)  # Obtenir la llista de Redis amb els insults
    print(f" [Filter] Received {text}")
    lineWords = text[1].split(" ")
    for word in lineWords:
        if word in cua:
            lineWords[lineWords.index(word)] = 'CENSORED'
    lineWords = " ".join(lineWords)
    result.append(lineWords)
    print(f"Sortida: {lineWords}")

# Consume messages
channel.basic_consume(queue='text', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit, press CTRL+C')
channel.start_consuming()
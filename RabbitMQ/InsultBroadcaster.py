#!/usr/bin/env python

import redis
import pika
import random
import time

class InsultBroadcaster:
    def __init__(self):
        """Inicialitza la connexió a Redis i els paràmetres per a la transmissió."""
        self.client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = connection.channel()
        #channel_name = "insult_channel"

        # Declare a fanout exchange
        self.channel.exchange_declare(exchange='insult_canal', exchange_type='fanout')
        self.insult_list = "insult_list"
        self.delay = 5

    def broadcast(self):
        """Publica insults aleatoris de Redis de manera contínua."""
        while True:
            # Recupera una llista d'insults de Redis
            insults = self.client.lrange(self.insult_list, 0, -1)
            if insults:
                insult = random.choice(insults)  # Escull un insult aleatori
                self.channel.basic_publish(exchange='insult_canal', routing_key='', body=insult)
                print(f"Published: {insult}")
            time.sleep(self.delay)  # Simula un retard entre els missatges

if __name__ == "__main__":
    broadcaster = InsultBroadcaster()  # Inicialitza l'objecte
    broadcaster.broadcast()  # Inicia la transmissió

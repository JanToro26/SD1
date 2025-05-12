'''#!/usr/bin/env python
import pika
import time
import random

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
insults = ["Burro", "Retrasat", "Gilipolles", "tonto"]
channel.queue_declare(queue='insults')

while True:
    insultRandom = random.choice(insults)
    channel.basic_publish(exchange='', routing_key='insults', body=insultRandom)
    print(" [x] Sent '"+insultRandom+"'")
    time.sleep(5)'''

#!/usr/bin/env python

import pika
import time
import random

class InsultProducer:
    def __init__(self, rabbitmq_host='localhost', queue_name='insults', insults=None, delay=5):
        """Inicialitza la connexió a RabbitMQ i la cua."""
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
        self.channel = self.connection.channel()
        self.queue_name = queue_name
        self.insults = insults or ["Burro", "Retrasat", "Gilipolles", "tonto"]
        self.delay = delay

        # Declara la cua
        self.channel.queue_declare(queue=self.queue_name)

    def send_random_insult(self):
        """Selecciona un insult aleatoriament i l'envia a la cua."""
        insult_random = random.choice(self.insults)
        self.channel.basic_publish(exchange='', routing_key=self.queue_name, body=insult_random)
        print(f" [x] Sent '{insult_random}'")

    def run(self):
        """Comença a generar insults i enviar-los a la cua a intervals."""
        for insult in self.insults:
            self.channel.basic_publish(exchange='', routing_key=self.queue_name, body=insult)
            print(f"Produced: {insult}")
            time.sleep(self.delay)

if __name__ == "__main__":
    producer = InsultProducer()  # Inicialitza l'objecte
    producer.run()  # Comença a enviar insults

'''#!/usr/bin/env python
import pika
import time
import random

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
frases = ["Com et trobes capgros", "Un dia qualsevol", "Ja marxo, tonto"]
channel.queue_declare(queue='text')

while True:
    textRandom = random.choice(frases)
    channel.basic_publish(exchange='', routing_key='text', body=textRandom)
    print(" [x] Sent '"+textRandom+"'")
    time.sleep(5)'''

#!/usr/bin/env python

import pika
import time
import random

class TextProducer:
    def __init__(self, rabbitmq_host='localhost', queue_name='text', frases=None, delay=5):
        """Inicialitza la connexió a RabbitMQ i la cua."""
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
        self.channel = self.connection.channel()
        self.queue_name = queue_name
        self.frases = frases or ["Com et trobes capgros", "Un dia qualsevol", "Ja marxo, tonto"]
        self.delay = delay

        # Declara la cua
        self.channel.queue_declare(queue=self.queue_name)

    def send_random_text(self):
        """Selecciona una frase aleatòria i l'envia a la cua."""
        text_random = random.choice(self.frases)
        self.channel.basic_publish(exchange='', routing_key=self.queue_name, body=text_random)
        print(f" [x] Sent '{text_random}'")

    def run(self):
        """Comença a generar frases i enviar-les a la cua a intervals."""
        while True:
            self.send_random_text()
            time.sleep(self.delay)

if __name__ == "__main__":
    producer = TextProducer()  # Inicialitza l'objecte
    producer.run()  # Comença a enviar frases

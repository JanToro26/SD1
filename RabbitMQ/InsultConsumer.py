'''connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare a queue (ensure it exists)
channel.queue_declare(queue='insults')

# Define the callback function
def callback(ch, method, properties, body):
    insult = body.decode('utf-8')  # Convertir de bytes a string
    cua = client.lrange(insult_list, 0, -1)  # Obtenir la llista de Redis amb els insults
    print(f" [x] Received {insult}")
    if(insult in cua):
        print(f"L'insult {insult} ja està a la llista")
    else:
        print(f"L'insult {insult} no està a la llista")
        client.lpush(insult_list, insult)

# Consume messages
channel.basic_consume(queue='insults', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit, press CTRL+C')
channel.start_consuming()
'''
#!/usr/bin/env python

import pika
import redis

class InsultReceiver:
    def __init__(self):
        """Inicialitza les connexions a Redis i RabbitMQ, i la configuració necessària."""
        # Connexió a Redis
        self.client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.insult_list = 'insult_list'

        # Connexió a RabbitMQ
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

        # Declara la cua
        self.channel.queue_declare(queue='insults')

    def callback(self, ch, method, properties, body):
        """Callback per processar els missatges rebuts."""
        insult = body.decode('utf-8')  # Convertir de bytes a string
        cua = self.client.lrange(self.insult_list, 0, -1)  # Obtenir la llista de Redis amb els insults
        print(f" [x] Received {insult}")
        if insult in cua:
            print(f"L'insult {insult} ja està a la llista")
        else:
            print(f"L'insult {insult} no està a la llista")
            self.client.lpush(self.insult_list, insult)

    def run(self):
        """Comença a escoltar i processar els missatges."""
        # Consumeix els missatges
        self.channel.basic_consume(queue='insults', on_message_callback=self.callback, auto_ack=True)
        print(' [*] Waiting for messages. To exit, press CTRL+C')
        self.channel.start_consuming()

if __name__ == "__main__":
    receiver = InsultReceiver()  # Inicialitza l'objecte
    receiver.run()  # Comença a consumir missatges

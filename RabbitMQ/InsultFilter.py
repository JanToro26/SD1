'''#!/usr/bin/env python

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
    lineWords = text.split(" ")
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
'''
#!/usr/bin/env python

import redis
import pika

class InsultReceiver:
    def __init__(self, redis_host='localhost', redis_port=6379, rabbitmq_host='localhost', insult_list='insult_list'):
        """Inicialitza les connexions a Redis i RabbitMQ, i la configuració necessària."""
        # Connexió a Redis
        self.client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
        self.insult_list = insult_list

        # Connexió a RabbitMQ
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitmq_host))
        self.channel = self.connection.channel()

        # Declara la cua
        self.channel.queue_declare(queue='insults')
        self.channel.queue_declare(queue='text')

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

    def process_text(self, ch, method, properties, body):
        """Callback per processar els missatges rebuts i censurar el text."""
        text = body.decode('utf-8')  # Convertir de bytes a string
        cua = self.client.lrange(self.insult_list, 0, -1)  # Obtenir la llista de Redis amb els insults
        print(f" [Filter] Received {text}")
        lineWords = text.split(" ")
        for word in lineWords:
            if word in cua:
                lineWords[lineWords.index(word)] = 'CENSORED'
        lineWords = " ".join(lineWords)
        print(f"Sortida: {lineWords}")

    def run(self):
        """Comença a escoltar i processar els missatges."""
        # Consumeix els missatges d'insults
        self.channel.basic_consume(queue='insults', on_message_callback=self.callback, auto_ack=True)

        # Consumeix els missatges de text
        self.channel.basic_consume(queue='text', on_message_callback=self.process_text, auto_ack=True)

        print(' [*] Waiting for messages. To exit, press CTRL+C')
        self.channel.start_consuming()

if __name__ == "__main__":
    receiver = InsultReceiver()  # Inicialitza l'objecte
    receiver.run()  # Comença a consumir missatges

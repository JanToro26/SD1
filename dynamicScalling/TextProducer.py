import xmlrpc.client 
import random
import time

insult_queue = xmlrpc.client.ServerProxy('http://localhost:8002')

texts = ["Genis puto amo", "Jan Retrasat", "Puto Gilipolles"]


while True:
    textRandom = random.choice(texts)
    print(insult_queue.filtrar(textRandom))
    #channel.basic_publish(exchange='', routing_key='hello', body=insultRandom)
    #print(" [x] Sent 'Hello World!'")
    time.sleep(5)
import xmlrpc.client 
import random
import time

insult_queue = xmlrpc.client.ServerProxy('http://localhost:8000')

insults = ["Burro", "Retrasat", "Gilipolles"]


while True:
    insultRandom = random.choice(insults)
    print(insultRandom)
    print(insult_queue.add_insult(insultRandom))
    #channel.basic_publish(exchange='', routing_key='hello', body=insultRandom)
    #print(" [x] Sent 'Hello World!'")
    time.sleep(5)
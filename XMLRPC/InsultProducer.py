# XMLRPC/InsultProducer.py

import xmlrpc.client
import random
import time

class InsultProducer:
    def __init__(self, queue_url='http://localhost:8000'):
        self.insult_queue = xmlrpc.client.ServerProxy(queue_url)
        self.insults = ["Burro", "Retrasat", "Gilipolles"]

    def send_insult(self, insult=None):
        insult = insult or random.choice(self.insults)
        print(f"Sending insult: {insult}")
        response = self.insult_queue.add_insult(insult)
        print(f"Response: {response}")
        return response

    def run(self):
        while True:
            self.send_insult()
            time.sleep(5)

# Genera insults (nous i repetits i els envia a una cua)
import redis
import time

class InsultProducer:
    def __init__(self, insults=None, delay=5):
        self.client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.queue_name = "insult_queue"
        self.insults = insults or ["tonto", "capgros", "iec"]
        self.delay = delay

    def run(self, insult=None):
        # Si es passa un insult, l'afegeix a la llista; si no, utilitza la llista per defecte
        insults_to_send = [insult] if insult else self.insults
        for insult in insults_to_send:
            self.client.rpush(self.queue_name, insult)
            print(f"Produced: {insult}")
            time.sleep(self.delay)

if __name__ == "__main__":
    InsultProducer().run()
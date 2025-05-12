# Llegeix insults de la cua de InsultProducer i els afegeix a la llista d'insults existents si no existien
import redis

class InsultConsumer:
    def __init__(self):
        self.client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.queue_name = "insult_queue"
        self.existingInsults = "INSULTS"

    def run(self):
        print("Consumer is waiting for insults...")
        while True:
            inInsult = self.client.blpop(self.queue_name, timeout=0)
            if inInsult:
                if inInsult[1] not in self.client.lrange(self.existingInsults, 0, -1):
                    self.client.lpush(self.existingInsults, inInsult[1])
                    print(f"Insult {inInsult[1]} afegit")

if __name__ == "__main__":
    InsultConsumer().run()

# Fa broadcast de la llista d'insults existents
import redis
import time
# Connect to Redis
client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
channel_name = "insult_channel"
# Publish multiple messages
messages = ["Hola", "asd"]
for message in messages:
    client.publish(channel_name, message)
    print(f"Published: {message}")
    time.sleep(5) # Simulating delay between messages

import redis
import time

class InsultBroadcaster:
    def __init__(self, channel_name="insult_channel", insults=None, delay=5):
        self.client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.channel_name = channel_name
        self.insults = insults or ["Hola", "asd"]
        self.delay = delay

    def broadcast(self):
        for insult in self.insults:
            self.client.publish(self.channel_name, insult)
            print(f"Published: {insult}")
            time.sleep(self.delay)

if __name__ == "__main__":
    InsultBroadcaster().broadcast()

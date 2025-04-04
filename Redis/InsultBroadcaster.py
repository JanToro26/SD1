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
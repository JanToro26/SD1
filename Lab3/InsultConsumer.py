import redis
# Connect to Redis
client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
queue_name = "insult_queue"
existingInsults = "INSULTS"
print("Consumer is waiting for insults...")
while True:
    inInsult = client.blpop(queue_name, timeout=0) # Blocks indefinitely until an insult is available  
    if inInsult:
        if inInsult[1] not in client.lrange(existingInsults, 0, 1):
            client.lpush(inInsult[1], existingInsults)
            print(f"Insult {inInsult[1]} afegit")
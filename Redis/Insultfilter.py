import redis
# Connect to Redis
client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
queue_name = "work_queue"
existingInsults = "INSULTS"
result = "RESULTS"
print("Consumer is waiting for text...")
while True:
    text = client.blpop(queue_name, timeout=0) # Blocks indefinitely until an insult is available  
    if text:
        print(f"Rebut: {text[1]}")
        lineWords = text[1].split(" ")
        for word in lineWords:
            if word in client.lrange(existingInsults, 0, 1):
                lineWords[lineWords.index(word)] = 'CENSORED'
        lineWords = " ".join(lineWords)
        client.rpush(result, lineWords)
        print(f"Sortida: {lineWords}")
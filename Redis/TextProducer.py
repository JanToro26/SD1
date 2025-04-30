import redis
import time
# Connect to Redis
client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
queue_name = "work_queue"
# Send multiple messages
tasks = ["Hola com vas", "Que tal"]
for task in tasks:
    client.rpush(queue_name, task)
    print(f"Produced: {task}")
    time.sleep(5) # Simulating a delay in task production
import redis
import time

class TextProducer:
    def __init__(self, texts=None, delay=3):
        self.client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.queue_name = "work_queue"
        self.texts = texts or ["Hola com vas tonto", "Que tal capgros"]
        self.delay = delay

    def run(self):
        for task in self.texts:
            self.client.rpush(self.queue_name, task)
            print(f"Produced: {task}")
            time.sleep(self.delay)

if __name__ == "__main__":
    TextProducer().run()

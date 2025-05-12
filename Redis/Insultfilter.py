import redis

class InsultFilter:
    def __init__(self):
        self.client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        self.queue_name = "work_queue"
        self.existingInsults = "INSULTS"
        self.result = "RESULTS"

    def run(self):
        print("Filter waiting for text...")
        while True:
            #if not text: 
            text = self.client.blpop(self.queue_name, timeout=0)
            if text:
                print(f"Rebut: {text[1]}")
                lineWords = text[1].split(" ")
                insults_list = self.client.lrange(self.existingInsults, 0, -1)

                for i, word in enumerate(lineWords):
                    if word in insults_list:
                        lineWords[i] = 'CENSORED'

                output = " ".join(lineWords)
                self.client.rpush(self.result, output)
                print(f"Sortida: {output}")

if __name__ == "__main__":
    InsultFilter().run()



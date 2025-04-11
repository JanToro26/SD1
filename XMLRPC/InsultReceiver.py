import xmlrpc.client
import time

server = xmlrpc.client.ServerProxy('http://localhost:8001')

last_index = 0

while True:
    insults, new_index = server.get_insults_since(last_index)

    for insult in insults:
        print(f"Rebut nou insult: {insult}")

    last_index = new_index
    time.sleep(5)

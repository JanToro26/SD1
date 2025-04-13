import Pyro4
import random
import time

# Connexió al Name Server de Pyro4
ns = Pyro4.locateNS(host='localhost')  # canvia 'localhost' per IP si cal
uri = ns.lookup("insult.broadcaster")  # el nom registrat al Name Server

# Obtenim el proxy remot
insult_queue = Pyro4.Proxy(uri)

# Bucle d'enviament
last_index = 0
while True:
    insults, new_index = insult_queue.get_insults_since(last_index)
    for insult in insults:
        print(f"Rebut nou insult: {insult}")
    last_index = new_index
    time.sleep(5)


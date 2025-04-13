import Pyro4
import random
import time

# Connexió al Name Server de Pyro4
ns = Pyro4.locateNS(host='localhost')  # canvia 'localhost' per IP si cal
uri = ns.lookup("insult.consumer")  # el nom registrat al Name Server

# Obtenim el proxy remot
insult_queue = Pyro4.Proxy(uri)

# Insults a enviar
insults = ["Burro", "Retrasat", "Gilipolles"]

# Bucle d'enviament
while True:
    insultRandom = random.choice(insults)
    print(insultRandom)
    print(insult_queue.add_insult(insultRandom))  # Crida remota
    time.sleep(5)

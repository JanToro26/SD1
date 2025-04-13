import Pyro4
import random
import time

# Connexió al Name Server de Pyro4
ns = Pyro4.locateNS(host='localhost')  # canvia 'localhost' per IP si cal
uri = ns.lookup("filter.service")  # el nom registrat al Name Server

# Obtenim el proxy remot
insult_queue = Pyro4.Proxy(uri)

# Insults a enviar
texts = ["Genis puto amo", "Jan Retrasat", "Puto Gilipolles"]

# Bucle d'enviament
while True:
    insultRandom = random.choice(texts)
    print(insult_queue.filtrar(insultRandom))  # Crida remota
    time.sleep(5)
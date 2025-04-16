import Pyro4
import threading
import time
import xmlrpc.client
import random


# Connexió al Name Server de Pyro4
ns = Pyro4.locateNS(host='localhost')  # canvia 'localhost' per IP si cal
uri = ns.lookup("insult.broadcaster")  # el nom registrat al Name Server

# Obtenim el proxy remot
broadcaster = Pyro4.Proxy(uri)

insult_list = []
filtered_list = []
last_index = 0
lock = threading.Lock()



@Pyro4.expose
class FilterService:
    def filtrar(self, text):
        with lock:
            insults = insult_list.copy()

        paraules = text.split(" ")
        for i, paraula in enumerate(paraules):
            if paraula in insults:
                paraules[i] = "CENSORED"
        text_filtrat = " ".join(paraules)
        filtered_list.append(text_filtrat)
        return text_filtrat

    def get_all_filtered(self):
        with lock:
            return filtered_list.copy()


def actualitzar_insults():
    global last_index, insult_list
    
    while True:
        nous_insults, last_index = broadcaster.get_insults_since(last_index)
        if nous_insults:
            with lock:
                insult_list.extend(nous_insults)
            print(f"[Actualitzat] Nous insults: {nous_insults}")
        time.sleep(1)



def main():
    threading.Thread(target=actualitzar_insults, daemon=True).start()

    daemon = Pyro4.Daemon()
    ns = Pyro4.locateNS()
    uri = daemon.register(FilterService())
    ns.register("filter.service", uri)
    daemon.requestLoop()

if __name__ == "__main__":
    main()

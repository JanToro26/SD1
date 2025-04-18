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
    def __init__(self):
        pass
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
    
    def get_all_insults(self):
        with lock:
            return insult_list
    
    def notify(self, insult):
        with lock:
            insult_list.append(insult)

def main():
    filter_service = FilterService()
    

    daemon = Pyro4.Daemon()
    ns = Pyro4.locateNS()
    uri = daemon.register(filter_service)
    ns.register("filter.service", uri)
    broadcaster.subscribe(filter_service)
    daemon.requestLoop()

if __name__ == "__main__":
    main()

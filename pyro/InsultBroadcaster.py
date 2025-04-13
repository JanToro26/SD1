import Pyro4
import random

# Habilita l'exposició explícita
Pyro4.config.REQUIRE_EXPOSE = True

@Pyro4.expose
class InsultManager:
    def __init__(self):
        self.insult_list = []

    def add_insult(self, insult):
        self.insult_list.append(insult)
        return f"L'insult {insult} ha estat afegit."

    def get_insults(self):
        return self.insult_list if self.insult_list else []

    def get_insults_since(self, index):
        return self.insult_list[index:], len(self.insult_list)

    def insult_me(self):
        if not self.insult_list:
            return "No hi ha insults encara!"
        return random.choice(self.insult_list)


if __name__ == "__main__":
    # Crea el daemon i registra l'objecte remot
    daemon = Pyro4.Daemon()  
    ns = Pyro4.locateNS()  # Connecta al Name Server de Pyro
    uri = daemon.register(InsultManager())  # Registra la instància de la classe
    ns.register("insult.broadcaster", uri)  # Dona-li un nom per trobar-lo fàcilment

    #print("Servidor Pyro4 llest. URI:", uri)
    daemon.requestLoop()

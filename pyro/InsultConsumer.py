# servidor_pyro.py
import Pyro4
import random

# Expose this class for remote use
@Pyro4.expose
class InsultService:
    def __init__(self):
        self.broadcaster = Pyro4.Proxy("PYRONAME:insult.broadcaster")

    def add_insult(self, insult):
        insult_list = self.broadcaster.get_insults()
        if insult not in insult_list:
            self.broadcaster.add_insult(insult)
            return f"L'insult {insult} s'ha afegit a la llista correctament"
        else:
            return f"L'insult {insult} ja està a la llista"

    def get_insults(self):
        return self.broadcaster.get_insults()

    def insult_me(self):
        insults = self.broadcaster.get_insults()
        if insults:
            return random.choice(insults)
        else:
            return "No hi ha insults!"

# Inici del servidor Pyro
if __name__ == "__main__":
    Pyro4.config.REQUIRE_EXPOSE = True
    daemon = Pyro4.Daemon()
    ns = Pyro4.locateNS()
    uri = daemon.register(InsultService())
    ns.register("insult.consumer", uri)
    #print("Servidor Pyro registrat com a 'insult.consumer'")
    daemon.requestLoop()

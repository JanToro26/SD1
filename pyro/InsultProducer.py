import Pyro4
import random
import time

class InsultProducer:
    def __init__(self):
        # Connexió al Name Server de Pyro4
        self.consumer = Pyro4.Proxy("PYRONAME:insult.consumer")
        self.insults = ["Burro", "Retrasat", "Gilipolles"]

    def send_random_insult(self):
        """Envia un insult aleatori a la cua"""
        insult_random = random.choice(self.insults)
        return self.consumer.add_insult(insult_random)

    def start_sending_insults(self, interval=5):
        """Envia insults de forma contínua amb un interval"""
        while True:
            self.send_random_insult()
            time.sleep(interval)
    @Pyro4.expose
    def send_insult(self, insult):
        return self.consumer.add_insult(insult)


if __name__ == "__main__":
    Pyro4.config.REQUIRE_EXPOSE = True
    daemon = Pyro4.Daemon()
    ns = Pyro4.locateNS()
    uri = daemon.register(InsultProducer())
    ns.register("insult.producer", uri)
    #print("Servidor Pyro registrat com a 'insult.consumer'")
    daemon.requestLoop()

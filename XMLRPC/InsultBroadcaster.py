# XMLRPC/InsultBroadcaster.py

from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import xmlrpc.client
import random

class InsultBroadcaster:
    def __init__(self, host='localhost', port=8001):
        self.host = host
        self.port = port
        self.insult_list = []
        self.subscribers = []

    def add_insult(self, insult):
        self.insult_list.append(insult)
        print(f"Insult afegit: {insult}")
        for url in self.subscribers:
            try:
                proxy = xmlrpc.client.ServerProxy(url)
                proxy.notify(insult)
            except Exception as e:
                print(f"Error notificando a {url}: {e}")
        return f"L'insult {insult} ha estat afegit."

    def get_insults(self):
        return self.insult_list if self.insult_list else []

    def get_insults_since(self, index):
        print(f"Agafant insults desde el index: {index}")
        return self.insult_list[index:], len(self.insult_list)

    def insult_me(self):
        if not self.insult_list:
            return "Encara no hi ha insults"
        return random.choice(self.insult_list)
    
    def subscribe(self, callback_url):
        print(callback_url)
        self.subscribers.append(callback_url)

    def run(self):
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)

        with SimpleXMLRPCServer((self.host, self.port), requestHandler=RequestHandler, allow_none=True) as server:
            server.register_introspection_functions()

            server.register_function(self.add_insult, 'add_insult')
            server.register_function(self.get_insults, 'get_insults')
            server.register_function(self.get_insults_since, 'get_insults_since')
            server.register_function(self.insult_me, 'insult_me')
            server.register_function(self.subscribe, 'subscribe' )

            server.serve_forever()

if __name__ == "__main__":
    broadcaster = InsultBroadcaster()
    broadcaster.run()

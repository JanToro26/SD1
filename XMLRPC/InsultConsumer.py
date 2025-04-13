# XMLRPC/InsultConsumer.py

from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import xmlrpc.client
import random

class InsultConsumer:
    def __init__(self, host='localhost', port=8000, broadcaster_url='http://localhost:8001'):
        self.host = host
        self.port = port
        self.broadcaster = xmlrpc.client.ServerProxy(broadcaster_url)

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
        insult_list = self.broadcaster.get_insults()
        if not insult_list:
            return "No insults available"
        return random.choice(insult_list)

    def run(self):
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)

        with SimpleXMLRPCServer((self.host, self.port), requestHandler=RequestHandler, allow_none=True) as server:
            server.register_introspection_functions()

            server.register_function(self.add_insult, 'add_insult')
            server.register_function(self.get_insults, 'get_insults')
            server.register_function(self.insult_me, 'insult_me')

            print(f"InsultReceiver running on {self.host}:{self.port}")
            server.serve_forever()

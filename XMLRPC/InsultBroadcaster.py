# XMLRPC/InsultBroadcaster.py

from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import random

class InsultBroadcaster:
    def __init__(self, host='localhost', port=8001):
        self.host = host
        self.port = port
        self.insult_list = []

    def add_insult(self, insult):
        self.insult_list.append(insult)
        print(f"Insult added: {insult}")
        return f"L'insult {insult} ha estat afegit."

    def get_insults(self):
        return self.insult_list if self.insult_list else []

    def get_insults_since(self, index):
        print(f"Fetching insults since index: {index}")
        return self.insult_list[index:], len(self.insult_list)

    def insult_me(self):
        if not self.insult_list:
            return "No insults available"
        return random.choice(self.insult_list)

    def run(self):
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)

        with SimpleXMLRPCServer((self.host, self.port), requestHandler=RequestHandler, allow_none=True) as server:
            server.register_introspection_functions()

            server.register_function(self.add_insult, 'add_insult')
            server.register_function(self.get_insults, 'get_insults')
            server.register_function(self.get_insults_since, 'get_insults_since')
            server.register_function(self.insult_me, 'insult_me')

            print(f"InsultBroadcaster running on {self.host}:{self.port}")
            server.serve_forever()

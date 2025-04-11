from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import xmlrpc.client 
import random

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

with SimpleXMLRPCServer(('localhost', 8000), requestHandler=RequestHandler) as server:
    server.register_introspection_functions()
    broadcaster = xmlrpc.client.ServerProxy('http://localhost:8001')
    insult_list = []

    def add_insult(insult):
        
        insult_list= broadcaster.get_insults()

        if insult not in insult_list:
            broadcaster.add_insult(insult)
            return f"L'insult {insult} s'ha afegit a la llista correctament"
        else:
            return f"L'insult {insult} ja està a la llista"


    server.register_function(add_insult,'add_insult') 

    def get_insults():
        insult_list= broadcaster.get_insults()
        return insult_list
    server.register_function(get_insults, 'get_insults') 
    
    def insult_me():
        insult_list= broadcaster.get_insults()
        return insult_list[random.randint(0, len(insult_list) - 1)] 
    server.register_function(insult_me, 'insult_me') 

    server.serve_forever()
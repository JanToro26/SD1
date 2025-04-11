from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import xmlrpc.client 
import random

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

with SimpleXMLRPCServer(('localhost', 8001), requestHandler=RequestHandler) as server:
    server.register_introspection_functions()
    #broadcaster = xmlrpc.client.ServerProxy('http://localhost:8001')
    insult_list = []
    

    def add_insult(insult):
        insult_list.append(insult)
        print(insult)
        return f"L'insult {insult} ha estat afegit."


    server.register_function(add_insult,'add_insult') 

    def get_insults():
        return insult_list if insult_list else []  # Si no hay insultos, devuelve una lista vacía

    server.register_function(get_insults, 'get_insults') 

    #Necessari al no ser un model de Publicador/Subscriptor
    def get_insults_since(index):
        print(index)
        #Retorna els insults a partir de quin li passes
        #Ens serveix per a que el subscriptor tingui els insults nous
        return insult_list[index:], len(insult_list)
    server.register_function(get_insults_since, 'get_insults_since') 
    
    #No sé si s'ha de borrar
    def insult_me():
        return insult_list[random.randint(0, len(insult_list) - 1)] 
    server.register_function(insult_me, 'insult_me') 

    server.serve_forever()
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import random

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

with SimpleXMLRPCServer(('localhost', 8000), requestHandler=RequestHandler) as server:
    server.register_introspection_functions()
    insult_list=[]

    def add_insult(insult):
        insult_list.append(insult)

    server.register_function(add_insult,'add_insult') 

    def get_insults():
        return insult_list
    server.register_function(get_insults, 'get_insults') 
    
    def insult_me():
        return insult_list[random.randint(0, len(insult_list) - 1)] 
    server.register_function(insult_me, 'insult_me') 

    server.serve_forever()
import xmlrpc.client 
import random

s = xmlrpc.client.ServerProxy('http://localhost:8000')

print(s.add_insult('janburro'))
print(s.get_insults())

print(s.system.listMethods())
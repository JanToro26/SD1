from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import xmlrpc.client
import threading
import time

# Connexió al broadcaster, port 8001
broadcaster = xmlrpc.client.ServerProxy('http://localhost:8001')

# Llista local d’insults
insult_list = []
filtered_list = []
last_index = 0
lock = threading.Lock()

# ============================
# ACTUALITZADOR EN SEGON PLA
# ============================
def actualitzar_insults():
    global last_index, insult_list
    while True:
        nous_insults, last_index = broadcaster.get_insults_since(last_index)
        if nous_insults:
            with lock:
                insult_list.extend(nous_insults)
            print(f"[Actualitzat] Nous insults: {nous_insults}")
        time.sleep(1)

# ============================
# FUNCIÓ FILTRAR
# ============================
def filtrar(text):
    with lock:
        insults = insult_list.copy()

    paraules = text.split(" ")
    for i, paraula in enumerate(paraules):
        if paraula in insults:
            paraules[i] = "CENSORED"
        text_filtrat = " ".join(paraules)
        filtered_list.append(text_filtrat)
    return text_filtrat

# ============================
# FUNCIÓ RETORNAR TEXT FILTRAT
# ============================

def get_all_filtered():
    with lock:
        return filtered_list


# ============================
# SERVIDOR XML-RPC
# ============================
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

with SimpleXMLRPCServer(("localhost", 8002), requestHandler=RequestHandler, allow_none=True) as server:
    server.register_introspection_functions()

    # Registra la funció que es podrà cridar remotament
    server.register_function(filtrar, 'filtrar')
    server.register_function(get_all_filtered, 'get_all_filtered')

    # Inicia el fil d’actualització
    threading.Thread(target=actualitzar_insults, daemon=True).start()

    server.serve_forever()

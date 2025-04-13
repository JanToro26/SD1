from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import xmlrpc.client
import threading
import time
import socket

# ============================
# Configuración inicial
# ============================

BROADCASTER_HOST = 'localhost'
BROADCASTER_PORT = 8001
BROADCASTER_URL = f'http://{BROADCASTER_HOST}:{BROADCASTER_PORT}/RPC2'

# Connexió al broadcaster
broadcaster = xmlrpc.client.ServerProxy(BROADCASTER_URL)

# Llistes locals
insult_list = []
filtered_list = []
last_index = 0
lock = threading.Lock()

# ============================
# Utilidad: Esperar Broadcaster
# ============================

def wait_for_broadcaster(port=BROADCASTER_PORT, host='localhost', timeout=10.0):
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                print(f"✅ Broadcaster disponible en {host}:{port}")
                return
        except OSError:
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timeout esperando al Broadcaster en {host}:{port}")

# ============================
# ACTUALIZADOR EN SEGUNDO PLANO
# ============================

def actualitzar_insults():
    global last_index, insult_list

    # Esperamos activamente que el Broadcaster esté disponible
    wait_for_broadcaster()

    while True:
        try:
            nous_insults, last_index = broadcaster.get_insults_since(last_index)
            if nous_insults:
                with lock:
                    insult_list.extend(nous_insults)
                print(f"[Actualitzat] Nous insults: {nous_insults}")
        except Exception as e:
            print(f"⚠️ Error al actualitzar insults: {e}")
        time.sleep(1)

# ============================
# FUNCIÓN FILTRAR
# ============================

def filtrar(text):
    with lock:
        insults = insult_list.copy()

    paraules = text.split(" ")
    for i, paraula in enumerate(paraules):
        if paraula in insults:
            paraules[i] = "CENSORED"

    text_filtrat = " ".join(paraules)
    with lock:
        filtered_list.append(text_filtrat)
    return text_filtrat

# ============================
# FUNCIÓN RETORNAR TEXTOS FILTRADOS
# ============================

def get_all_filtered():
    with lock:
        return filtered_list

# ============================
# SERVIDOR XML-RPC
# ============================

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

def run_server():
    with SimpleXMLRPCServer(("localhost", 8002), requestHandler=RequestHandler, allow_none=True) as server:
        server.register_introspection_functions()

        # Registramos funciones remotas
        server.register_function(filtrar, 'filtrar')
        server.register_function(get_all_filtered, 'get_all_filtered')

        # Inicia el hilo de actualización
        threading.Thread(target=actualitzar_insults, daemon=True).start()

        print("✅ Servidor InsultFilter en marcha en puerto 8002")
        server.serve_forever()

# Permite que se pueda ejecutar como script directamente
if __name__ == "__main__":
    run_server()

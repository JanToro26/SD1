from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import xmlrpc.client
import threading
import time
import socket

class InsultFilter:
    def __init__(self, broadcaster_url='http://localhost:8001', host='localhost', port=8002):
        self.host = host
        self.port = port
        self.broadcaster_url = broadcaster_url

        # Conexió al broadcaster
        self.broadcaster = xmlrpc.client.ServerProxy(self.broadcaster_url)

        # Llistes i variables locals
        self.insult_list = []
        self.filtered_list = []
        self.lock = threading.Lock()    # Necessària per al sincronisme

    # Sincronización para esperar a que el broadcaster esté disponible
    def wait_for_broadcaster(self, port=8001, host='localhost', timeout=10.0):
        start_time = time.time()
        while True:
            try:
                with socket.create_connection((host, port), timeout=0.5):
                    print(f"Broadcaster disponible a {host}:{port}")
                    return
            except OSError:
                time.sleep(0.1)
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Timeout esperant al Broadcaster en {host}:{port}")

    def notify(self, insult):
        with self.lock:
            self.insult_list.append(insult)
        print(f"[Notificació rebuda] Nou insult: {insult} - Insults actuals: {self.insult_list}")
        return f"Insult rebut: {insult}"

    def filtrar(self, text):
        with self.lock:
            insults = self.insult_list.copy()

        words = text.split(" ")
        for i, word in enumerate(words):
            if word in insults:
                words[i] = "CENSORED"

        filtered_text = " ".join(words)
        with self.lock:
            self.filtered_list.append(filtered_text)
        return filtered_text

    def get_all_filtered(self):
        with self.lock:
            return self.filtered_list
    
    def get_all_insults(self):
        with self.lock:
            return self.insult_list

    def run(self):
        # Construir l'URL públic d'aquest filtre
        callback_url = f'http://{self.host}:{self.port}'

        # Subscriure al broadcaster
        try:
            self.broadcaster.subscribe(callback_url)
            print(f"Subscrits al broadcaster com a: {callback_url}")
        except Exception as e:
            print(f"Error al subscriure's al broadcaster: {e}")
        
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)

        with SimpleXMLRPCServer((self.host, self.port), requestHandler=RequestHandler, allow_none=True) as server:
            server.register_introspection_functions()

            # Registrar las funciones del servidor
            server.register_function(self.filtrar, 'filtrar')
            server.register_function(self.get_all_filtered, 'get_all_filtered')
            server.register_function(self.notify, 'notify')
            server.register_function(self.get_all_insults, 'get_all_insults')

            server.serve_forever()

if __name__ == "__main__":
    broadcaster = InsultFilter()
    broadcaster.run()
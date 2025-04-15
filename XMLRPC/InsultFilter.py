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
        self.last_index = 0
        self.lock = threading.Lock()    #Necessària per al sincronisme i que no es solapin els processos i peticions.
    

    #Mirar si el broadcaster està disponible
    def wait_for_broadcaster(self, port=8001, host='localhost', timeout=10.0):
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

    def actualitzar_insults(self, max_duration=10):
        """Actualiza la lista de insultos desde el Broadcaster por un tiempo máximo."""
        self.wait_for_broadcaster()
        
        start_time = time.time()
        
        while time.time() - start_time < max_duration:  # Limitar la duración de la actualización
            try:
                new_insults, self.last_index = self.broadcaster.get_insults_since(self.last_index)
                if new_insults:
                    with self.lock:
                        self.insult_list.extend(new_insults)
                    print(f"[Actualitzat] Nous insults: {new_insults}")
            except Exception as e:
                print(f"⚠️ Error al actualitzar insults: {e}")
            time.sleep(1)

        print("🛑 Fin de la actualización de insultos.")
    
    #Funció que filtra
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

    def run(self):
        # Inicia el thread d'actualització periòdica
        threading.Thread(target=self.actualitzar_insults, daemon=True).start()

        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)

        with SimpleXMLRPCServer((self.host, self.port), requestHandler=RequestHandler, allow_none=True) as server:
            server.register_introspection_functions()

            # Registrem les funcions del servidor
            server.register_function(self.filtrar, 'filtrar')
            server.register_function(self.get_all_filtered, 'get_all_filtered')

            server.serve_forever()


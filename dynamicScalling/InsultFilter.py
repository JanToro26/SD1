import pika
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import threading

class InsultFilter:
    def __init__(self, host='localhost', port=8002):
        self.host = host
        self.port = port
        self.insult_list = []
        self.filtered_list = []
        self.lock = threading.Lock()

        # Conexión a RabbitMQ
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', port=5672))
        self.channel = self.connection.channel()

        # Declara la cola para los insultos
        self.channel.queue_declare(queue='insult_channel')

    def callback(self, ch, method, properties, body):
        """Recibe los insultos desde RabbitMQ y los agrega a la lista"""
        insult = body.decode()
        print(f"[Filter] Recibido insulto: {insult}")
        self.insult_list.append(insult)

    def filtrar(self, text):
        """Filtra los insultos en el texto"""
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
        """Devuelve todos los textos filtrados"""
        with self.lock:
            return self.filtered_list

    def get_all_insults(self):
        """Devuelve todos los insultos almacenados"""
        with self.lock:
            return self.insult_list

    def run(self):
        """Inicia el consumidor de RabbitMQ y el servidor XML-RPC en hilos separados"""
        # Iniciar el hilo de RabbitMQ para escuchar los insultos
        rabbitmq_thread = threading.Thread(target=self.listen_rabbitmq)
        rabbitmq_thread.start()

        # Iniciar el servidor XML-RPC
        self.start_xmlrpc_server()

    def listen_rabbitmq(self):
        """Escuchar los insultos de RabbitMQ"""
        self.channel.basic_consume(queue='insult_channel', on_message_callback=self.callback, auto_ack=True)
        print("[Filter] Esperando insultos de RabbitMQ...")
        self.channel.start_consuming()

    def start_xmlrpc_server(self):
        """Inicia el servidor XML-RPC para el filtro"""
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)

        with SimpleXMLRPCServer((self.host, self.port), requestHandler=RequestHandler, allow_none=True) as server:
            server.register_introspection_functions()
            server.register_function(self.filtrar, 'filtrar')
            server.register_function(self.get_all_filtered, 'get_all_filtered')
            server.register_function(self.get_all_insults, 'get_all_insults')

            print("[Filter] Iniciando servidor XML-RPC...")
            server.serve_forever()

if __name__ == "__main__":
    filter_service = InsultFilter()
    filter_service.run()

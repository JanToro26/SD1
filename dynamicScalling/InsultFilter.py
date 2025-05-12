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
        self.channel.queue_declare(queue='insult_channel')

    def callback(self, ch, method, properties, body):
        """Recibe los insultos desde RabbitMQ y los agrega a la lista"""
        insult = body.decode()
        print(f"[Filter] Recibido insulto: {insult}")
        self.insult_list.append(insult)

    def filtrar(self, text):
        """Filtra los insults en el text"""
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
        """Retorna tots els textos filtrats"""
        with self.lock:
            return self.filtered_list

    def get_all_insults(self):
        """Retorna tots els insults emmagatzemats"""
        with self.lock:
            return self.insult_list

    def run(self):
        """Inicia el consumidor de RabbitMQ y el servidor XML-RPC en fils separados"""
        # Iniciar el fil de RabbitMQ para escoltar los insults
        rabbitmq_thread = threading.Thread(target=self.listen_rabbitmq)
        rabbitmq_thread.start()

        # Iniciar el servidor XML-RPC
        self.start_xmlrpc_server()

    def listen_rabbitmq(self):
        self.channel.basic_consume(queue='insult_channel', on_message_callback=self.callback, auto_ack=True)
        print("[Filter] Esperant insults de RabbitMQ...")
        self.channel.start_consuming()

    def start_xmlrpc_server(self):
        """Inicia el servidor XML-RPC pel filtro"""
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)

        with SimpleXMLRPCServer((self.host, self.port), requestHandler=RequestHandler, allow_none=True) as server:
            server.register_introspection_functions()
            server.register_function(self.filtrar, 'filtrar')
            server.register_function(self.get_all_filtered, 'get_all_filtered')
            server.register_function(self.get_all_insults, 'get_all_insults')

            print("[Filter] Iniciant servidor XML-RPC...")
            server.serve_forever()

if __name__ == "__main__":
    filter_service = InsultFilter()
    filter_service.run()

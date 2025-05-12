import pika
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

class InsultBroadcaster:
    def __init__(self, host='localhost', port=5672, xmlrpc_host='localhost', xmlrpc_port=8001):
        self.host = host
        self.port = port
        self.xmlrpc_host = xmlrpc_host
        self.xmlrpc_port = xmlrpc_port
        
        # Connexió i cua de RabbitMQ
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.port))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='insult_channel')

        # Lista de insults
        self.insult_list = []

    def add_insult(self, insult):
        """Afegeix un insult a la lista y lo envía a los consumidors a través de RabbitMQ"""
        self.insult_list.append(insult)
        print(f"[Broadcaster] Insulto añadido: {insult}")

        # Publica el insult a la cola
        self.channel.basic_publish(exchange='',
                                  routing_key='insult_channel',
                                  body=insult)
        print(f"[Broadcaster] Insult enviat a la cua de RabbitMQ: {insult}")
        return f"L'insult {insult} ha estat afegit."

    def get_insults(self):
        """Retorna la lista de insults"""
        return self.insult_list if self.insult_list else []

    def run(self):
        """Inicia el servei del broadcaster que escoltarà peticions XML-RPC"""
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)

        with SimpleXMLRPCServer((self.xmlrpc_host, self.xmlrpc_port), requestHandler=RequestHandler, allow_none=True) as server:
            server.register_introspection_functions()

            server.register_function(self.add_insult, 'add_insult')
            server.register_function(self.get_insults, 'get_insults')

            print(f"[Broadcaster] Servidor XML-RPC iniciado en {self.xmlrpc_host}:{self.xmlrpc_port}")
            server.serve_forever()

if __name__ == "__main__":
    broadcaster = InsultBroadcaster()
    broadcaster.run()

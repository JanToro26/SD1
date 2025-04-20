import pika
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

class InsultBroadcaster:
    def __init__(self, host='localhost', port=5672):
        self.host = host
        self.port = port
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.port))
        self.channel = self.connection.channel()

        # Declara la cola para los insultos
        self.channel.queue_declare(queue='insult_channel')

        # Lista de insultos
        self.insult_list = []

    def add_insult(self, insult):
        """Añade un insulto a la lista y lo envía a los consumidores a través de RabbitMQ"""
        self.insult_list.append(insult)
        print(f"[Broadcaster] Insulto añadido: {insult}")

        # Enviar el insulto a la cola
        self.channel.basic_publish(exchange='',
                                  routing_key='insult_channel',
                                  body=insult)
        print(f"[Broadcaster] Insulto enviado a la cola de RabbitMQ: {insult}")
        return f"L'insult {insult} ha estat afegit."

    def get_insults(self):
        """Devuelve la lista de insultos"""
        return self.insult_list if self.insult_list else []

    def run(self):
        """Inicia el servicio del broadcaster"""
        class RequestHandler(SimpleXMLRPCRequestHandler):
            rpc_paths = ('/RPC2',)

        with SimpleXMLRPCServer((self.host, 8001), requestHandler=RequestHandler, allow_none=True) as server:
            server.register_introspection_functions()

            server.register_function(self.add_insult, 'add_insult')
            server.register_function(self.get_insults, 'get_insults')

            server.serve_forever()

if __name__ == "__main__":
    broadcaster = InsultBroadcaster()
    broadcaster.run()

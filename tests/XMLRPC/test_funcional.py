import pytest
import os, sys
import socket
from multiprocessing import Process
from xmlrpc.client import ServerProxy

# Agregamos al path el directorio raíz del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from XMLRPC import InsultProducer, InsultConsumer, InsultBroadcaster

def start_broadcaster():
    broadcaster = InsultBroadcaster.InsultBroadcaster()
    broadcaster.run()

def start_receiver():
    receiver = InsultConsumer.InsultConsumer()
    receiver.run()

def wait_for_port(port, host='localhost', timeout=5.0):
    """Función para esperar activamente a que un puerto esté abierto."""
    import time
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timeout waiting for port {port} on host {host}")

@pytest.fixture(scope="module", autouse=True)
def setup_services():
    # Arrancamos Broadcaster primero
    broadcaster_process = Process(target=start_broadcaster)
    broadcaster_process.start()

    # Esperamos que el puerto 8001 esté abierto antes de continuar
    wait_for_port(8001)

    # Ahora arrancamos el Receiver, que depende del Broadcaster
    receiver_process = Process(target=start_receiver)
    receiver_process.start()

    # Esperamos que el puerto 8000 también esté abierto
    wait_for_port(8000)

    yield

    # Terminamos los procesos después del test
    for process in (broadcaster_process, receiver_process):
        process.terminate()
        process.join()

def test_producer_to_broadcaster():
    # Creamos el producer manualmente
    producer = InsultProducer.InsultProducer()

    # Lista de insultos de prueba que vamos a enviar
    test_insults = ["InsultTest1", "InsultTest2", "InsultTest3"]

    # Enviamos cada insulto y verificamos la respuesta del receiver
    for insult in test_insults:
        response = producer.send_insult(insult)
        assert f"L'insult {insult} s'ha afegit a la llista correctament" in response or \
               f"L'insult {insult} ja està a la llista" in response
        print(f"✅ Enviado insulto '{insult}' al Receiver correctamente")

    # Esperamos un poco para asegurarnos que el receiver haya procesado los insultos
    import time
    time.sleep(1)

    # Verificamos que todos los insultos estén en la lista del Broadcaster
    broadcaster_client = ServerProxy("http://localhost:8001/RPC2")
    insults_in_broadcaster = broadcaster_client.get_insults()

    for insult in test_insults:
        assert insult in insults_in_broadcaster, f"❌ El insulto '{insult}' no se encontró en el Broadcaster"
        print(f"✅ Insulto '{insult}' encontrado en el Broadcaster")

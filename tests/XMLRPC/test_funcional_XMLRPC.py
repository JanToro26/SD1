import pytest
import os
import sys
import socket
import time
from multiprocessing import Process
from xmlrpc.client import ServerProxy

# Agregamos al path el directorio raíz del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from XMLRPC import InsultProducer, InsultConsumer, InsultBroadcaster, InsultFilter

# ================================
# Configuració base
# ================================

BROADCASTER_URL = "http://localhost:8001/RPC2"
RECEIVER_URL = "http://localhost:8000/RPC2"
FILTER_URL = "http://localhost:8002/RPC2"

# ================================
# Helpers
# ================================

def wait_for_port(port, host='localhost', timeout=5.0):
    start_time = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Timeout esperando al puerto {port} en host {host}")

def start_broadcaster():
    broadcaster = InsultBroadcaster.InsultBroadcaster()
    broadcaster.run()

def start_receiver():
    receiver = InsultConsumer.InsultConsumer()
    receiver.run()

def start_filter():
    filter = InsultFilter.InsultFilter()
    filter.run()

def listen_to_broadcaster(duration=5):
    server = ServerProxy(BROADCASTER_URL)
    last_index = 0
    received_insults = []

    start_time = time.time()
    while time.time() - start_time < duration:
        insults, new_index = server.get_insults_since(last_index)

        for insult in insults:
            print(f"👂 Rebut nou insult: {insult}")
            received_insults.append(insult)

        last_index = new_index
        time.sleep(1)

    return received_insults

# ================================
# Fixture de setup
# ================================

@pytest.fixture(scope="module", autouse=True)
def setup_services():
    processes = []

    # Broadcaster
    broadcaster_process = Process(target=start_broadcaster)
    broadcaster_process.start()
    processes.append(broadcaster_process)
    wait_for_port(8001)

    # Receiver
    receiver_process = Process(target=start_receiver)
    receiver_process.start()
    processes.append(receiver_process)
    wait_for_port(8000)

    # Filter service
    filter_process = Process(target=start_filter)
    filter_process.start()
    processes.append(filter_process)
    wait_for_port(8002)

    yield

    # Terminamos procesos
    for process in processes:
        process.terminate()
        process.join()

# ================================
# Tests
# ================================

def test_producer_to_broadcaster():
    """Verifica Producer → Consumer → Broadcaster."""
    producer = InsultProducer.InsultProducer()
    test_insults = ["InsultTest1", "InsultTest2", "InsultTest3"]

    for insult in test_insults:
        response = producer.send_insult(insult)
        assert f"L'insult {insult} s'ha afegit a la llista correctament" in response or \
               f"L'insult {insult} ja està a la llista" in response
        print(f"✅ Enviado insulto '{insult}' al Receiver correctamente")

    time.sleep(1)

    broadcaster_client = ServerProxy(BROADCASTER_URL)
    insults_in_broadcaster = broadcaster_client.get_insults()

    for insult in test_insults:
        assert insult in insults_in_broadcaster, f"❌ El insulto '{insult}' no se encontró en el Broadcaster"
        print(f"✅ Insulto '{insult}' encontrado en el Broadcaster")

def test_listener_receives_new_insults():
    """Verifica que el listener recibe insultos nuevos del Broadcaster."""
    producer = InsultProducer.InsultProducer()
    test_insults = ["ListenerTest1", "ListenerTest2"]

    for insult in test_insults:
        producer.send_insult(insult)
        print(f"🚀 Enviado insulto '{insult}' para listener")

    received_insults = listen_to_broadcaster(duration=3)

    for insult in test_insults:
        assert insult in received_insults, f"❌ El insulto '{insult}' no fue recibido por el listener"
        print(f"✅ Listener recibió insulto '{insult}' correctamente")

def test_filter_service_filters_text():
    """Verifica que el servicio Filter censura correctamente los insultos."""

    producer = InsultProducer.InsultProducer()
    test_insults = ["FiltreInsult", "puto"]  # Agregamos también 'puto'

    # Aseguramos que los insultos se envían
    for insult in test_insults:
        producer.send_insult(insult)
        print(f"🚀 Enviado insulto '{insult}' para el filtro")

    time.sleep(2)  # Tiempo para que el filtro actualice sus insultos desde el Broadcaster

    filter_client = ServerProxy(FILTER_URL)
    test_texts = ["Genis puto amo", f"Jan FiltreInsult", f"Puto FiltreInsult"]

    for text in test_texts:
        filtered_text = filter_client.filtrar(text)
        print(f"📝 Texto original: '{text}' ➡️ Filtrado: '{filtered_text}'")
        assert "CENSORED" in filtered_text, f"❌ El texto '{text}' no fue filtrado correctamente"

    # Verificamos que el filtro almacena los textos filtrados
    filtered_results = filter_client.get_all_filtered()
    for original in test_texts:
        assert any("CENSORED" in result for result in filtered_results), f"❌ No se encontró texto censurado en los resultados filtrados"

    print(f"✅ Textos filtrados almacenados correctamente")
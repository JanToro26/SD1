import pytest
import os
import sys
import socket
import time
from multiprocessing import Process
from xmlrpc.client import ServerProxy

# Ens movem pel projecte
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
                raise TimeoutError(f"Timeout esperant al port {port} en host {host}")
            

def start_broadcaster():
    broadcaster = InsultBroadcaster.InsultBroadcaster()
    broadcaster.run()

def start_receiver():
    receiver = InsultConsumer.InsultConsumer()
    receiver.run()

def start_filter():
    filter = InsultFilter.InsultFilter()
    filter.run()

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

    # Llimpiem tots els processos
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
               f"L'insult {insult} ja esta a la llista" in response
        print(f"L'insult '{insult}' s'ha enviat al Receiver correctament")

    time.sleep(1)

    broadcaster_client = ServerProxy(BROADCASTER_URL)
    insults_in_broadcaster = broadcaster_client.get_insults()

    for insult in test_insults:
        assert insult in insults_in_broadcaster, f"L'insult '{insult}' no s'ha trobat al broadcaster"
        print(f"L'insult '{insult}' s'ha trobat al broadcaster")

def test_listener_receives_new_insults():
    """Verifica que el listener rep insults nous del Broadcaster, mitjançant notificacions."""
    producer = InsultProducer.InsultProducer()
    test_insults = ["ListenerTest1", "ListenerTest2"]

    for insult in test_insults:
        producer.send_insult(insult)
        time.sleep(5)
        print(f"Enviat l'insult '{insult}' al listener")

    # Esperem un poc a que els insults siguin notificats als filters
    time.sleep(2)

    filter_client = ServerProxy(FILTER_URL)
    received_insults = filter_client.get_all_insults()
    print(received_insults)
    time.sleep(5)
    for insult in test_insults:
        assert any(insult in result for result in received_insults), f"L'insult '{insult}' no l'ha rebut listener"
        print(f"El listener ha rebut l'insult '{insult}' correctament")

def test_filter_service_filters_text():
    """Verifica que el servei Filter censura correctament els insults."""

    producer = InsultProducer.InsultProducer()
    test_insults = ["FiltreInsult", "puto"]  # Afegim insults al broadcaster

    # Liu enviem al broadcaster per a que els guardi
    for insult in test_insults:
        producer.send_insult(insult)
        print(f"Insult enviat '{insult}' al filtre")

    time.sleep(2)  # Ens esperem prudencialment per a que no es solapi o hi hagi errors

    filter_client = ServerProxy(FILTER_URL)
    test_texts = ["Genis puto amo", f"Jan FiltreInsult", f"Puto FiltreInsult"]

    for text in test_texts:
        filtered_text = filter_client.filtrar(text)
        print(f"Text original: '{text}' ➡️ Filtrat: '{filtered_text}'")
        assert "CENSORED" in filtered_text, f"El text '{text}' no s'ha filtrat correctament"

    # Verifiquem que el text es guarda en el filter com una "caché"
    filtered_results = filter_client.get_all_filtered()
    for original in test_texts:
        assert any("CENSORED" in result for result in filtered_results), f"No s'ha trobat el text censurat a la llista"

    print(f"Textos filtrats estan guardats correctament")

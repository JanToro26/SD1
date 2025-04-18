import pytest
import Pyro4
import time
from multiprocessing import Process
import os
import sys
import subprocess

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../pyro'))
sys.path.insert(0, BASE_DIR)

# ================================
# Helpers
# ================================

def start_broadcaster():
    path = os.path.join(BASE_DIR, "InsultBroadcaster.py")
    subprocess.Popen(["python3", path])

def start_receiver():
    path = os.path.join(BASE_DIR, "InsultConsumer.py")
    subprocess.Popen(["python3", path])

def start_filter():
    path = os.path.join(BASE_DIR, "InsultFilter.py")
    subprocess.Popen(["python3", path])

def connect_to(name):
    ns = Pyro4.locateNS()
    uri = ns.lookup(name)
    return Pyro4.Proxy(uri)

# ================================
# Fixture de setup
# ================================
processes = []
@pytest.fixture(scope="module", autouse=True)
def setup_services():


    # Iniciar los procesos
    broadcaster_process = Process(target=start_broadcaster)
    broadcaster_process.start()
    processes.append(broadcaster_process)

    receiver_process = Process(target=start_receiver)
    receiver_process.start()
    processes.append(receiver_process)

    filter_process = Process(target=start_filter)
    filter_process.start()
    processes.append(filter_process)

    # Temps prudencial per a que no hagi errors
    time.sleep(5)

    yield

    # Llimpiem tots els processos
    for process in processes:
        process.terminate()
        process.join()

# ================================
# Tests
# ================================

def test_producer_to_broadcaster():
    """Verifica Producer → Consumer → Broadcaster con Pyro4."""
    receiver = connect_to("insult.consumer")
    broadcaster = connect_to("insult.broadcaster")

    test_insults = ["InsultTest1", "InsultTest2", "InsultTest3"]

    for insult in test_insults:
        response = receiver.add_insult(insult)
        assert insult in response
        print(f"Insult '{insult}' enviat al Receiver correctament")

    time.sleep(1)  

    insults_in_broadcaster = broadcaster.get_insults()

    for insult in test_insults:
        assert insult in insults_in_broadcaster, f"L'insulto '{insult}' no s'ha trobat al broadcaster"
        print(f"L'insulto '{insult}' trobat al Broadcaster")

def test_listener_receives_new_insults():
    """Verifica que el listener rep els insults nous del Broadcaster."""
    receiver = connect_to("insult.consumer")
    insultFilter = connect_to("filter.service")
    broadcaster = connect_to("insult.broadcaster")

    test_insults = ["ListenerTest1", "ListenerTest2"]

    for insult in test_insults:
        receiver.add_insult(insult)
        print(f"L'insult '{insult}' s'ha enviat al listener")

    time.sleep(1)

    insults_in_filter = insultFilter.get_all_insults()

    for insult in test_insults:
        assert insult in insults_in_filter, f"L'insult '{insult}' no l'ha rebut el filter"
        print(f"El listener ha rebut l'insult '{insult}' correctament")

def test_filter_service_filters_text():
    """Verifica que el servei Filter censura correctament els insults usant Pyro4."""

    filter_process = Process(target=start_filter)
    filter_process.start()
    processes.append(filter_process)
    time.sleep(5)
    filter_client = connect_to("filter.service")
    broadcaster = connect_to("insult.broadcaster")

    test_insults = ["FiltreInsult", "puto"]  

    for insult in test_insults:
        broadcaster.add_insult(insult)
        print(f"Enviant l'insult '{insult}' para el filtre")


    time.sleep(2)

    test_texts = ["Genis puto amo", f"Jan FiltreInsult", f"Puto FiltreInsult"]

    filtered_texts = []
    for text in test_texts:
        filtered_text = filter_client.filtrar(text)
        filtered_texts.append(filtered_text)
        print(f"Text original: '{text}' ➡️ Filtrat: '{filtered_text}'")
        assert "CENSORED" in filtered_text, f"El text '{text}' no s'ha filtrat correctament"

    filtered_results = filter_client.get_all_filtered()
    for original in test_texts:
        assert any("CENSORED" in result for result in filtered_results), f"No s'ha trobat text censurat en els resultats filtrats"

    print(f"Texts filtrats guardats són correctes")

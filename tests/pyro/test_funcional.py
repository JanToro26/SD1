import pytest
import Pyro4
import time
from multiprocessing import Process
import os
import sys
import subprocess

BASE_DIR = sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# ================================
# Helpers
# ================================

def start_broadcaster():
    path = os.path.join(BASE_DIR, "InsultBroadcaster.py")
    print(f"Starting Broadcaster at: {path}")
    subprocess.Popen(["python3", path])

def start_receiver():
    path = os.path.join(BASE_DIR, "InsultConsumer.py")
    print(f"Starting Receiver at: {path}")
    subprocess.Popen(["python3", path])

def start_filter():
    path = os.path.join(BASE_DIR, "InsultFilter.py")
    print(f"Starting Filter at: {path}")
    subprocess.Popen(["python3", path])

def connect_to(name):
    ns = Pyro4.locateNS()
    uri = ns.lookup(name)
    return Pyro4.Proxy(uri)

# ================================
# Fixture de setup
# ================================

@pytest.fixture(scope="module", autouse=True)
def setup_services():
    processes = []

    broadcaster_process = Process(target=start_broadcaster)
    broadcaster_process.start()
    processes.append(broadcaster_process)

    receiver_process = Process(target=start_receiver)
    receiver_process.start()
    processes.append(receiver_process)

    filter_process = Process(target=start_filter)
    filter_process.start()
    processes.append(filter_process)

    # Pequeña espera para levantar servicios
    time.sleep(2)

    yield

    for process in processes:
        process.terminate()
        process.join()

# ================================
# Tests
# ================================

def test_producer_to_broadcaster():
    """Verifica Producer → Consumer → Broadcaster."""
    # Conectamos al receiver y broadcaster via Pyro
    receiver = connect_to("insult.consumer")
    broadcaster = connect_to("insult.broadcaster")

    test_insults = ["InsultTest1", "InsultTest2", "InsultTest3"]

    for insult in test_insults:
        response = receiver.add_insult(insult)
        assert insult in response
        print(f"✅ Enviado insulto '{insult}' al Receiver correctamente")

    time.sleep(1)  # Espera a que se propague

    insults_in_broadcaster = broadcaster.get_insults()

    for insult in test_insults:
        assert insult in insults_in_broadcaster, f"❌ El insulto '{insult}' no se encontró en el Broadcaster"
        print(f"✅ Insulto '{insult}' encontrado en el Broadcaster")

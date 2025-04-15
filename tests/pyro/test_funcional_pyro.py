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

    # Pequeña espera para levantar servicios
    time.sleep(15)

    yield

    # Terminamos los procesos después de las pruebas
    for process in processes:
        process.terminate()
        process.join()

# ================================
# Tests
# ================================

def test_producer_to_broadcaster():
    """Verifica Producer → Consumer → Broadcaster con Pyro4."""
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

def test_listener_receives_new_insults():
    """Verifica que el listener recibe insultos nuevos del Broadcaster."""
    # Conectamos al receiver y broadcaster via Pyro
    receiver = connect_to("insult.consumer")
    broadcaster = connect_to("insult.broadcaster")

    test_insults = ["ListenerTest1", "ListenerTest2"]

    for insult in test_insults:
        receiver.add_insult(insult)
        print(f"🚀 Enviado insulto '{insult}' para listener")

    # Esperamos un poco para que el receptor reciba los insultos
    time.sleep(1)

    # Recuperamos los insultos desde el broadcaster
    insults_in_broadcaster = broadcaster.get_insults()

    for insult in test_insults:
        assert insult in insults_in_broadcaster, f"❌ El insulto '{insult}' no fue recibido por el listener"
        print(f"✅ Listener recibió insulto '{insult}' correctamente")

def test_filter_service_filters_text():
    """Verifica que el servicio Filter censura correctamente los insultos usando Pyro4."""

    # Conectamos al Filter via Pyro
    filter_client = connect_to("filter.service")
    broadcaster = connect_to("insult.broadcaster")

    test_insults = ["FiltreInsult", "puto"]  # Agregamos también 'puto'

    # Aseguramos que los insultos se envían
    for insult in test_insults:
        broadcaster.add_insult(insult)
        print(f"🚀 Enviado insulto '{insult}' para el filtro")

    # Esperamos que el filtro actualice sus insultos
    time.sleep(2)

    test_texts = ["Genis puto amo", f"Jan FiltreInsult", f"Puto FiltreInsult"]

    filtered_texts = []
    for text in test_texts:
        filtered_text = filter_client.filtrar(text)
        filtered_texts.append(filtered_text)
        print(f"📝 Texto original: '{text}' ➡️ Filtrado: '{filtered_text}'")
        assert "CENSORED" in filtered_text, f"❌ El texto '{text}' no fue filtrado correctamente"

    # Verificamos que el filtro almacena los textos filtrados
    filtered_results = filter_client.get_all_filtered()
    for original in test_texts:
        assert any("CENSORED" in result for result in filtered_results), f"❌ No se encontró texto censurado en los resultados filtrados"

    print(f"✅ Textos filtrados almacenados correctamente")

import os
import sys
import time
from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
import Pyro4
import subprocess

# Configuración del path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../pyro'))

# ================================
# Helpers
# ================================

def start_broadcaster():
    """Inicia el servicio del broadcaster"""
    path = os.path.join(BASE_DIR, "InsultBroadcaster.py")
    subprocess.Popen(["python3", path])

def start_receiver():
    """Inicia el servicio del receiver"""
    path = os.path.join(BASE_DIR, "InsultConsumer.py")
    subprocess.Popen(["python3", path])

def start_filter():
    """Inicia el servicio del filter"""
    path = os.path.join(BASE_DIR, "InsultFilter.py")
    subprocess.Popen(["python3", path])

def start_producer():
    """Inicia el servicio del producer"""
    path = os.path.join(BASE_DIR, "InsultProducer.py")
    subprocess.Popen(["python3", path])

def connect_to(name):
    """Conecta con el servicio Pyro correspondiente"""
    ns = Pyro4.locateNS()  # Localiza el Name Server
    uri = ns.lookup(name)  # Busca el servicio por nombre
    return Pyro4.Proxy(uri)  # Devuelve el proxy al servicio remoto

# ================================
# Función principal del test
# ================================

def stress_test(task_function, num_requests):
    """Calcula el tiempo necesario para realizar el estrés test enviando peticiones concurrentemente."""
    start_time = time.perf_counter()

    # Función que se usa para enviar todas las peticiones en paralelo
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(task_function, range(num_requests))

    # Retorna el tiempo que ha tardado en ejecutarse
    duration = time.perf_counter() - start_time
    return duration

# Función que simula peticiones al Consumer/broadcaster
def producer_task(i):
    """Envia un insulto al Consumer"""
    producer = connect_to("insult.producer")  # Conecta al productor de insultos
    insult = f"StressInsult{i}"
    response = producer.send_insult(insult)
    print(f"Enviado: {insult}, Respuesta: {response}")

def filter_task(i):
    """Simula una petición al servicio Filter"""
    filter_client = connect_to("filter.service")  # Conectamos con el servicio Filter
    text = f"This is a test StressInsult message {i}"
    filtered_text = filter_client.filtrar(text)
    print(f"Texto original: '{text}' ➡️ Filtrado: '{filtered_text}'")

# ================================
# Funciones de exportación y salida
# ================================

def export_results_txt(results):
    """Exporta los resultados del test a un archivo .txt para su posterior análisis."""
    with open('single_node_performance_results_Pyro.txt', 'w') as f:
        f.write("Número de peticions\tTemps InsultService (s)\tTempsFilterService (s)\n")
        for i in range(len(results['requests'])):
            f.write(f"{results['requests'][i]}\t{results['InsultService'][i]:.4f}\t{results['FilterService'][i]:.4f}\n")

def suppress_output():
    """Suprime la salida estándar durante el test"""
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

def run_test():
    """Realiza el test de estrés enviando peticiones concurrentes y midiendo el tiempo de ejecución"""

    processes = []

    # Inicializar los 3 servicios y esperar que se inicien correctamente
    broadcaster_process = Process(target=start_broadcaster)
    broadcaster_process.start()
    processes.append(broadcaster_process)

    receiver_process = Process(target=start_receiver)
    receiver_process.start()
    processes.append(receiver_process)

    filter_process = Process(target=start_filter)
    filter_process.start()
    processes.append(filter_process)

    producer_process = Process(target=start_producer)
    producer_process.start()
    processes.append(producer_process)

    # Esperamos un momento para asegurarnos de que todos los servicios estén activos
    time.sleep(5)

    # Preparar insulto inicial para el filtro
    producer = connect_to("insult.producer")
    producer.send_insult("StressInsult")
    time.sleep(1)

    # Realizar las pruebas con 100, 200, 500, 1000 y 2000 peticiones
    results = {'requests': [], 'InsultService': [], 'FilterService': []}

    for num_requests in [100, 200, 500, 1000, 2000]:
        insult_service_time = stress_test(producer_task, num_requests)
        filter_service_time = stress_test(filter_task, num_requests)

        results['requests'].append(num_requests)
        results['InsultService'].append(insult_service_time)
        results['FilterService'].append(filter_service_time)

        if insult_service_time > 30 or filter_service_time > 30:
            break

    # Exportar los resultados
    export_results_txt(results)

    # Finalizar los procesos
    for process in processes:
        process.terminate()
        process.join()

if __name__ == "__main__":
    run_test()

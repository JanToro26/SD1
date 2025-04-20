import os
import sys
import time
import socket
from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
import subprocess
from xmlrpc.client import ServerProxy

# Configuración del path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
from dynamicScalling import InsultProducer, InsultConsumer, InsultBroadcaster, InsultFilter

FILTER_URL = "http://localhost:8002/RPC2"

# Configuraciones básicas del test
REQUESTS = 500  # El número de peticiones iniciales
MAX_REQUESTS = 2000  # Número máximo de peticiones a enviar
INCREMENT = 500  # Incremento en el número de peticiones
MAX_NODES = 10  # Número máximo de nodos a utilizar

results = {
    'requests': [],
    'nodes_consumer': [],
    'nodes_broadcaster': [],
    'nodes_filter': [],
    'InsultService_time': [],
    'FilterService_time': [],
    'Broadcaster_time': [],
    'Messages_per_second': []
}

# ================================
# Helpers
# ================================

def start_broadcaster():
    """Inicia el InsultBroadcaster que ya maneja la conexión y la cola RabbitMQ"""
    broadcaster_process = subprocess.Popen(["python3", os.path.join(BASE_DIR, "InsultBroadcaster.py")])
    return broadcaster_process

def start_receiver():
    """Inicia el consumidor que escucha los insultos de RabbitMQ"""
    receiver_process = subprocess.Popen(["python3", os.path.join(BASE_DIR, "InsultConsumer.py")])
    return receiver_process

def start_filter():
    """Inicia el servicio de filtrado"""
    filter_process = subprocess.Popen(["python3", os.path.join(BASE_DIR, "InsultFilter.py")])
    return filter_process

def connect_to(name):
    """Conecta a un servicio XMLRPC"""
    ns = ServerProxy("http://localhost:8000")
    uri = ns.lookup(name)
    return ServerProxy(uri)

# ================================
# Función para realizar el test de carga
# ================================

def stress_test(task_function, num_requests):
    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(task_function, range(num_requests))

    duration = time.perf_counter() - start_time
    return duration

def producer_task(i):
    producer = InsultProducer.InsultProducer()
    insult = f"StressInsult{i}"
    producer.send_insult(insult)

def filter_task(i):
    filter_client = ServerProxy(FILTER_URL)
    text = f"This is a test StressInsult message {i}"
    filter_client.filtrar(text)

# ================================
# Función para exportar los resultados a un archivo
# ================================

def export_results_txt(results):
    with open('dynamic_scaling_results.txt', 'w') as f:
        f.write("Peticiones\tNodos_Consumer\tNodos_Broadcaster\tNodos_Filter\tTiempo_InsultService (s)\tSpeedup_InsultService\tTiempo_FilterService (s)\tSpeedup_FilterService\tMensajes_por_segundo\n")

        for i in range(len(results['requests'])):
            peticiones = results['requests'][i]
            consumer_nodes = results['nodes_consumer'][i]
            broadcaster_nodes = results['nodes_broadcaster'][i]
            filter_nodes = results['nodes_filter'][i]
            insult_time = results['InsultService_time'][i]
            filter_time = results['FilterService_time'][i]
            speedup_insult = results['InsultService_time'][0] / insult_time if insult_time > 0 else 0
            speedup_filter = results['FilterService_time'][0] / filter_time if filter_time > 0 else 0
            messages_per_second = results['Messages_per_second'][i]

            f.write(f"{peticiones}\t{consumer_nodes}\t{broadcaster_nodes}\t{filter_nodes}\t{insult_time:.4f}\t{speedup_insult:.2f}\t{filter_time:.4f}\t{speedup_filter:.2f}\t{messages_per_second:.2f}\n")

def calculate_nodes(num_requests):
    """Calcula el número de nodos necesario según las peticiones"""
    nodes_needed = num_requests // 100  # Por ejemplo, cada nodo puede manejar 100 peticiones
    if num_requests % 100 != 0:
        nodes_needed += 1
    return min(nodes_needed, MAX_NODES)  # Limitar a un máximo de nodos definidos

def run_dynamic_scaling_test():
    num_requests = 500
    while num_requests <= MAX_REQUESTS:
        for num_nodes in range(1, calculate_nodes(num_requests) + 1):
            processes = []

            # Iniciar el broadcaster
            broadcaster_process = start_broadcaster()
            processes.append(broadcaster_process)

            # Iniciar los consumers y filters
            for _ in range(num_nodes):
                receiver_process = start_receiver()
                processes.append(receiver_process)

            for _ in range(num_nodes):
                filter_process = start_filter()
                processes.append(filter_process)

            # Tiempo prudencial para que todo se inicie correctamente
            time.sleep(5)

            # Generar el insulto inicial
            producer = connect_to("insult.producer")
            producer.send_insult("StressInsult")
            time.sleep(1)

            # Realizar el test de las 500 peticiones
            insult_service_time = stress_test(producer_task, num_requests)
            filter_service_time = stress_test(filter_task, num_requests)

            # Guardar los resultados
            results['requests'].append(num_requests)
            results['nodes_consumer'].append(num_nodes)
            results['nodes_broadcaster'].append(num_nodes)
            results['nodes_filter'].append(num_nodes)
            results['InsultService_time'].append(insult_service_time)
            results['FilterService_time'].append(filter_service_time)
            results['Messages_per_second'].append(num_requests / (insult_service_time + filter_service_time))

            # Terminar todos los procesos
            for process in processes:
                process.terminate()
                process.join()

        export_results_txt(results)

        # Aumentar el número de peticiones para la siguiente iteración
        num_requests += INCREMENT


if __name__ == "__main__":
    run_dynamic_scaling_test()

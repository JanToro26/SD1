import os
import sys
import time
import socket
from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
import subprocess
from xmlrpc.client import ServerProxy

# Configuració del path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../dynamicScalling'))
from dynamicScalling import InsultProducer, InsultConsumer, InsultBroadcaster, InsultFilter

FILTER_URL = "http://localhost:8002/RPC2"

N_REQUESTS = [500, 1000, 2000, 5000, 10000, 500]  # Peticions de prueba
MAX_NODES = 10  # Número màxim de nodos a utilitzar

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
    """Inicia el InsultBroadcaster que ja controla la connexió y la cua RabbitMQ"""
    broadcaster_process = subprocess.Popen(
        ["python3", os.path.join(BASE_DIR, "InsultBroadcaster.py")],
        stdout=subprocess.PIPE,  # Redirigeix la sortida estándar
        stderr=subprocess.PIPE   # Redirigeix la sortida de errors
    )
    return broadcaster_process

def start_receiver():
    """Inicia el receiver del consumidor InsultConsumer"""
    receiver = InsultConsumer.InsultConsumer()
    receiver.run()

def start_filter():
    """Inicia el filter"""
    filter = InsultFilter.InsultFilter()
    filter.run()


# ================================
# Funció per a realitzar el test de càrrega
# ================================

def stress_test(task_function, num_requests):
    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(task_function, range(num_requests))

    duration = time.perf_counter() - start_time
    return duration

def producer_task(i):
    """Tasca del productor que envia insults"""
    producer = InsultProducer.InsultProducer()
    insult = f"StressInsult{i}"
    producer.send_insult(insult)

def filter_task(i):
    """Tasca de filtrat que crida al servei de filtrat"""
    filter_client = ServerProxy(FILTER_URL)
    text = f"This is a test StressInsult message {i}"
    filter_client.filtrar(text)

# ================================
# Funció per a exportar els resultats a un arxiu
# ================================

def export_results_txt(results):
    with open('dynamic_scaling_results.txt', 'w') as f:
        f.write("Peticiones\tNodos_Consumer\tNodos_Broadcaster\tNodos_Filter\tTiempo_InsultService (s)\tTiempo_FilterService (s)\tMensajes_por_segundo\n")

        for i in range(len(results['requests'])):
            peticiones = results['requests'][i]
            consumer_nodes = results['nodes_consumer'][i]
            broadcaster_nodes = results['nodes_broadcaster'][i]
            filter_nodes = results['nodes_filter'][i]
            insult_time = results['InsultService_time'][i]
            filter_time = results['FilterService_time'][i]
            messages_per_second = results['Messages_per_second'][i]

            f.write(f"{peticiones}\t{consumer_nodes}\t{broadcaster_nodes}\t{filter_nodes}\t{insult_time:.4f}\t{filter_time:.4f}\t{messages_per_second:.2f}\n")


def calculate_nodes(num_requests, total_time, processing_time, worker_capacity):
    # Calcula la taxa d'arribada' de missatges (lambda)
    lambda_rate = num_requests / total_time  # Número de peticions per segon
    
    # Aplica la fórmula: N = ceil((lambda * T) / C)
    num_nodes = (lambda_rate * processing_time) / worker_capacity
    
    # Arrodonir cap dalt si no és un número sencer
    return int(num_nodes) if num_nodes == int(num_nodes) else int(num_nodes) + 1


def suppress_output():
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')


def run_dynamic_scaling_test():
    processing_time = 0.1  # Temps de processament per petició en segons
    worker_capacity = 10  # Capacitat de un traeballador en missatges per segon
    total_time = 20
    suppress_output()
    for n_requests in N_REQUESTS:
        print(f"Realitzant prova amb {n_requests} peticions")

        num_nodes = calculate_nodes(n_requests, total_time, processing_time, worker_capacity)
        processes = []

        # Iniciar el broadcaster en processos independents
        for _ in range(num_nodes):
            broadcaster_process = Process(target=start_broadcaster)
            broadcaster_process.start()
            processes.append(broadcaster_process)

        # Iniciar els consumidors i filtres en processos independents
        for _ in range(num_nodes):
            receiver_process = Process(target=start_receiver)
            receiver_process.start()
            processes.append(receiver_process)

        for _ in range(num_nodes):
            filter_process = Process(target=start_filter)
            filter_process.start()
            processes.append(filter_process)

        # Temps prudencial per a que tot s'iniciï correctament
        time.sleep(5)

        # Realitzar el test de las peticions
        insult_service_time = stress_test(producer_task, n_requests)
        filter_service_time = stress_test(filter_task, n_requests)

        # Guardar els resultats
        results['requests'].append(n_requests)
        results['nodes_consumer'].append(num_nodes)
        results['nodes_broadcaster'].append(num_nodes)
        results['nodes_filter'].append(num_nodes)
        results['InsultService_time'].append(insult_service_time)
        results['FilterService_time'].append(filter_service_time)
        results['Messages_per_second'].append(n_requests / (insult_service_time + filter_service_time))

        # Terminar tots els processos
        for process in processes:
            process.terminate()
            process.join()

        export_results_txt(results)

if __name__ == "__main__":
    run_dynamic_scaling_test()

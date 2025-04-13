# tests/XMLRPC/test_performance_static_scaling.py

import os
import sys
import time
import socket
from multiprocessing import Process
from xmlrpc.client import ServerProxy
from concurrent.futures import ThreadPoolExecutor

# Configuración de paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from XMLRPC import InsultProducer, InsultConsumer, InsultBroadcaster, InsultFilter

# ================================
# Configuración base
# ================================

BROADCASTER_URL = "http://localhost:8001/RPC2"
FILTER_URL = "http://localhost:8002/RPC2"
REQUESTS = 500
NODE_COUNTS = [1, 2, 3]

results = {
    'nodes': [],
    'InsultService_time': [],
    'FilterService_time': [],
}

# ================================
# Helpers
# ================================

original_stdout = sys.stdout
original_stderr = sys.stderr

def suppress_output():
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

def restore_output():
    sys.stdout = original_stdout
    sys.stderr = original_stderr

def wait_for_port(port, host='localhost', timeout=10.0):
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
    from XMLRPC import InsultFilter
    InsultFilter.run_server()

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
# Test escalado estático multinodo
# ================================

def run_static_scaling_test():
    suppress_output()

    for num_nodes in NODE_COUNTS:
        processes = []

        # Broadcaster único
        broadcaster_process = Process(target=start_broadcaster)
        broadcaster_process.start()
        processes.append(broadcaster_process)
        wait_for_port(8001)

        # Varios Receivers
        for _ in range(num_nodes):
            receiver_process = Process(target=start_receiver)
            receiver_process.start()
            processes.append(receiver_process)
        wait_for_port(8000)

        # Varios Filters
        for _ in range(num_nodes):
            filter_process = Process(target=start_filter)
            filter_process.start()
            processes.append(filter_process)
        wait_for_port(8002)

        # Preparar insulto inicial
        producer = InsultProducer.InsultProducer()
        producer.send_insult("StressInsult")
        time.sleep(1)

        # Stress tests
        insult_service_time = stress_test(producer_task, REQUESTS)
        filter_service_time = stress_test(filter_task, REQUESTS)

        # Guardar resultados
        results['nodes'].append(num_nodes)
        results['InsultService_time'].append(insult_service_time)
        results['FilterService_time'].append(filter_service_time)

        # Terminar procesos
        for process in processes:
            process.terminate()
            process.join()

    restore_output()

    # Guardamos resultados en txt
    export_results_txt(results)

def export_results_txt(results):
    initial_insult_time = results['InsultService_time'][0]
    initial_filter_time = results['FilterService_time'][0]

    with open('static_scaling_results.txt', 'w') as f:
        f.write("Número de nodos\tTiempo InsultService (s)\tSpeedup InsultService\tTiempo FilterService (s)\tSpeedup FilterService\n")

        for i in range(len(results['nodes'])):
            insult_time = results['InsultService_time'][i]
            filter_time = results['FilterService_time'][i]

            insult_speedup = initial_insult_time / insult_time if insult_time > 0 else 0
            filter_speedup = initial_filter_time / filter_time if filter_time > 0 else 0

            f.write(f"{results['nodes'][i]}\t{insult_time:.4f}\t{insult_speedup:.2f}\t{filter_time:.4f}\t{filter_speedup:.2f}\n")

    print("📄 Resultados exportados a 'static_scaling_results.txt'")

# ================================
# Lanzador manual
# ================================

if __name__ == "__main__":
    run_static_scaling_test()

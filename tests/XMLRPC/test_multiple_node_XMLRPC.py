# tests/XMLRPC/test_performance_static_scaling.py

import os
import sys
import time
import socket
from multiprocessing import Process
from xmlrpc.client import ServerProxy
from concurrent.futures import ThreadPoolExecutor

# Configuració del path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from XMLRPC import InsultProducer, InsultConsumer, InsultBroadcaster, InsultFilter

# ================================
# Configuració base
# ================================

BROADCASTER_URL = "http://localhost:8001/RPC2"
FILTER_URL = "http://localhost:8002/RPC2"
REQUESTS = 500          #Mantenim estàtic ja que no és el que ens interesa, podria ser major o menor
NODE_COUNTS = [1, 2, 3]     #Fixem el número de nodes que tindrem

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


#Mateixa funció que espera el port per que no hagin errors
#Mira si el port esta actiu i esperant conexions
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

#Mateixes 3 funcion d'inicialització
def start_broadcaster():
    broadcaster = InsultBroadcaster.InsultBroadcaster()
    broadcaster.run()

def start_receiver():
    receiver = InsultConsumer.InsultConsumer()
    receiver.run()

def start_filter():
    filter = InsultFilter.InsultFilter()
    filter.run()

#Mateixa funció que en el single node
#Envia x peticions en paral·lel
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

#Funció base del test
def run_static_scaling_test():
    suppress_output()

    for num_nodes in NODE_COUNTS:
        processes = []

        # Broadcaster únic ja que no l'hem de testejar en aquest cas
        broadcaster_process = Process(target=start_broadcaster)
        broadcaster_process.start()
        processes.append(broadcaster_process)
        wait_for_port(8001)

        #X recievers
        for _ in range(num_nodes):
            receiver_process = Process(target=start_receiver)
            receiver_process.start()
            processes.append(receiver_process)
        wait_for_port(8000)

        #X Filters
        for _ in range(num_nodes):
            filter_process = Process(target=start_filter)
            filter_process.start()
            processes.append(filter_process)
        wait_for_port(8002)

        #Preparem insult inicial
        producer = InsultProducer.InsultProducer()
        producer.send_insult("StressInsult")
        time.sleep(1)

        #Fem el test de les 500 peticions per als 2 serveis.
        #Les peticions es faràn seqüencialment
        # 1era petició -> 1er node
        # 2na petició -> 2n node
        # 3era petició -> 3er node
        #Succesivament.....
        insult_service_time = stress_test(producer_task, REQUESTS)
        filter_service_time = stress_test(filter_task, REQUESTS)

        # Guardar resultados
        results['nodes'].append(num_nodes)
        results['InsultService_time'].append(insult_service_time)
        results['FilterService_time'].append(filter_service_time)

        # Matar tots els processos
        for process in processes:
            process.terminate()
            process.join()


    # Guardem resultats a un txt
    export_results_txt(results)

def export_results_txt(results):
    initial_insult_time = results['InsultService_time'][0]
    initial_filter_time = results['FilterService_time'][0]

    with open('static_scaling_results_XMLRPC.txt', 'w') as f:
        f.write("Número de nodes\tTemps InsultService (s)\tSpeedup InsultService\tTemps FilterService (s)\tSpeedup FilterService\n")

        for i in range(len(results['nodes'])):
            insult_time = results['InsultService_time'][i]
            filter_time = results['FilterService_time'][i]

            insult_speedup = initial_insult_time / insult_time if insult_time > 0 else 0
            filter_speedup = initial_filter_time / filter_time if filter_time > 0 else 0

            f.write(f"{results['nodes'][i]}\t{insult_time:.4f}\t{insult_speedup:.2f}\t{filter_time:.4f}\t{filter_speedup:.2f}\n")

if __name__ == "__main__":
    run_static_scaling_test()

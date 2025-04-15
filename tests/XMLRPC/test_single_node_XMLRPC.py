# tests/XMLRPC/test_performance_single_node.py

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

#Funció que espera que s'establixque el servei
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

#Execucció del servei broadcaster
def start_broadcaster():
    broadcaster = InsultBroadcaster.InsultBroadcaster()
    broadcaster.run()
#Execucció del Consumer
def start_receiver():
    receiver = InsultConsumer.InsultConsumer()
    receiver.run()

#Execucció del filter
def start_filter():
    filter = InsultFilter.InsultFilter()
    filter.run()


#Funció principal del test
def stress_test(task_function, num_requests):
    #Calculem el temps per a poder fer l'estudi 
    start_time = time.perf_counter()

    #Funció que usem per a poder enviar totes les peticions en paral·lel i poder fer l'estress test necessari amb 100 "clients" que son fils paral·lels que fan
    #peticions a l'hora
    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(task_function, range(num_requests))
    
    #Retornem el temps que ha tardat en executar-se
    duration = time.perf_counter() - start_time
    return duration


#Funció que simula peticions al Consumer/broadcaster
def producer_task(i):
    producer = InsultProducer.InsultProducer()
    insult = f"StressInsult{i}"
    producer.send_insult(insult)

#Funció que simula peticions al filter
def filter_task(i):
    filter_client = ServerProxy(FILTER_URL)
    text = f"This is a test StressInsult message {i}"
    filter_client.filtrar(text)


#Funció per exportar-ho a un txt per a poder fer les gràfiques
def export_results_txt(results):
    with open('single_node_performance_results_XMLRPC.txt', 'w') as f:
        f.write("Número de peticiones\tTemps InsultService (s)\tTempsFilterService (s)\n")
        for i in range(len(results['requests'])):
            f.write(f"{results['requests'][i]}\t{results['InsultService'][i]:.4f}\t{results['FilterService'][i]:.4f}\n")

#Funció per a llevar el output
def suppress_output():
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

def run_test():
    processes = []
    suppress_output()

    # Inicialitzar els 3 serveis i esperar que s'establixquen per a poder començar amb el test sense problemes
    broadcaster_process = Process(target=start_broadcaster)
    broadcaster_process.start()
    processes.append(broadcaster_process)
    wait_for_port(8001)

    receiver_process = Process(target=start_receiver)
    receiver_process.start()
    processes.append(receiver_process)
    wait_for_port(8000)

    filter_process = Process(target=start_filter)
    filter_process.start()
    processes.append(filter_process)
    wait_for_port(8002)

    # Preparar insulto inicial para el filtro
    producer = InsultProducer.InsultProducer()
    producer.send_insult("StressInsult")
    time.sleep(1)

    # Realitzar les proves amb 100, 200, 500, 1000 i 2000 peticions
    results = {'requests': [], 'InsultService': [], 'FilterService': []}

    for num_requests in [100, 200, 500, 1000, 2000]:
        insult_service_time = stress_test(producer_task, num_requests)
        filter_service_time = stress_test(filter_task, num_requests)

        results['requests'].append(num_requests)
        results['InsultService'].append(insult_service_time)
        results['FilterService'].append(filter_service_time)

        if insult_service_time > 30 or filter_service_time > 30:
            break

    #Exportar resultats
    export_results_txt(results)

    #Matar tots els processos
    for process in processes:
        process.terminate()
        process.join()

if __name__ == "__main__":
    run_test()

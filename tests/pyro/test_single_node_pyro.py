import os
import sys
import time
from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
import Pyro4
import subprocess

# Configuració del path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../pyro'))

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

def start_producer():
    path = os.path.join(BASE_DIR, "InsultProducer.py")
    subprocess.Popen(["python3", path])

def connect_to(name):
    ns = Pyro4.locateNS()  
    uri = ns.lookup(name)  
    return Pyro4.Proxy(uri)  

# ================================
# Funció principal del test
# ================================

def stress_test(task_function, num_requests):
    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(task_function, range(num_requests))

    duration = time.perf_counter() - start_time
    return duration

def producer_task(i):
    producer = connect_to("insult.producer") 
    insult = f"StressInsult{i}"
    response = producer.send_insult(insult)

def filter_task(i):
    
    filter_client = connect_to("filter.service") 
    text = f"This is a test StressInsult message {i}"
    filtered_text = filter_client.filtrar(text)
    

# ================================
# uncio que ens dona el txt amb els resultats
# ================================

def export_results_txt(results):
    with open('single_node_performance_results_Pyro.txt', 'w') as f:
        f.write("Número de peticions\tTemps InsultService (s)\tTempsFilterService (s)\n")
        for i in range(len(results['requests'])):
            f.write(f"{results['requests'][i]}\t{results['InsultService'][i]:.4f}\t{results['FilterService'][i]:.4f}\n")

def suppress_output():
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

def run_test():
    

    processes = []

    # Inicialitzem els 3 serveis i esperem que estiguin operatius
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

   
    time.sleep(5)

    # Primer insult prudencial
    producer = connect_to("insult.producer")
    producer.send_insult("StressInsult")
    time.sleep(1)

    # Fem proves amb 100, 200, 300, 500, 1000 i 2000 peticions
    results = {'requests': [], 'InsultService': [], 'FilterService': []}

    for num_requests in [100, 200, 500, 1000, 2000]:
        insult_service_time = stress_test(producer_task, num_requests)
        filter_service_time = stress_test(filter_task, num_requests)

        results['requests'].append(num_requests)
        results['InsultService'].append(insult_service_time)
        results['FilterService'].append(filter_service_time)

        if insult_service_time > 30 or filter_service_time > 30:
            break

    # Exportem resultats
    export_results_txt(results)

    # Llimpiem tots els processos
    for process in processes:
        process.terminate()
        process.join()

if __name__ == "__main__":
    run_test()

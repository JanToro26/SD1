import os
import sys
import time
from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
import Pyro4
import subprocess

# Configuració del path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../pyro'))

# Configuracions bàsiques del test
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
# Funcio que ens dona el txt amb els resultats
# ================================


def export_results_txt(results):
    initial_insult_time = results['InsultService_time'][0]
    initial_filter_time = results['FilterService_time'][0]

    with open('static_scaling_results_pyro.txt', 'w') as f:
        f.write("Número de nodes\tTemps InsultService (s)\tSpeedup InsultService\tTemps FilterService (s)\tSpeedup FilterService\n")

        for i in range(len(results['nodes'])):
            insult_time = results['InsultService_time'][i]
            filter_time = results['FilterService_time'][i]

            insult_speedup = initial_insult_time / insult_time if insult_time > 0 else 0
            filter_speedup = initial_filter_time / filter_time if filter_time > 0 else 0

            f.write(f"{results['nodes'][i]}\t{insult_time:.4f}\t{insult_speedup:.2f}\t{filter_time:.4f}\t{filter_speedup:.2f}\n")

def suppress_output():
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

def run_test():
    for n_nodes in NODE_COUNTS:
        
        processes = []

        # Broadcaster és un solament
        broadcaster_process = Process(target=start_broadcaster)
        broadcaster_process.start()
        processes.append(broadcaster_process)

        for _ in range(n_nodes):
            receiver_process = Process(target=start_receiver)
            receiver_process.start()
            processes.append(receiver_process)

        for _ in range(n_nodes):
            filter_process = Process(target=start_filter)
            filter_process.start()
            processes.append(filter_process)

        # Preparem insult inicial
        producer_process = Process(target=start_producer)
        producer_process.start()
        processes.append(producer_process)

        # Temps prudencial per no causar problemes
        time.sleep(5)


        producer = connect_to("insult.producer")
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

        results['nodes'].append(n_nodes)
        results['InsultService_time'].append(insult_service_time)
        results['FilterService_time'].append(filter_service_time)

        # Matar tots els processos
        for process in processes:
            process.terminate()
            process.join()
        
    export_results_txt(results)

if __name__ == "__main__":
    run_test()

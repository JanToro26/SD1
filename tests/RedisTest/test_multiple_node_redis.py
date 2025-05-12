import os
import sys
import time
from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
import subprocess
import redis

# Configuració del path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Redis'))

# Configuracions bàsiques del test
REQUESTS = 500
NODE_COUNTS = [1, 2, 3]  # Nombre de nodes per cada execució del test

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

def start_text():
    path = os.path.join("Redis/TextProducer.py")
    subprocess.Popen(["/bin/python3", path])

def start_receiver():
    path = os.path.join(BASE_DIR, "InsultConsumer.py")
    subprocess.Popen(["python3", path])

def start_filter():
    path = os.path.join(BASE_DIR, "Insultfilter.py")
    subprocess.Popen(["python3", path])

def start_producer():
    path = os.path.join(BASE_DIR, "InsultProducer.py")
    subprocess.Popen(["python3", path])

def connect_to_redis(service_name):
    """Connexió a Redis per al servei especificat"""
    client = redis.StrictRedis(host='localhost', port=6379, db=0)
    return client

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
    producer = connect_to_redis("insult.producer")
    insult = f"StressInsult{i}"
    # Afegir insult a la llista Redis
    producer.lpush("insults", insult)

def filter_task(i):
    filter_client = connect_to_redis("filter.service")
    text = f"This is a test StressInsult message {i}"
    # Afegir insult a la llista Redis
    filter_client.lpush("filter_messages", text)

# ================================
# Funció per exportar els resultats a un arxiu
# ================================

def export_results_txt(results):
    initial_insult_time = results['InsultService_time'][0]
    initial_filter_time = results['FilterService_time'][0]

    with open('static_scaling_results_redis.txt', 'w') as f:
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

        # Iniciar els serveis a Redis
        for i in range(n_nodes):
            start_broadcaster_process = Process(target=start_broadcaster)
            start_broadcaster_process.start()
            processes.append(start_broadcaster_process)
            
        for i in range(n_nodes):
            start_receiver_process = Process(target=start_receiver)
            start_receiver_process.start()
            processes.append(start_receiver_process)

        for i in range(n_nodes):
            start_filter_process = Process(target=start_filter)
            start_filter_process.start()
            processes.append(start_filter_process)

        # Iniciar el productor
        producer_process = Process(target=start_producer)
        producer_process.start()
        processes.append(producer_process)

        text_process = Process(target=start_text)
        text_process.start()
        processes.append(text_process)

        # Temps prudencial per evitar errors en la connexió
        time.sleep(5)

        # Insult inicial per començar el test
        producer = connect_to_redis("insult.producer")
        producer.lpush("insults", "StressInsult")
        time.sleep(1)

        # Test de les 500 peticions
        insult_service_time = stress_test(producer_task, REQUESTS)
        filter_service_time = stress_test(filter_task, REQUESTS)

        results['nodes'].append(n_nodes)
        results['InsultService_time'].append(insult_service_time)
        results['FilterService_time'].append(filter_service_time)

        # Finalitzar els processos
        for process in processes:
            process.terminate()
            process.join()

    export_results_txt(results)

if __name__ == "__main__":
    run_test()

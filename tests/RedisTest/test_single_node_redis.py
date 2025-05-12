import os
import sys
import time
from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
import subprocess

#from Redis import InsultProducer, Insultfilter
# Configuració del path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
#print(os.path.abspath('.'))
from Redis.InsultProducer import InsultProducer
from Redis.InsultConsumer import InsultConsumer
from Redis import Insultfilter

# ================================
# Helpers
# ================================

def start_broadcaster():
    path = os.path.join("Redis/InsultBroadcaster.py")
    subprocess.Popen(["/bin/python3", path])

def start_text():
    path = os.path.join("Redis/TextProducer.py")
    subprocess.Popen(["/bin/python3", path])

def start_receiver():
    path = os.path.join("Redis/InsultConsumer.py")
    subprocess.Popen(["/bin/python3", path])

def start_filter():
    path = os.path.join("Redis/Insultfilter.py")
    subprocess.Popen(["/bin/python3", path])

def start_producer():
    path = os.path.join("Redis/InsultProducer.py")
    subprocess.Popen(["/bin/python3", path])

def start_consumer():
    path = os.path.join("Redis/InsultConsumer.py")
    subprocess.Popen(["/bin/python3", path])
    
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
    insult = f"StressInsult{i}"
    response = InsultProducer.run(insult)
    #InsultConsumer.run()

def consumer_task(i):
    response = InsultConsumer.run()
    InsultConsumer.run()


def filter_task(i):
    text = f"This is a test StressInsult message {i}"
    filtered_text = Insultfilter.run(text)
    

# ================================
# Funció que dona el txt amb els resultats
# ================================

def export_results_txt(results):
    with open('single_node_performance_results_Redis.txt', 'w') as f:
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

    text_process = Process(target=start_text)
    text_process.start()
    processes.append(text_process)

    receiver_process = Process(target=start_receiver)
    receiver_process.start()
    processes.append(receiver_process)

    filter_process = Process(target=start_filter)
    filter_process.start()
    processes.append(filter_process)

    producer_process = Process(target=start_producer)
    producer_process.start()
    processes.append(producer_process)

    consumer_process = Process(target=start_consumer)
    consumer_process.start()
    processes.append(consumer_process)

   
    time.sleep(5)

    # Primer insult prudencial
    InsultProducer().run("StressInsult")
    time.sleep(1)

    # Fem proves amb 100, 200, 300, 500, 1000 i 2000 peticions
    results = {'requests': [], 'InsultService': [], 'FilterService': []}

    for num_requests in [100, 200, 500, 1000, 2000]:
        insult_service_time = stress_test(producer_task, num_requests)
        #consumer_service_time = stress_test(consumer_task, num_requests)
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

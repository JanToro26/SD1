import os
import sys
import time
from multiprocessing import Process
from concurrent.futures import ThreadPoolExecutor
import subprocess

# Configuració del path
print(os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.abspath('.'))))
print(sys.path)
#from RabbitMQ.InsultProducer import InsultProducer
#from RabbitMQ import InsultConsumer
#from RabbitMQ import InsultFilter
#import RabbitMQ
from RabbitMQ import InsultConsumer, InsultFilter
from RabbitMQ.InsultProducer import InsultProducer
#from RabbitMQ.InsultFilter import InsultFilter

# ================================
# Helpers
# ================================

def start_broadcaster():
    path = os.path.join("RabbitMQ/InsultBroadcaster.py")
    subprocess.Popen(["/bin/python3", path])

def start_text():
    path = os.path.join("RabbitMQ/TextProducer.py")
    subprocess.Popen(["/bin/python3", path])

def start_receiver():
    path = os.path.join("RabbitMQ/InsultConsumer.py")
    subprocess.Popen(["/bin/python3", path])

def start_filter():
    path = os.path.join("RabbitMQ/InsultFilter.py")
    subprocess.Popen(["/bin/python3", path])

def start_producer():
    path = os.path.join("RabbitMQ/InsultProducer.py")
    subprocess.Popen(["/bin/python3", path])

def start_consumer():
    path = os.path.join("RabbitMQ/InsultConsumer.py")
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


def filter_task(i):
    text = f"This is a test StressInsult message {i}"
    filtered_text = InsultFilter.run(text)
    

# ================================
# Funció que dona el txt amb els resultats
# ================================

def export_results_txt(results):
    with open('single_node_performance_results_rabbit.txt', 'w') as f:
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
    InsultProducer().run()
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

# tests/XMLRPC/test_performance_dynamic_scaling.py

import multiprocessing
import time
import os
import sys
import socket
import math
from xmlrpc.client import ServerProxy

# Configuración de paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from XMLRPC import InsultProducer, InsultConsumer, InsultBroadcaster, InsultFilter

# ================================
# Configuración
# ================================

BROADCASTER_URL = "http://localhost:8001/RPC2"
FILTER_URL = "http://localhost:8002/RPC2"
RUN_TIME = 15  # Duración total del test en segundos
CHECK_INTERVAL = 2  # Cada cuánto chequeamos la carga para escalar (segundos)

# Para la simulación
MESSAGE_RATES = [50, 100, 300, 500, 700]  # mensajes/segundo
PROCESSING_TIME = 0.05  # segundos por mensaje
WORKER_CAPACITY = 1 / PROCESSING_TIME  # mensajes/segundo por worker

results = {
    'time': [],
    'message_rate': [],
    'workers': [],
}

# ================================
# Helpers
# ================================

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

def producer_task(rate_per_sec, duration):
    producer = InsultProducer.InsultProducer()
    end_time = time.time() + duration
    while time.time() < end_time:
        insult = f"DynamicInsult{int(time.time() * 1000)}"
        producer.send_insult(insult)
        time.sleep(1.0 / rate_per_sec)

def calculate_required_workers(message_rate):
    required = math.ceil((message_rate * PROCESSING_TIME) / WORKER_CAPACITY)
    return max(required, 1)

# ================================
# Test Dynamic Scaling
# ================================

import sys
import os

def suppress_output():
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

    
def run_dynamic_scaling_test():
    suppress_output()
    processes = []

    # Iniciar Broadcaster
    broadcaster_process = multiprocessing.Process(target=start_broadcaster)
    broadcaster_process.start()
    processes.append(broadcaster_process)
    wait_for_port(8001)

    # Iniciar Filter
    filter_process = multiprocessing.Process(target=start_filter)
    filter_process.start()
    processes.append(filter_process)
    wait_for_port(8002)

    # ✅ Añadimos Receiver inicial
    receiver_process = multiprocessing.Process(target=start_receiver)
    receiver_process.start()
    processes.append(receiver_process)
    wait_for_port(8000)

    # Preparamos insulto inicial para filtro
    producer = InsultProducer.InsultProducer()
    producer.send_insult("DynamicInsult")
    time.sleep(1)

    # Iniciar productor en segundo plano para simular carga
    producer_process = multiprocessing.Process(target=producer_task, args=(MESSAGE_RATES[0], RUN_TIME))
    producer_process.start()

    # Workers dinámicos iniciales
    worker_processes = []

    start_time = time.time()
    current_rate_index = 0
    next_rate_change = time.time() + CHECK_INTERVAL

    while time.time() - start_time < RUN_TIME:
        elapsed = int(time.time() - start_time)

        # Simulación de incremento de carga
        if time.time() >= next_rate_change and current_rate_index < len(MESSAGE_RATES) - 1:
            current_rate_index += 1
            new_rate = MESSAGE_RATES[current_rate_index]
            print(f"🚀 Incrementando tasa de mensajes a: {new_rate}/s")
            producer_process.terminate()
            producer_process = multiprocessing.Process(target=producer_task, args=(new_rate, RUN_TIME - elapsed))
            producer_process.start()
            next_rate_change = time.time() + CHECK_INTERVAL

        current_message_rate = MESSAGE_RATES[current_rate_index]
        required_workers = calculate_required_workers(current_message_rate)
        current_workers = len(worker_processes)

        # Escalado dinámico
        if required_workers > current_workers:
            for _ in range(required_workers - current_workers):
                p = multiprocessing.Process(target=start_receiver)
                p.start()
                worker_processes.append(p)
            print(f"🔼 Escalando a {required_workers} workers")
        elif required_workers < current_workers:
            for _ in range(current_workers - required_workers):
                p = worker_processes.pop()
                p.terminate()
            print(f"🔽 Reducción a {required_workers} workers")

        # Guardamos resultados para el txt
        results['time'].append(elapsed)
        results['message_rate'].append(current_message_rate)
        results['workers'].append(len(worker_processes))

        time.sleep(1)

    # Cleanup
    producer_process.terminate()
    for p in worker_processes:
        p.terminate()
    for p in processes:
        p.terminate()

    # Guardamos resultados en txt
    save_results_txt()

def save_results_txt():
    with open("dynamic_scaling_results.txt", "w") as f:
        f.write("Tiempo (s)\tTasa de mensajes (msg/s)\tNúmero de workers\n")
        for t, rate, workers in zip(results['time'], results['message_rate'], results['workers']):
            f.write(f"{t}\t{rate}\t{workers}\n")
    print("📄 Resultados guardados en 'dynamic_scaling_results.txt'")

# ================================
# Lanzador manual
# ================================

if __name__ == "__main__":
    run_dynamic_scaling_test()

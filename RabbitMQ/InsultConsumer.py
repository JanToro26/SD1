import pika, redis

# Connect to the existing insults list using Redis
client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
insult_list = "insult_list"
# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare a queue (ensure it exists)
channel.queue_declare(queue='insults')

# Define the callback function
def callback(ch, method, properties, body):
    insult = body.decode('utf-8')  # Convertir de bytes a string
    cua = client.lrange(insult_list, 0, -1)  # Obtenir la llista de Redis amb els insults
    print(f" [x] Received {insult}")
    if(insult in cua):
        print(f"L'insult {insult} ja està a la llista")
    else:
        print(f"L'insult {insult} no està a la llista")
        client.lpush(insult_list, insult)

# Consume messages
channel.basic_consume(queue='insults', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit, press CTRL+C')
channel.start_consuming()

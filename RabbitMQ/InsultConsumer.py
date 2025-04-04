#!/usr/bin/env python
import pika, sys, os, redis

def main():
    client = redis.Redis(host='localhost', port=6379, db=0,
    decode_responses=True)
    insult_list = "insult_list"
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        insult = body.decode('utf-8')  # Convertir de bytes a string
        cua = client.lrange(insult_list, 0, -1)  # Obtener la lista de Redis

        if(insult in cua):
            print(f"L'insult {insult} ja està a la llista")
        else:
            print(f"L'insult {insult} no està a la llista")
            client.lpush(insult_list, insult)
        print(f" [x] Received {insult}")

    channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
import socket
from foods import get_foods
import json
import random
import time
import uvicorn

foods = get_foods()

HEADER = 64
PORT = 8080
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
#SERVER = "192.168.56.1"
SERVER = "127.0.0.1"
ADDR = (SERVER, PORT)

def main():

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)

    def send(msg):
        message = msg.encode(FORMAT)
        msg_length = len(message)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        client.send(send_length)
        client.send(message)
        print(client.recv(2048).decode(FORMAT))

    def new_order():

        order = {}
        order['id'] = int(random.random() * random.random() / random.random() * 1000000)
        order['items'] = random.sample(range(0, len(foods)), random.randint(1, 5))
        order['priority'] = random.randint(1, 5)
        order['max_wait'] = foods[order['items'][0]]['preparation-time'] * 1.3
        for i in range(len(order['items'])):
            order['max_wait'] = max(order['max_wait'], foods[order['items'][i]]['preparation-time'] * 1.3)
        for i in range(len(order['items'])):
            order['items'][i] += 1
        return order

    for i in range(random.randint(2, 5)):
        order = new_order()
        print(f"Order {order['id']} sent!")
        send(str(order))

    send(DISCONNECT_MESSAGE)

if __name__ == '__main__':
    uvicorn.run(main(), port = PORT, host = SERVER) 
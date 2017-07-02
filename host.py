#!/usr/bin/env python3

import socket
import time
import threading
import signal
import sys
import os

closing = False
connected = []
messages = []
lock = threading.Lock()
sock = socket.socket()


def signal_handler():
        print('shutting down host')
        closing = True
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
        sock.close()
        sys.exit(0)


def answer(conn, addr):
    print("connected: " + str(addr))
    while True:
        data = conn.recv(1024)
        print(str(addr) + ": " + data.decode('utf-8'))
        if not data:
            break

        #add message to queue
        lock.acquire()
        messages.append((conn, addr, data))
        lock.release()

    messages.append((conn, addr, b'disconnected!'))
    print("closing connection to " + str(addr))
    conn.close()
    lock.acquire()
    for connection in connected:
        if connection[1] == addr:
            connected.remove(connection)
    lock.release()


def send_messages(messages_array, address_array):
    for entry in messages_array:
        for address in address_array:
            if entry[1] != address[1]:
                message = b'[' + entry[1][0].encode('ascii') + b']' + entry[2]
                address[0].send(message)


signal.signal(signal.SIGINT, signal_handler)

sock.bind(('', 9707))
sock.listen(1)
sock.settimeout(0.5)

# print(sock.getsockname())

while not closing:
    try:
        conn, addr = sock.accept()
    except:
        pass
    else:
        lock.acquire()
        connected.append((conn, addr))
        lock.release()

        print('created thread for host ' + str(addr))
        threading.Thread(target=answer, args=(conn, addr)).start()

    lock.acquire()
    send_messages(messages, connected)
    messages.clear()
    lock.release()

sock.shutdown(socket.SHUT_RDWR)
sock.close()

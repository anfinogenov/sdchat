#!/usr/bin/env python3
import socket
import time
import threading
import signal
import sys
import os

closing = False
addrconnected = []
messages = []
lock = threading.Lock()

sock = socket.socket()

def signal_handler(signal, frame):
        print('shutting down host')
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
        sock.close()
        #lock.release()
        #os.kill()
        closing = True
        sys.exit(0)

def answer (conn, addr):
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

    messages.append((conn, addr, addr[0].encode('ascii') + b" disconnected!"))
    print("closing connection to " + str(addr))
    conn.close()
    lock.acquire()
    for i in addrconnected:
        if i[1] == addr:
            addrconnected.remove(i)
    lock.release()
    isWaiting(2)

def isWaiting (count):
    if threading.active_count() == count:
        pass
        #print ("waiting for connection")


signal.signal(signal.SIGINT, signal_handler)

sock.bind(('', 9707))
sock.listen(1)
sock.settimeout(0.5)

#print(sock.getsockname())

while not closing:
    isWaiting(1)
    try:
        conn, addr = sock.accept()
    except:
        isWaiting(1)
    else:
        lock.acquire()
        addrconnected.append((conn, addr))
        lock.release()

        print('created thread '+str(addr))
        threading.Thread(target=answer, args=(conn, addr)).start()

    lock.acquire()
    for i in messages:
        for j in addrconnected:
            if (i[1] != j[1]):
                j[0].send(i[1][0].encode('ascii') + b': ' + i[2])

    messages.clear()
    lock.release()

sock.shutdown(socket.SHUT_RDWR)
sock.close()


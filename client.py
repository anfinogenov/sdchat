#!/usr/bin/env python3

import socket
import threading
import sys


def usage(argv):
    print("Usage: {} <server_ip> <server_port> [nickname]".format(argv))
    sys.exit(1)


def send():
    if len(sys.argv) >= 4:
        sock.send(b"|setname " + sys.argv[3][0:20].encode('ascii', 'replace'))
    while True:
        s = input("> ")
        if s == ':q':
            break
        elif s != ':u':
            sock.send(s.encode('ascii', 'replace'))


def recv():
    while True:
        try:
            data = sock.recv(1024)
        except OSError:
            break
        if data != b'':
            print(data.decode('utf-8', 'ignore') + "\n> ", end='')


if len(sys.argv) < 3:
    usage(sys.argv[0])

server_ip = sys.argv[1]
server_port = int(sys.argv[2])

sock = socket.socket()
sock.connect((server_ip, server_port))

t1 = threading.Thread(target=send)
t2 = threading.Thread(target=recv)

t1.start()
t2.start()

print('threads started\n> ', end='')
t1.join()
print('thread "send" closed')

sock.shutdown(socket.SHUT_RDWR)
sock.close()
print('socket closed')
t2.join()

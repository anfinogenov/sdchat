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

#if message starts with that string - it's a command to server, not message
CMD = b'|'
MAX_NAME_LEN = 20

def signal_handler(signal, frame):
    print('shutting down host')
    closing = True
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except:
        pass
    sock.close()
    sys.exit(0)


#do when locked
def assign_name(conn, addr, name):
    if len(name) > MAX_NAME_LEN:
        tosend = b"Error: this name is too long. Max length is "
        tosend += str(MAX_NAME_LEN).encode('ascii') + b".\n"
        conn.send(tosend)
        return

    name_free = True
    for connection in connected:
        if len(connection) > 2:
            if connection[2] == name and connection[1] != addr:
                name_free = False
                break

    if not name_free:
        conn.send(b"Error: this name is already in use.\n")
        return

    for i in range(0, len(connected)):
        if connected[i][1] == addr:
            connected[i] = (conn, addr, name)
            print('*INFO* name set! [' + addr[0] + '] -> ' + name.decode('utf-8'))


def cmd_parse(conn, addr, message):
    # |help
    if message.startswith(CMD + b'help'):
        tosend = b"List of availbale commands:\n"
        tosend += b"-- |list\n"
        tosend += b"    Print all connected clients.\n"
        tosend += b"    Name printed if was assigned.\n"
        tosend += b"\n"
        tosend += b"-- |help\n"
        tosend += b"    Print this help.\n"
        tosend += b"\n"
        tosend += b"-- |setname <new_name>\n"
        tosend += b"    Sets a new name for current connection.\n"
        tosend += b"    Two connections couldn't have same names.\n"
        conn.send(tosend)

    # |setname <new_name>
    if message.startswith(CMD + b'setname '):
        name = message.split(b' ')[1]
        lock.acquire()
        assign_name(conn, addr, name)
        lock.release()

    # |list
    if message.startswith(CMD + b'list'):
        tosend = b"List of connected clients:\n"
        for connection in connected:
            tosend += b'-- ' + get_sender_name(connection[1])
            if connection[1] == addr:
                tosend += b' (you)'
            tosend += b"\n"
        conn.send(tosend)


#return name if set; else return ip
def get_sender_name(addr):
    for connection in connected:
        if connection[1] == addr:
            if len(connection) > 2:
                return connection[2]
            return connection[1][0].encode('ascii')
    return b'SERVER'


def answer(conn, addr):
    print("connected: " + str(addr))
    lock.acquire()
    messages.append((conn, addr, get_sender_name(addr) + b' connected!'))
    lock.release()

    while True:
        data = conn.recv(1024)
        print(str(addr) + ": " + data.decode('utf-8'))
        if not data:
            break

        #if command - parse
        if data.startswith(CMD):
            cmd_parse(conn, addr, data)
        else:
            #add message to queue
            lock.acquire()
            messages.append((conn, addr, data))
            lock.release()

    messages.append((conn, addr, get_sender_name(addr) + b' disconnected!'))
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
                message = b'[' + get_sender_name(entry[1]) + b'] ' + entry[2]
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

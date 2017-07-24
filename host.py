#!/usr/bin/env python3

import socket
import string
import threading
import signal
import sys

closing = False
connected = []
messages = []
lock = threading.Lock()
sock = socket.socket()

CMD = b'|'  # if message starts with that string - it's a command to server, not message
MAX_NAME_LEN = 20


def signal_handler(sig, frame):
    if sig == signal.SIGINT:
        print('\b\b^C catched!\nshutting down host')

        closing = True

        for connection in connected:
            message = "Server closed the connection."
            connection[0].send(message.encode('utf-8'))
            connection[0].close()
            connected.remove(connection)

        try:
            sock.shutdown(socket.SHUT_RDWR)
        except:
            pass

        sock.close()
        sys.exit(0)


def assign_name(conn, addr, name):
    for char in name.decode('utf-8'):
        if char not in string.printable and char in string.whitespace:
            status = "Error: this name is not valid"
            conn.send(status.encode('utf-8'))
            return

    if len(name) > MAX_NAME_LEN:
        status = "Error: this name is too long. Max length is "
        status += str(MAX_NAME_LEN) + "."
        conn.send(status.encode('utf-8'))
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

    messages.append((0, 0, get_sender_name(addr) + b' changed his\her nickname to <' + name + b'>!'))

    for i in range(0, len(connected)):
        if connected[i][1] == addr:
            connected[i] = (conn, addr, name)
            print('*INFO* name set! [' + addr[0] + '] -> ' + name.decode('utf-8'))


def cmd_parse(conn, addr, message):
    # |help
    if message.startswith(CMD + b'help'):
        tosend =  "List of availbale commands:\n"
        tosend += "-- |list\n"
        tosend += "    Print all connected clients.\n"
        tosend += "    Name printed if was assigned.\n"
        tosend += "\n"
        tosend += "-- |help\n"
        tosend += "    Print this help.\n"
        tosend += "\n"
        tosend += "-- |setname <new_name>\n"
        tosend += "    Sets a new name for current connection.\n"
        tosend += "    Two connections couldn't have same names.\n"
        conn.send(tosend.encode('utf-8'))

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
            return connection[1][0].encode('utf-8')
    return 'SERVER'.encode('utf-8')


def answer(conn, addr):
    print("connected: " + str(addr))
    lock.acquire()
    messages.append((0, 0, get_sender_name(addr) + b' connected!'))
    lock.release()

    while True:
        try:
            data = conn.recv(1024)
        except OSError:
            return

        print(str(addr) + ": " + data.decode('utf-8', 'replace'))
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


def main():
    signal.signal(signal.SIGINT, signal_handler)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', 9707))
    sock.listen(1)
    sock.settimeout(0.5)

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


if __name__ == '__main__' and sys.platform in ['linux', 'darwin']:
    main()

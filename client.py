#!/usr/bin/env python3

import socket
import threading

sock = socket.socket()
sock.connect(('192.168.1.6', 9707))
#sock.connect(('localhost', 9707))

def send():
	while True:
		s = input()
		if s == ':q':
			break
		elif s != ':u':
			sock.send(s.encode('ascii'))

def recv():
	while True:
		try:
			data = sock.recv(1024)
		except OSError:
			break
		print(data.decode('utf-8', 'ignore'))

t1 = threading.Thread(target=send)
t2 = threading.Thread(target=recv)

t1.start()
t2.start()

print('threads started')
t1.join()
print('thread "send" closed')

sock.shutdown(socket.SHUT_RDWR)
sock.close()
print('socket closed')
t2.join()

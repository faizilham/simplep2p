import socket
from time import localtime, strftime

def trace(*str, **option):
	filename, date, show_log = None, True, True
	for e in option:
		if e=="filename" and option[e]!=None:
			filename = option[e]
		elif e=="date" and option[e]!=True:
			date = False
		elif e=="show_log" and option[e]!=True:
			show_log = False
	
	s = ""
	if(date): 
		s = strftime("%a, %d %b %Y %H:%M:%S", localtime()) + ': '
	s = s + ''.join(str)
	
	if(show_log):
		print s
	
	if filename:
		f = None
		try:
			f = open(filename, 'a')
		except:
			f = open(filename, 'w')
		
		f.write(s + '\n')
		f.close()

def parse_address(addr):
	res = addr.split(':')
	return res[0], int(res[1])
	
def make_address(host, port):
	return host + ":" + str(port)
	
def make_address2(addr):
	return make_address(addr[0], addr[1])

def send_data(host, port, data, reply=True, buffer=1024, timeout=30.0):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		sock.connect((host, port))
		sock.sendall(data)
		if reply:
			sock.shutdown(socket.SHUT_WR)
			sock.settimeout(timeout)
			
			data = ""
	
			while 1:
				get = sock.recv(buffer)
				if get:
					data = data + get
				else: 
					break
			return data
		else:
			return None
	finally:
		sock.close()
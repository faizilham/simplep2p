import socket
import threading
import SocketServer
import time
from helper import parse_address, make_address, make_address2, trace
from blazefile import hashlength

"""
TrackerDB
format file:
hash_info, filename

format db:
hash_info : [filename, {peer: no_send}]
peer : "host:port"
no_send: udah berapa kali ga update
"""

class TrackerDB:
	def __init__(self, dbfile, autoload=True):
		self.dbfile = dbfile
		if(autoload):
			self.load(True)
		else:
			self.clear()
		
	def clear(self):
		self.data = {}
	
	def load(self, clear=False):
		if clear: self.clear()
		f = open(self.dbfile, 'r')
		for ln in f:
			line = ln.strip()
			if(len(line)>0 and line[0] != "#"): # if not empty lines and comment
				entry = line.split(",")
				key = entry[0].strip()
				value = entry[1].strip()
				if clear or not self.exist(key):
					self.put(key, value)
					if not clear: trackerlog(key, ' is added to database')
		f.close()
		
	def save(self):
		f = open(self.dbfile, 'w')
		for key, val in self.data.items():
			f.write(key + "," + val[0] + "\n")
		f.close()
	
	def put(self, key, filename):
		self.data[key] = [filename, {}];
	
	def exist(self, key):
		return key in self.data
		
	def filename(self, key):
		return self.data[key][0]
	
	def peers(self, key):
		return self.data[key][1]
		
	def add_peer(self, key, peer):
		peers = self.peers(key)
		
		if peer not in peers:
			trackerlog(peer, ' join ', key)
		
		peers[peer] = 0

	def del_peer(self, key, peer):
		peers = self.peers(key)
		
		if peer in peers:
			del peers[peer]
			trackerlog(peer, ' leave ', key)
		
	def update_peer(self,maxtimeout):
		for key, val in self.data.items():
			peers = self.peers(key)
			for peer in val[1].keys():
				peers[peer] = peers[peer] + 1
				if (peers[peer] > maxtimeout):
					self.del_peer(key, peer)
	
	def print_peer(self):
		for key, val in self.data.items():
			print 'file  :', val[0]
			print 'hash  :', key
			if not val[1]:
				print 'no peer connected'
			else:
				print 'peers :'
				for e in val[1].keys():
					print '       -', e

class Tracker(threading.Thread):
	def __init__(self, host, port, dbfile):
		threading.Thread.__init__(self);
		
		self.server = TrackerTCPServer((host, port), TrackerTCPRequestHandler)
		self.server.lock = threading.Lock()
		self.server.db = TrackerDB(dbfile)
		
		self.job = TrackingJob(self.server)
		
	def run(self):
		self.job.start()
		trackerlog("Tracker starts.")
		
		try:
			self.server.serve_forever()
		except:
			self.stop()
	
	def print_peer(self):
		self.server.db.print_peer()
	
	def stop(self):
		self.server.shutdown()
		self.job.stop()
		self.job.join()
		trackerlog("Tracker stops. Exiting...")

class TrackingJob(threading.Thread):
	def __init__(self, server, interval=60, maxtimeout=1):
		threading.Thread.__init__(self);
		self.server = server
		self.interval = interval
		self.maxtimeout = maxtimeout
		self.running = False
	
	def run(self):
		self.running = True
		while(self.running):
			# poll stop while sleep
			for i in range(self.interval):
				time.sleep(1)
				if not self.running: break
			if not self.running: break
						
			self.server.lock.acquire()
			
			# job starts here
			# trackerlog("Job running")
			self.server.db.update_peer(self.maxtimeout)
			
			self.server.lock.release()
			
	def stop(self):
		self.running = False


"""
ping:
!!! //jarang dipake

request:
HAI hash_info host:port // join, peers/no
PLZ hash_info host:port // regular check, peers/no 
BYE hash_info host:port // leave, no-reply

reply:
NOO error_msg //error: no connected peer, file not found, other error
YEA //success
GUY host:port [,host:port]* //peers data
"""

# ping
PRE_PING = "!!!"

# request
PRE_JOIN = "HAI"
PRE_GET = "PLZ"
PRE_LEAVE = "BYE"

# error reply
PRE_ERR = "NOO"
PRE_ERR_NOFILE = PRE_ERR + "File not exist"
PRE_ERR_INVALID = PRE_ERR + "Invalid message"

PRE_OK = "OKE"
PRE_PEER = "NIH"

class TrackerTCPRequestHandler(SocketServer.BaseRequestHandler):
	# main request handler
	def handle(self):
		lock = self.server.lock;
		
		data = ""
		
		while 1:
			get = self.request.recv(1024)
			if get:
				data = data + get
			else: 
				break
		
		data = data.strip()
		prefix = data[:3]
		data = data[3:]
		
		lock.acquire()
		if (prefix==PRE_PING):
			response = self.handle_ping()
		elif (prefix==PRE_JOIN or prefix==PRE_GET):
			response = self.handle_joinupdate(data)
		elif (prefix==PRE_LEAVE):
			response = self.handle_leave(data)
		else:
			response = PRE_ERR_INVALID
		lock.release()
		
		self.request.sendall(response)
	
	# handle ping
	def handle_ping(self):
		return PRE_OK
	
	# handle join and get
	def handle_joinupdate(self, data):
		hash = data[:hashlength()]
		db = self.server.db;
		
		if not db.exist(hash): 
			db.load()
			if not db.exist(hash): return PRE_ERR_NOFILE
		
		addr = data[hashlength():].strip()
		
		try:
			parse_address(addr)
			db.add_peer(hash, addr) # kalo udah ada cuma update retry
		except:
			return PRE_ERR_INVALID
		
		return self.peer_info(hash, addr)
	
	# handle leave
	def handle_leave(self, data):
		hash = data[:hashlength()]
		db = self.server.db;
		
		if not db.exist(hash): return PRE_ERR_NOFILE
		
		addr = data[hashlength():].strip()
		
		try:
			parse_address(addr)
			db.del_peer(hash, addr)
		except:
			return PRE_ERR_INVALID
		
		return PRE_OK
	
	# build peer info reply message
	def peer_info(self, hash, addr):
		db = self.server.db;
		if len(db.peers(hash)) < 2: return PRE_PEER
		
		reply = PRE_PEER
		n = 0
		for e in db.peers(hash):
			if e != addr:
				if n > 0:
					reply = reply + ','
				reply = reply + e
				n = n + 1
		return reply
	
class TrackerTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	lock = None
	db = None
	
def trackerlog(*str):
	trace(*str, date=False)

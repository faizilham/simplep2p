"""
.blaze file library

"""

import hashlib
import os

def hashfunc(s):
	return hashlib.sha1(s).hexdigest()

def hashlength():
	return 40
	
def getpiecesize(size):
	kilo = 1024
	mega = 1024 * kilo
	giga = 1024 * mega
	
	if size < 50 * mega:
		return 32 * kilo
	elif size < 150 * mega:
		return 64 * kilo
	elif size < 350 * mega:
		return 128 * kilo
	elif size < 512 * mega:
		return 256 * kilo
	elif size < giga:
		return 512 * kilo
	elif size < 2 * giga:
		return mega
	else:
		return 2 * mega
	
class BlazeFile:
	
	def __init__(self):
		self.clear()
	
	def clear(self):
		self.tracker = None
		self.filename = None
		self.size = 0
		self.block_size = 0
		self.block = []
		self.hash_info = None
		
	def load(self, filename):
		self.clear()
		f = open(filename, 'r')
		
		self.tracker = f.readline().strip()
		self.filename = f.readline().strip()
		self.size = long(f.readline().strip())
		self.block_size = long(f.readline().strip())
		block = []
		self.block = block
		
		hlen = hashlength()
		reading = True
		
		while(reading):
			s = f.read(hlen)
			if(len(s) == hlen):
				block.append(s)
			else:
				reading = False
		
		f.close()
		
		self.hash_info = self.gethash()
	
	def save(self, filepath):
		f = open(filepath,'w')
		f.write(self.tracker + '\n')
		f.write(self.filename + '\n')
		f.write(str(self.size) + '\n')
		f.write(str(self.block_size) + '\n')
		
		for e in self.block:
			f.write(e)
			
		f.close()
	
	def encodefrom(self, filepath, filename, tracker, size=None):
		self.clear()
		
		self.tracker = tracker
		self.filename = filename
		
		fsize = os.path.getsize(filepath)
		self.size = fsize
		
		block = []
		self.block = block
		
		if (not size): 
			size = getpiecesize(fsize)
		
		self.block_size = size
		
		f = open(filepath, 'rb')
		
		reading = True
		while(reading):
			s = f.read(size)
			if(len(s) > 0):
				block.append(hashfunc(s))
			else:
				reading = False
		
		f.close()
		
		self.hash_info = self.gethash()
		
	def gethash(self):
		if (self.filename):
			return hashfunc(self.filename)
		else:
			return None
"""
.blaze file library

"""

import hashlib
import os

def hashfunc(s):
	return hashlib.sha1(s).hexdigest()

def hashlength():
	return len(hashfunc('0'))
	
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
		self.dict = {}
	
	def clear(self):
		self.dict = {}
		
	def __getitem__(self, key):
		return self.dict.get(key)
	
	def load(self, filename):
		self.clear()
		f = open(filename, 'r')
		
		self.dict['tracker'] = f.readline().strip()
		self.dict['filename'] = f.readline().strip()
		self.dict['size'] = long(f.readline().strip())
		block = []
		self.dict['block'] = block
		
		hlen = hashlength()
		reading = True
		
		while(reading):
			s = f.read(hlen)
			if(len(s) == hlen):
				block.append(s)
			else:
				reading = False
		
		f.close()
	
	def save(self, filename=None):
		if (not filename):
			filename = self.dict['filename'] + ".blaze"
	
		f = open(filename,'w')
		f.write(self.dict['tracker'] + '\n')
		f.write(self.dict['filename'] + '\n')
		f.write(str(self.dict['size']) + '\n')
		
		for e in self.dict['block']:
			f.write(e)
			
		f.close()
	
	def encodefrom(self, filename, tracker, size=None):
		self.clear()
		
		self.dict['tracker'] = tracker
		self.dict['filename'] = filename
		
		fsize = os.path.getsize(filename)
		self.dict['size'] = fsize
		
		block = []
		self.dict['block'] = block
		
		if (not size): 
			size = getpiecesize(fsize)
		
		f = open(filename, 'rb')
		
		reading = True
		while(reading):
			s = f.read(size)
			if(len(s) > 0):
				block.append(hashfunc(s))
			else:
				reading = False
		
		f.close()
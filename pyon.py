# -*- coding: utf-8 -*-

import asyncore
import asynchat
import socket
import struct
import traceback
import threading
import code
import sys

class AionConnection(asynchat.async_chat):
	static_key = [ord(x) for x in "nKO/WctQ0AVLbpzfBkS6NevDYT8ourG5CRlmdjyJ72aswx4EPq1UgZhFMXH?3iI9"]
	
	def __init__(self, sock=None):
		asynchat.async_chat.__init__(self, sock=sock)
		
		self.data = ''
		
		self.length = None
		self.set_terminator(2)
		
		self.decryption_key = None
		self.encryption_key = None
		self.fixed_byte = None
		
	def decrypt_message(self, data):
		
		if not self.decryption_key:
			return data

		data_bytes = [ord(x) for x in data]
		key_bytes = [ord(x) for x in struct.pack('L', self.decryption_key)]

		prev = data_bytes[0]
		data_bytes[0] ^= key_bytes[0]

		for i in range (1, len(data_bytes)):
			curr = data_bytes[i]
			data_bytes[i] ^= AionConnection.static_key[i&63]^key_bytes[i&7]^prev
			prev = curr

		self.decryption_key += len(data_bytes)
		self.decryption_key &= 0xFFFFFFFFFFFFFFFF

		xored = ''

		for x in data_bytes:
			xored += chr(x)
		
		
		return xored

	def encrypt_message(self, data):
		
		if not self.encryption_key:
			return data
		
		data_bytes = [ord(x) for x in data]
		key_bytes = [ord(x) for x in struct.pack('L', self.encryption_key)]

		data_bytes[0] ^= key_bytes[0]

		for i in range (1, len(data_bytes)):
			data_bytes[i] ^= AionConnection.static_key[i&63]^key_bytes[i&7]^data_bytes[i-1]

		self.encryption_key += len(data_bytes)
		self.encryption_key &= 0xFFFFFFFFFFFFFFFF

		xored = ''

		for x in data_bytes:
			xored += chr(x)
		
		return xored
		
	def pack_instruction(self, opcode, data):
		return struct.pack('=3B', opcode, self.fixed_byte, ~opcode&0xFF)+data
		
	def collect_incoming_data(self, data):
		self.data += data
		
	def found_terminator(self):

		if not self.length:
			self.length = struct.unpack('H', self.data[:2])[0]-2
			self.data = self.data[2:]
			self.set_terminator(self.length)
		
		if len(self.data) < self.length:
			return
		
		self.handle_message(self.data[:self.length])
		
		self.data = self.data[self.length:]
		
		self.length = None
		self.set_terminator(2)
		
	def handle_message(self, data):

		decrypted_data = self.decrypt_message(data)
		
		if not self.fixed_byte:
			self.fixed_byte = ord(decrypted_data[1])
		
		instruction = (ord(decrypted_data[0]), decrypted_data[3:])
		
		try:
			instruction = self.preprocess_instruction(*instruction)
		except:
			traceback.print_exc()
		
		if instruction:
			try:
				self.dispatch_instruction(*instruction)
				self.postprocess_instruction(*instruction)
			except:
				traceback.print_exc()
		
	def preprocess_instruction(self, opcode, data):
		return (opcode, data)
		
	def postprocess_instruction(self, opcode, data):
		pass
		
	def dispatch_instruction(self, opcode, data):
		self.dispatch_message(self.encrypt_message(self.pack_instruction(opcode, data)))
		
	def dispatch_message(self, data):
		pass
		
	def write_message(self, data):
		self.send(struct.pack('H', len(data)+2)+data)

class AionProxy(asyncore.dispatcher):
	
	def __init__(self, listen_address, forward_address):
		asyncore.dispatcher.__init__(self)
		
		self.forward_address = forward_address
		self.clients = []
		
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.bind(listen_address)
		self.listen(5)
		
	def handle_accept(self):
		conn, addr = self.accept()
		
		print 'New connection from ', addr
		
		client = AionClientConnection(conn)
		server = AionServerConnection()
		
		client.server = server
		server.client = client
		
		server.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		server.connect(self.forward_address)
		
		self.clients.append(client)
		
class AionClientConnection(AionConnection):
	
	def __init__(self, sock=None):
		AionConnection.__init__(self, sock)
		
		self.server = None
		self.modules = []
		
		self.load_module('opcodes')
		self.load_module('constructors')
		self.load_module('key')
		self.load_module('loader')
		
	def load_module(self, name):
		__import__('modules.'+name)
		
		module = sys.modules['modules.'+name]
		
		if self.modules.count(module) > 0:
			reload(self.modules[self.modules.index(module)])
			
		else:
			self.modules.append(module)
	
	def unload_module(self, name):
		module = sys.modules['modules.'+name]
		
		self.modules.remove(module)
		
	def reload_module(self, name=None):
		if name:
			module = sys.modules['modules.'+name]
			reload(self.modules[self.modules.index(module)])
		else:
			map(reload, self.modules)
		
	def handle_close(self):
		if self.server:
			self.server.client = None
			self.server.close()
			self.server = None
		
		self.close()
	
	def dispatch_message(self, data):
		self.server.write_message(data)
		
	def preprocess_instruction(self, opcode, data):
		for module in self.modules:
			if hasattr(module, 'preprocess_client'):
				retval = module.preprocess_client(self, opcode, data)
				
				if not retval:
					return None
					
				opcode = retval[0]
				data = retval[1]
				
		return (opcode, data)
		
	def postprocess_instruction(self, opcode, data):
		for module in self.modules:
			if hasattr(module, 'postprocess_client'):
				module.postprocess_client(self, opcode, data)

class AionServerConnection(AionConnection):
	
	def __init__(self, sock=None):
		AionConnection.__init__(self, sock)
		
		self.client = None
		
	def handle_connect(self):
		pass
		
	def handle_close(self):
		if self.client:
			self.client.server = None
			self.client.close()
			self.client = None
		
		self.close()
		
	def dispatch_message(self, data):
		self.client.write_message(data)
		
	def preprocess_instruction(self, opcode, data):
		for module in self.client.modules:
			if hasattr(module, 'preprocess_server'):
				retval = module.preprocess_server(self, opcode, data)
				
				if not retval:
					return None
					
				opcode = retval[0]
				data = retval[1]
				
		return (opcode, data)
		
	def postprocess_instruction(self, opcode, data):
		for module in self.client.modules:
			if hasattr(module, 'postprocess_server'):
				module.postprocess_server(self, opcode, data)

class ConsoleThread(threading.Thread):
	
	def __init__(self, proxy):
		threading.Thread.__init__(self)
		self.proxy = proxy
	
	def run(self):
		proxy = self.proxy
		console = code.InteractiveConsole(locals())
		console.interact()

if __name__ == '__main__':
	proxy = AionProxy((sys.argv[1], int(sys.argv[2])), (sys.argv[3], int(sys.argv[4])))
	
	ConsoleThread(proxy).start()
	
	asyncore.loop()
	
	
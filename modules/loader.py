"""Loads, unloads, and reloads modules."""

import sys
from modules import constructors, opcodes

def preprocess_client(client, opcode, data):
	if opcode != opcodes.CLIENT_WHISPER:
		return (opcode, data)
	
	strings = data.decode('utf-16-le').split('\00')
	
	name = strings[0]
	message = strings[1]
	
	if name != 'Pyon':
		return (opcode, data)
	
	tokens = message.split(' ')
	
	if tokens[0] == 'load':
		client.load_module(tokens[1])
		constructors.server_chat(client.server, 4, 0, 0, name, 'Module "%s" loaded.' % tokens[1])
		return None
		
	elif tokens[0] == 'unload':
		client.unload_module(tokens[1])
		constructors.server_chat(client.server, 4, 0, 0, name, 'Module "%s" unloaded.' % tokens[1])
		return None
		
	elif tokens[0] == 'reload':	
		if len(tokens) > 1:
			client.reload_module(tokens[1])
			constructors.server_chat(client.server, 4, 0, 0, name, 'Module "%s" reloaded.' % tokens[1])
		else:
			client.reload_module()
			constructors.server_chat(client.server, 4, 0, 0, name, '%d modules reloaded.' % len(client.modules))
		return None
				
	elif tokens[0] == 'debug':
		print client.modules
		return None
		
	return (opcode, data)
	
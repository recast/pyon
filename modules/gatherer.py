import struct
import threading
import math
from modules import constructors
from modules import opcodes

node_objid = None
stop_count = 0
gather_count = 0
node_queue = []

#def preprocess_client(client, opcode, data):
#	pass

def target(client):
	print 'targeting'
	
	global node_objid
	
	constructors.client_target(client, node_objid)

def harvest(client):
	print 'harvesting'
	
	constructors.client_harvest(client, 0)

def postprocess_server(server, opcode, data):
	if opcode == opcodes.SERVER_SPAWN_OBJECT: 
		postprocess_server_object_spawn(server, opcode, data)
	elif opcode == opcodes.SERVER_DESPAWN:
		postprocess_server_despawn(server, opcode, data)
		
def preprocess_server(server, opcode, data):
	global node_objid
	
	if opcode == opcodes.SERVER_HARVEST_PROGRESS:
		return None
	elif opcode == opcodes.SERVER_HARVEST_ACTION:
		return preprocess_server_harvest_window(server, opcode, data)
	
	return (opcode, data)
	
def preprocess_server_harvest_window(server, opcode, data):
	global node_objid, gather_count
	
	print 'havest_window'
	
	(item_id, objid, unknown, mode) = struct.unpack('=2IHB', data)
	
	try:
		if mode == 2 or mode == 4:
			constructors.client_harvest(server.client, -1)
		
			if gather_count > 0:
				gather_count -= 1
			
				constructors.client_target(server.client, node_objid)
				constructors.client_harvest(server.client, 0)
			else:
				node_objid = None
	except:
		pass
	
	print 'blocked'
	return None
		
def postprocess_server_object_spawn(server, opcode, data):
	global node_objid, stop_count, gather_count
	
	(x, y, z, objid, unknown1, type_id, unknown2, unknown3, name_id, unknown4, unknown5, unknown6) = struct.unpack('=3f3IBH2IHB', data)

	if not node_objid and type_id == 400205:
		node_objid = objid
		gather_count = 2 
		
		constructors.client_target(server.client, node_objid)
		constructors.client_harvest(server.client, 0)

def postprocess_server_despawn(server, opcode, data):
	global node_objid
	
	(objid, unknown) = struct.unpack('=IB', data)

	if objid == node_objid:
		node_objid = None
		
	if objid in node_queue:
		node_queue.remove(objid)

	return (opcode, data)
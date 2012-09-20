import struct
import time
import threading
from modules import constructors
from modules import opcodes

damage_timestamps = {}

cast_times = {
	1354: 2.0,
	1559: 2.0,
	1583: 4.0,
	1365: 2.0,
	1569: 0.0,
	1570: 1.0,
	1584: 0.0,
	1369: 0.0,
	1383: 0.0
}

enabled = True

def preprocess_client(client, opcode, data):
	if opcode == opcodes.CLIENT_SKILL:
		return preprocess_client_skill(client, opcode, data)
	elif opcode == opcodes.CLIENT_WHISPER:
		return preprocess_client_whisper(client, opcode, data)
	
	return (opcode, data)

def preprocess_client_whisper(client, opcode, data):
	global enabled
	
	strings = data.decode('utf-16-le').split('\00')
	
	name = strings[0]
	message = strings[1]
	
	tokens = message.split(' ')
	
	if name != 'Pyon' or tokens[0] != 'barrage':
		return (opcode, data)
	
	if tokens[1] == 'off':
		enabled = False
		constructors.server_chat(client.server, 4, 0, 0, name, 'Barrage disabled.')
		
		
	elif tokens[1] == 'on':
		enabled = True
		constructors.server_chat(client.server, 4, 0, 0, name, 'Barrage enabled.')
		
	return None
	
def barrage_warning(client, objid):
	constructors.server_chat(client.server, 4, 0, 0, 'Pyon', 'Damage will proc on %s in 3 seconds.' % hex(objid))

def preprocess_client_skill(client, opcode, data):
	global damage_timestamps, enabled
	
	skill_id, level, type = struct.unpack('=HBB', data[:4])
	
	if not enabled or skill_id not in cast_times.keys():
		return (opcode, data)
	
	if type == 0:
		objid, delay = struct.unpack('=IH', data[4:])
		
		if objid not in damage_timestamps.keys():
			damage_timestamps[objid] = time.time()+cast_times[skill_id]+20
			threading.Timer(damage_timestamps[objid]-time.time()-3, barrage_warning, args=[client, objid]).start()
			
		if damage_timestamps[objid] < time.time():
			damage_timestamps[objid] = time.time()+cast_times[skill_id]+20
			threading.Timer(damage_timestamps[objid]-time.time()-3, barrage_warning, args=[client, objid]).start()
			
		delay = int((damage_timestamps[objid]-time.time()-cast_times[skill_id])*1000)
		
		if delay < 0:
			delay = 0
		
		data = struct.pack('=HBBIH', skill_id, level, type, objid, delay)
	elif type == 1:
		x, y, z, delay = struct.unpack('=fffH', data[4:])
		print 'client_skill', skill_id, level, type, x, y, z, delay
	else:
		print 'client_skill', skill_id, level, type
		print dump(data)
	
	return (opcode, data)
#WELCOME TO WARP ZONE!
import struct
from modules import constructors, opcodes

def preprocess_client(client, opcode, data):
	if opcode == opcodes.CLIENT_LOCATION:
		return preprocess_client_location(client, opcode, data)
	elif opcode == opcodes.CLIENT_WHISPER:
		return preprocess_client_whisper(client, opcode, data)
	
	return (opcode, data)

def preprocess_client_whisper(client, opcode, data):
	global enabled

	strings = data.decode('utf-16-le').split('\00')

	name = strings[0]
	message = strings[1]

	tokens = message.split(' ')

	if name != 'Pyon':
		return (opcode, data)
		
	if tokens[0] == 'nudge':
		
		if len(tokens) < 4:
			return None
		
		x = float(tokens[1])
		y = float(tokens[2])
		z = float(tokens[3])
		
		constructors.server_location(client.server, client.x+x, client.y+y, client.z+z, 0)

	return None

def preprocess_client_location(client, opcode, data):
	x, y, z, heading, flags = struct.unpack('=3fBB', data[:14])
	
	client.x = x
	client.y = y
	client.z = z
	client.heading = heading
	
	data = struct.pack('=3fBB', x, y, z, heading, flags)+data[14:]
	
	if flags&64 and flags&8 == 0 and flags&4 == 0 and flags&32:
		nx, ny, nz = struct.unpack('=3f', data[14:])
		
		constructors.server_location(client.server, nx, ny, nz, heading)
		return None
		
	return (opcode, data)
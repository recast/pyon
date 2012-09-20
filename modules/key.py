"""Updates the crypto key when received from the server."""

import ctypes
import struct

from modules import opcodes

def postprocess_server(server, opcode, data):
	if opcode != 248:
		return
	
	(key,) = struct.unpack('I', data)
	
	key -= 0x3FF2CC87
	key ^= 0xCD92E451
	key &= 0xFFFFFFFF
	key |= (0x87546CA1 << 32)
	
	server.decryption_key = key
	server.encryption_key = key
	server.client.encryption_key = key
	server.client.decryption_key = key
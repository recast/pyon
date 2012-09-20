# -*- coding: utf-8 -*-

import random
import struct
from modules import opcodes

def dump(src, length=8):
	FIITER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])
	
	N=0; result=''
	while src:
		s,src = src[:length],src[length:]
		hexa = ' '.join(["%02X"%ord(x) for x in s])
		s = s.translate(FIITER)
		result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
		N+=length
	return result

def client_talknpc(client, objid):
	data = struct.pack('I', objid)
	
	client.dispatch_instruction(opcodes.CLIENT_TALK_NPC, data)

def client_target(client, objid, assist=0):
	data = struct.pack('=IB', objid, assist)
	
	client.dispatch_instruction(opcodes.CLIENT_TARGET, data)	

def client_attack(client, objid, counter, unknown1, unknown2, animation):
	data = struct.pack('=IBBBB', objid, counter, unknown1, unknown2, animation)
	
	client.dispatch_instruction(opcodes.CLIENT_ATTACK, data)
	
def client_harvest(client, mode):
	data = struct.pack('=I', mode)
	
	client.dispatch_instruction(opcodes.CLIENT_HARVEST, data)

def client_loot(client, objid, mode):
	data = struct.pack('=IB', objid, mode)
	
	client.dispatch_instruction(opcodes.CLIENT_LOOT, data)

def client_takeloot(client, objid, slot):
	data = struct.pack('=IB', objid, slot)
	
	client.dispatch_instruction(opcodes.CLIENT_TAKE_LOOT, data)
	
def client_whisper(client, name, message):
	data = name.encode('utf-16-le')+'\00\00'
	data += message.encode('utf-16-le')+'\00\00'
	
	client.dispatch_instruction(opcodes.CLIENT_WHISPER, data)
	
def client_skill(client, skill_id, level, type, objid, unknown, delay):
	data = struct.pack('=HBBIBB', skill_id, level, type, objid, unknown, delay)
	
	client.dispatch_instruction(opcodes.CLIENT_SKILL, data)
	
def client_action(client, type):
	data = struct.pack('=B', type)
	
	client.dispatch_instruction(opcodes.CLIENT_ACTION, data)
	
def client_chat(client, chat_type, message):
	data = chr(chat_type)+message.encode('utf-16-le')+'\00\00'
	
	client.dispatch_instruction(opcodes.CLIENT_CHAT, data)
	
def client_disconnect(client, unknown):
	data = chr(unknown)
	
	client.dispatch_instruction(237, data)
	
def client_quit(client, unknown):
	data = chr(unknown)

	client.dispatch_instruction(236, data)
	
def client_teleport(client, objid, unknown1, unknown2=0):
	data = struct.pack('=IIH', objid, unknown1, unknown2)
	
	client.dispatch_instruction(opcodes.CLIENT_TELEPORT, data)
	
def client_survey_response(client, timestamp, response):
	data = struct.pack('=I', timestamp)
	data += response.encode('utf-16-le')+'\00\00'
	
	client.dispatch_instruction(123, data)
	
def client_npcoption(client, objid, href, unknown1, referrer, quest_id, unknown2=0):
	data = struct.pack('=IHHHHH', objid, href, unknown1, referrer, quest_id, unknown2)
	
	client.dispatch_instruction(opcodes.CLIENT_NPC_OPTION, data)

def client_craft(client, flags, craft_id, recipe_id, objid, ingredients):
	data = struct.pack('=BIIIH', flags, craft_id, recipe_id, objid, len(ingredients))
	
	for ingredient in ingredients:
		data += struct.pack('=III', ingredient[0], ingredient[1], ingredient[2])
		
	client.dispatch_instruction(115, data)
	
def client_abandon_quest(client, quest_id):
	data = struct.pack('=H', quest_id)
	
	client.dispatch_instruction(opcodes.CLIENT_ABANDON_QUEST, data)
	
def client_npcshop(client, objid, action, items):
	data = struct.pack('=IHH', objid, action, len(items))
	
	for item in items:
		data += struct.pack('=III', item[0], item[1], item[2])
		
	client.dispatch_instruction(opcodes.CLIENT_NPC_SHOP, data)

def client_random(client):
	i = random.randint(0, 255)
	
	server_chat(client.server, 4, 0, 0, 'Pyon', 'Dispatching random instruction %d.' % i)
	
	#207: Instant disconnect
	
	client.dispatch_instruction(i, '')

def server_chat(server, chat_type, unknown, character_id, name, message):
	data = struct.pack('=BBI', chat_type, unknown, character_id)
	data += name.encode('utf-16-le')+'\00\00'
	data += message.encode('utf-16-le')+'\00\00'
	
	server.dispatch_instruction(40, data) #Formerly 0x31
	
def server_chat_raw(server, chat_type, unknown, character_id, name, message):
	data = struct.pack('=BBI', chat_type, unknown, character_id)
	data += name.encode('utf-16-le')+'\00\00'
	data += message+'\00\00'

	server.dispatch_instruction(0x31, data)
	
def server_teleport(server, unknown1, unknown2, unknown3, x, y, z, heading):
	data = struct.pack('=BIH3fB', unknown1, unknown2, unknown3, x, y, z, heading)
	
	server.dispatch_instruction(52, data)
	
def server_location(server, x, y, z, heading):
	data = struct.pack('=3fB', x, y, z, heading)
	
	server.dispatch_instruction(opcodes.SERVER_LOCATION, data)
	
def y():
	pass
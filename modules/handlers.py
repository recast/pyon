# -*- coding: utf-8 -*-

import ctypes
import struct
import sys
import time
from modules import constructors
from modules import opcodes, strings

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
	
def preprocess_client_unknown(client, opcode, data):
	print 'Client', opcode
	print dump(data)
	
	return (opcode, data)
	
def postprocess_client_unknown(client, opcode, data):
	pass

def preprocess_server_unknown(client, opcode, data):
	#0x800092fc
	if opcode == 47:
		print 'Server', opcode
		print dump(data)
		pass
	
	return (opcode, data)

def postprocess_server_unknown(client, opcode, data):
	pass

def preprocess_client_whisper(client, opcode, data):
	strings = data.decode('utf-16-le').split('\00')
	
	name = strings[0]
	message = strings[1]
	
	print 'Whisper (name: "%s", message: "%s")' % (name, message)
	
	if name == 'Pyon':
		tokens = message.split(' ')
		
		try:
			if tokens[0] == 'eval':
				constructors.server_chat(client.server, 4, 0, 0, name, str(eval(' '.join(tokens[1:]), globals(), locals())))
				return None
			elif tokens[0] == 'exec':
				exec ' '.join(tokens[1:])
				return None
		except:
			constructors.server_chat(client.server, 4, 0, 0, name, '%s: %s' % (sys.exc_info()[0].__name__, sys.exc_info()[1]))
			return None
	
	return (opcode, data)
	
def preprocess_client_location(client, opcode, data):
	#print 'Iocation (%d bytes)' % len(data)
	
	x, y, z, heading, flags = struct.unpack('=3fBB', data[:14])
	
	#print 'client_location', x, y, z, heading, bin(flags)
	
	data = struct.pack('=3fBB', x, y, z, heading, flags)+data[14:]
	
	if flags&64:
		if flags&4:
			nx, ny, nz, gliding_flags = struct.unpack('=3fB', data[14:])
			#print nx, ny, nz, bin(gliding_flags)
			#print bin(gliding_flags)
		elif flags&8 == 0:
			nx, ny, nz = struct.unpack('=3f', data[14:])
			#print nx, ny, nz
		
	elif flags&4:
		(gliding_flags,) = struct.unpack('=B', data[14:])
		#print bin(gliding_flags)
		
	elif len(data) > 14:
		print dump(data)
		
	if flags&1 or flags&2 or flags&16:
		print 'Location (%d bytes)' % len(data)
		print x, y, z, heading, bin(flags)
		print dump(data)
	
	return (opcode, data)
	
def postprocess_server_message(server, opcode, data):
	pass
	
def postprocess_server_key(server, opcode, data):
	key = ctypes.c_ulong(struct.unpack('I', data)[0])
	
	key.value -= 0x3FF2CC87;
	key.value ^= 0xCD92E451;

	server.decryption_key = ctypes.c_ulonglong(key.value)
	server.decryption_key.value |= (0x87546CA1 << 32)
	server.encryption_key = ctypes.c_ulonglong(server.decryption_key.value)
	
	server.client.decryption_key = ctypes.c_ulonglong(server.decryption_key.value)
	server.client.encryption_key = ctypes.c_ulonglong(server.encryption_key.value)

def postprocess_server_chat(server, opcode, data):
	#print dump(data)
	
	chat_type, unknown, character_id = struct.unpack('=BBI', data[:6])
	
	strings = data[6:].decode('utf-16-le').split('\00')
	
	name = strings[0]
	message = strings[1]
	
	print 'Chat (type: %d, unknown: %d, character id: %d, name: "%s", message: "%s")' % (chat_type, unknown, character_id, name, message)

def postprocess_ignore(connection, opcode, data):
	pass

def preprocess_client_target(client, opcode, data):
	objid, assist = struct.unpack('IB', data)
	
	print 'client_target', hex(objid), assist
	
	return (opcode, data)
	
def preprocess_client_harvest(client, opcode, data):
	(mode,) = struct.unpack('I', data)
	print 'client_harvest', mode
	
	data = struct.pack('I', mode)
	
	return (opcode, data)	

def preprocess_client_action(client, opcode, data):
	(type,) = struct.unpack('B', data[:1])
	
	if type == 16:
		(emote_id,) = struct.unpack('H', data[1:])
		print 'client_action', type, emote_id
	elif len(data) > 1:
		print 'client_action', type
		print dump(data)
	else:
		print 'client_action', type
	
	return (opcode, data)	

def preprocess_client_channel(client, opcode, data):
	channel = struct.unpack('I', data)
	
	print 'client_channel', channel
	
	return (opcode, data)
	
def preprocess_client_mapchange(client, opcode, data):
	print 'client_mapchange'
	
	return (opcode, data)
	
def preprocess_client_skill(client, opcode, data):
	skill_id, level, type = struct.unpack('=HBB', data[:4])
	
	if type == 0:
		objid, unknown, delay = struct.unpack('=IBB', data[4:])
		print 'client_skill', skill_id, level, type, hex(objid), unknown, delay
	elif type == 1:
		x, y, z, unknown, delay = struct.unpack('=fffBB', data[4:])
		print 'client_skill', skill_id, level, type, x, y, z, unknown, delay
	else:
		print 'client_skill', skill_id, level, type
		print dump(data)
	
	return (opcode, data)

def preprocess_client_attack(client, opcode, data):
	global attack_start_time, last_attack_objid
	
	objid, counter, unknown, delay, animation = struct.unpack('=IBBBB', data)
	
	print 'client_attack', hex(objid), counter, bin(unknown), delay, animation
	
	data = struct.pack('=IBBBB', objid, counter, unknown, delay, animation)
	
	return (opcode, data)
	
def preprocess_client_talknpc(client, opcode, data):
	(objid,) = struct.unpack('I', data)
	
	print 'client_talknpc', hex(objid)
	
	return (opcode, data)
	
def preprocess_client_closenpc(client, opcode, data):
	(objid,) = struct.unpack('I', data)
	
	print 'client_closenpc', hex(objid)
	
	return (opcode, data)
	
def preprocess_client_npcoption(client, opcode, data):
	objid, action, unknown1, unknown2, quest_id, unknown3 = struct.unpack('=IHHHHH', data)
	
	#2 - buy item
	#3 - sell item
	#20 - open warehouse
	#29 - bind
	#30 - soul heal
	#31 - change the PVP zone...?
	#32 - change the PVP zone...?
	#39 - teleport/improve skill? wtf?
	#40 - learn skill
	#41 - expand cube
	#42 - expand warehouse
	#47 - open legion warehouse
	#54 - load fail!
	
	
	if unknown1 != 1 or unknown3 != 0:
		print '******* HEY, IOOK AT ME! *********'
	
	print 'client_npcoption', hex(objid), action, unknown1, unknown2, quest_id, unknown3
	
	if unknown1 != 1 or unknown3 != 0:
		print '******* HEY, IOOK AT ME! *********'
	
	data = struct.pack('=IHHHHH', objid, action, unknown1, unknown2, quest_id, unknown3)
	
	return (opcode, data)
	
def preprocess_client_loot(client, opcode, data):
	objid, mode = struct.unpack('=IB', data)
	
	print 'client_loot', hex(objid), mode
	
	data = struct.pack('=IB', objid, mode)
	
	return (opcode, data)
	
def preprocess_client_takeloot(client, opcode, data):
	objid, slot = struct.unpack('=IB', data)
	
	print 'client_takeloot', hex(objid), slot
	
	return (opcode, data)
	
def preprocess_client_useitem(client, opcode, data):
	item_id, unknown = struct.unpack('=IB', data)
	
	print 'client_useitem', item_id, unknown
	
	return (opcode, data)

def preprocess_client_moveitem(client, opcode, data):
	item_id, from_type, to_type, slot = struct.unpack('=IBBH', data)
	
	print 'client_moveitem', item_id, from_type, to_type, slot
	
	return (opcode, data)

def preprocess_client_moveitemqty(client, opcode, data):
	item_id, amount, unknown, from_type, to_item_id, to_type, slot = struct.unpack('=3IBIBH', data)
	
	print 'client_moveitemqty', item_id, amount, unknown, from_type, to_item_id, to_type, slot
	
	#amount |= 0xFF000000
	#unknown = 0x10000000
	
	data = struct.pack('=3IBIBH', item_id, amount, unknown, from_type, to_item_id, to_type, slot)
	
	return (opcode, data)
	
def preprocess_client_create_character(client, opcode, data):
	account_id = struct.unpack('I', data[:4])
	
	
	print dump(data)
	
	(account_id, strings, gender, race, class_id, unknown1, unknown2, voice, skin_color, hair_color, lip_color,
	face, hair, decoration, tattoo, unknown3, face_shape, forehead,
	eye_height, eye_space, eye_width, eye_size, eye_shape, eye_angle,
	brow_height, brow_angle, brow_shape, nose, nose_bridge, nose_width,
	nose_tip, cheeck, lip_height, mouth_size, lip_size, smile, lip_shape,
	jaw_height, chin_jut, ear_shape, head_size, neck, neck_length, shoulders,
	torso, chest, waist, hips, arm_thickness, hand_size, leg_thickness,
	foot_size, facial_rate, unknown4, unknown5, height) = struct.unpack('=I66s9I44Bf', data)
	
	strings = strings.decode('utf-16-le').split(u'\00')
	account = strings[0]
	name = strings[1]
	
	print 'client_create_character', account_id, account, name, gender, race, class_id, unknown1, unknown2, voice, skin_color, hair_color, lip_color, face, hair, decoration, tattoo, unknown3, face_shape, forehead, eye_height, eye_space, eye_width, eye_size, eye_shape, eye_angle, brow_height, brow_angle, brow_shape, nose, nose_bridge, nose_width, nose_tip, cheeck, lip_height, mouth_size, lip_size, smile, lip_shape, jaw_height, chin_jut, ear_shape, head_size, neck, neck_length, shoulders, torso, chest, waist, hips, arm_thickness, hand_size, leg_thickness, foot_size, facial_rate, unknown4, unknown5, height
	
	strings = u'\00'.join([account, name])
	strings = strings.encode('utf-16-le')
	
	#height = 50
	
	data = struct.pack('=I66s9I44Bf', account_id, strings, gender, race, class_id, unknown1, 
	unknown2, voice, skin_color, hair_color, lip_color,
	face, hair, decoration, tattoo, unknown3, face_shape, forehead,
	eye_height, eye_space, eye_width, eye_size, eye_shape, eye_angle,
	brow_height, brow_angle, brow_shape, nose, nose_bridge, nose_width,
	nose_tip, cheeck, lip_height, mouth_size, lip_size, smile, lip_shape,
	jaw_height, chin_jut, ear_shape, head_size, neck, neck_length, shoulders,
	torso, chest, waist, hips, arm_thickness, hand_size, leg_thickness,
	foot_size, facial_rate, unknown4, unknown5, height)
	
	print dump(data)
	
	return (opcode, data)
	
def preprocess_client_delete_character(client, opcode, data):
	account_id, character_id = struct.unpack('II', data)
	
	print 'client_delete_character', account_id, character_id
	
	return (opcode, data)
	
def preprocess_client_restore_character(client, opcode, data):
	account_id, character_id = struct.unpack('II', data)

	print 'client_restore_character', account_id, character_id

	return (opcode, data)
	
def preprocess_server_flight_time(server, opcode, data):
	time_left, max_time = struct.unpack('=II', data)

	#print 'server_flight_time', time_left, max_time

	data = struct.pack('=II', time_left, max_time)

	return (opcode, data)

def preprocess_client_teleport(client, opcode, data):
	objid, destination, unknown = struct.unpack('=IIH', data)
	
	print 'client_teleport', hex(objid), destination, unknown
	
	data = struct.pack('=IIH', objid, destination, unknown)
	
	return (opcode, data)
	
def preprocess_client_loadend(client, opcode, data):
	print 'client_loadend'
	
	return (opcode, data)
	
def preprocess_client_wtf(client, opcode, data):
	print 'client_wtf'
	
	return (opcode, data)
	
def preprocess_client_tick(client, opcode, data):
	(tick,) = struct.unpack('=I', data)
	
	print 'client_tick', tick, time.time()
	
	return (opcode, data)
	
def preprocess_client_chat(client, opcode, data):
	channel = ord(data[0])
	message = data[1:].decode('utf-16-le').strip('\00')
	
	print 'client_chat', channel, message
	
	return (opcode, data)
		
def preprocess_client_survey_response(client, opcode, data):
	(timestamp,) = struct.unpack('=I', data[:4])
	response = data[4:].decode('utf-16-le').strip('\00')
	
	print 'client_survey_response', time.ctime(timestamp), response
	
	return (opcode, data)
	
def preprocess_client_abandon_quest(client, opcode, data):
	(quest_id,) = struct.unpack('=H', data)
	
	print 'client_abandon_quest', quest_id
	
	return (opcode, data)
	
def preprocess_client_craft(client, opcode, data):
	(flags, craft_id, recipe_id, objid, ingredient_count) = struct.unpack('=BIIIH', data[:15])
	
	ingredients = []
	
	for i in range(0, ingredient_count):
		ingredients.append(struct.unpack('=III', data[15+(12*i):15+(12*(i+1))]))
	
	if flags != 128:
		print '********************************************'	
	
	print 'client_craft', flags, craft_id, recipe_id, hex(objid), ingredients
		
	data = struct.pack('=BIIIH', flags, craft_id, recipe_id, objid, len(ingredients))
	
	for ingredient in ingredients:
		data += struct.pack('=III', ingredient[0], ingredient[1], ingredient[2])
	
	print 'client_craft', flags, craft_id, recipe_id, hex(objid), ingredients
	
	return (opcode, data)
	
def preprocess_client_destroyitem(client, opcode, data):
	(item_id,) = struct.unpack('=I', data)
	
	print 'client_destroyitem', item_id
	
	return (opcode, data)
	
def preprocess_server_itemdestroyed(server, opcode, data):
	(item_id, unknown) = struct.unpack('=IB', data)
	
	print 'server_itemdestroyed', item_id, bin(unknown)
	
	data = struct.pack('=IB', item_id, unknown)
	
	return (opcode, data)
	
def preprocess_client_npcshop(client, opcode, data):
	(objid, action, item_count) = struct.unpack('=IHH', data[:8])
	
	items = []
	
	for i in range(0, item_count):
		items.append(struct.unpack('=III', data[8+(12*i):8+(12*(i+1))]))
		
	print 'client_npcshop', hex(objid), action, items
	
	data = struct.pack('=IHH', objid, action, len(items))
	
	for item in items:
		data += struct.pack('=III', item[0], item[1], item[2])
	
	return (opcode, data)
	
def preprocess_server_itemupdate(client, opcode, data):
	
	return (opcode, data)
	
def preprocess_server_newitem(client, opcode, data):
	
	return (opcode, data)
	
def preprocess_server_questlist(server, opcode, data):
	(quests_length,) = struct.unpack('I', data[:4])
	
	quests = []
	
	for i in range(0, quests_length):
		quests.append(struct.unpack('I', data[4+(4*i):8+(4*i)])[0])
		
	print 'server_questlist', quests
	
	return (opcode, data)
	
def preprocess_client_pollmap(client, opcode, data):
	print 'client_pollmap'
	
	if len(data) > 0:
		print dump(data)
	
	return (opcode, data)
	
def preprocess_server_inventorystatus(server, opcode, data):
	unknown1, item_count, unknown2, unknown3, unknown4 = struct.unpack('=HIBBB', data)
	
	print 'server_inventorystatus', unknown1, item_count, unknown2, unknown3, unknown4
	
	#unknown3 = 0
	#unknown4 = 0
	
	print 'server_inventorystatus', unknown1, item_count, unknown2, unknown3, unknown4
	
	data = struct.pack('=HIBBB', unknown1, item_count, unknown2, unknown3, unknown4)
	
	return (opcode, data)
	
def preprocess_client_askreply(client, opcode, data):
	question_id, response, unknown1, objid, unknown2 = struct.unpack('=IIHII', data)
	
	print 'client_askreply', question_id, response, unknown1, hex(objid), unknown2
	
	return (opcode, data)
	
def preprocess_server_npcreply(server, opcode, data):
	objid, unknown1, unknown2 = struct.unpack('=3I', data)
	
	print 'server_npcreply', hex(objid), unknown1, unknown2
	
	data = struct.pack('=3I', objid, unknown1, unknown2)
	
	return (opcode, data)
	
def preprocess_server_shopsell(server, opcode, data):
	objid, unknown = struct.unpack('=2I', data)
	
	print 'server_shopsell', hex(objid), unknown
	
	data = struct.pack('=2I', objid, unknown)
	
	return (opcode, data)
	
def preprocess_server_friend_login(server, opcode, data):
	name = data.decode('utf-16-le').strip('\00')
	
	print 'server_friend_login', name
	
	return (opcode, data)
	
def preprocess_server_despawn(server, opcode, data):
	(objid, unknown) = struct.unpack('=IB', data)
	
	if unknown != 0:
		print 'server_despawn', hex(objid), unknown
	
	return (opcode, data)
	
def preprocess_server_target_info(server, opcode, data):
	(objid, level, hp, max_hp) = struct.unpack('=IH2I', data)
	
	print 'server_target_info', hex(objid), level, hp, max_hp
	
	data = struct.pack('=IH2I', objid, level, hp, max_hp)
	
	return (opcode, data)
	
def preprocess_server_spawn_object(server, opcode, data):
	(x, y, z, objid, unknown1, type_id, unknown2, unknown3, name_id, unknown4, unknown5, unknown6) = struct.unpack('=3f3IBH2IHB', data)
	
	print 'server_spawn_object', x, y, z, hex(objid), unknown1, type_id, unknown2, unknown3, name_id, unknown4, unknown5, unknown6
	
	data = struct.pack('=3f3IBH2IHB', x, y, z, objid, unknown1, type_id, unknown2, unknown3, name_id, unknown4, unknown5, unknown6)
	
	return (opcode, data)
	
def preprocess_server_spawn_npc(server, opcode, data):
	(x, y, z, objid, type_id1, type_id2, animation, flags, unknown1, heading, name_id, title_id) = struct.unpack('=3f3I4B2I', data[:36])
	
	#print 'server_spawn_npc', x, y, z, hex(objid), type_id1, type_id2, animation, flags, unknown1, heading, name_id, title_id
	
	"""
	if objid == 0x4007BE80:
		print 'server_spawn_npc', x, y, z, hex(objid), type_id1, type_id2, animation, flags, unknown2, name_id
		print dump(data[32:])
		
		type_id1 = 212283
		type_id2 = 212283
		name_id = 305095
	"""
		
	data = struct.pack('=3f3I4B2I', x, y, z, objid, type_id1, type_id2, animation, flags, unknown1, heading, name_id, title_id)+data[36:]
		
	return (opcode, data)
	
def preprocess_server_npc_move(server, opcode, data):
	return (opcode, data)

def preprocess_server_harvest_window(server, opcode, data):
	(item_id, objid, unknown, mode) = struct.unpack('=2IHB', data)
	
	print 'server_harvest_window', item_id, hex(objid), unknown, mode
	
	data = struct.pack('=2IHB', item_id, objid, unknown, mode)
	
	return (opcode, data)
	
def preprocess_server_quest_progress(server, opcode, data):
	(quest_id, step, unk1, unk2) = struct.unpack('=H2BI', data)
	
	print 'server_quest_progress', quest_id, step, unk1, unk2
	
	return (opcode, data)
	
def preprocess_server_quest_accepted(server, opcode, data):
	(quest_id, step, unk1, unk2) = struct.unpack('=H2BI', data)

	print 'server_quest_accepted', quest_id, step, unk1, unk2

	return (opcode, data)
	
def preprocess_server_quest_failed(server, opcode, data):
	(quest_id, unknown) = struct.unpack('=HB', data)
	
	print 'server_quest_failed', quest_id, unknown
	
	return (opcode, data)

def preprocess_client_ping(client, opcode, data):
	(unknown,) = struct.unpack('=H', data)
	
	if unknown != 7:
		print 'client_ping', unknown
	
	return (opcode, data)

def preprocess_server_teleport(server, opcode, data):
	unknown1, unknown2, unknown3, x, y, z, heading = struct.unpack('=BIH3fB', data)
	
	print 'server_teleport', unknown1, unknown2, unknown3, x, y, z, heading
	#print dump(data)
	
	
	
	data = struct.pack('=BIH3fB', unknown1, unknown2, unknown3, x, y, z, heading)
	
	return (opcode, data)

def preprocess_server_location(server, opcode, data):
	x, y, z, heading = struct.unpack('=3fB', data)
	
	print 'server_location', x, y, z, heading
	
	return (opcode, data)

def preprocess_client_share_quest(client, opcode, data):
	(quest_id,) = struct.unpack('=H', data)
	
	print 'client_share_quest', quest_id
	
	return (opcode, data)

def preprocess_client_open_mail(client, opcode, data):
	(mode,) = struct.unpack('=B', data)
	
	print 'client_open_mail', mode

	return (opcode, data)

def preprocess_client_read_mail(client, opcode, data):
	(mail_id,) = struct.unpack('=I', data)

	print 'client_read_mail', mail_id

	return (opcode, data)
	
def preprocess_client_take_mail_item(client, opcode, data):
	(mail_id, index) = struct.unpack('=IB', data)

	print 'client_take_mail_item', mail_id, index

	return (opcode, data)

def preprocess_client_express_mail(client, opcode, data):
	print 'client_express_mail'
	print dump(data)
	
	(mode,) = struct.unpack('=B', data)
	
	if mode == 0:
		return None
	
	return (opcode, data)
	
def preprocess_client_remove_effect(client, opcode, data):
	(effect_id, unknown) = struct.unpack('=HB', data)

	print 'client_remove_effect', effect_id, unknown
	
	#unknown = 1
	
	data = struct.pack('=HB', effect_id, unknown)

	return (opcode, data)
	
def preprocess_server_system_message(server, opcode, data):
	unknown1, objid, string_id, argument_count = struct.unpack('=H2IB', data[:11])
	
	i = 11
	arguments = []
	
	while i < len(data)-1:
		
		if data[i:i+2].decode('utf-16-le') == '$':
			arguments.append(struct.unpack('=I', data[i+2:i+6])[0])
			i += 8
			continue
		
		j = i
		
		while data[j:j+2] != '\x00\x00':
			j += 2
		
		arguments.append(data[i:j].decode('utf-16-le'))
		
		i = j+2
	
	unknown2 = ord(data[-1])
	
	print 'server_system_message', unknown1, hex(objid), strings.get_string_by_id(string_id).body, arguments, unknown2
	
	data = struct.pack('=H2IB', unknown1, objid, string_id, argument_count)+data[11:]
	
	return (opcode, data)
	
client_preprocessors = {
	opcodes.CLIENT_WHISPER: preprocess_client_whisper,
	opcodes.CLIENT_OPEN_MAIL: preprocess_client_open_mail,
	opcodes.CLIENT_READ_MAIL: preprocess_client_read_mail,
	opcodes.CLIENT_TAKE_MAIL_ITEM: preprocess_client_take_mail_item,
	opcodes.CLIENT_EXPRESS_MAIL: preprocess_client_express_mail,
	#1: preprocess_client_create_character,
	#2: preprocess_client_delete_character,
	#3: preprocess_client_restore_character,
	opcodes.CLIENT_LOOT: preprocess_client_loot,
	opcodes.CLIENT_TAKE_LOOT: preprocess_client_takeloot,
	opcodes.CLIENT_MOVE_ITEM: preprocess_client_moveitem,
	opcodes.CLIENT_MOVE_ITEM_QTY: preprocess_client_moveitemqty,
	opcodes.CLIENT_CHANNEL: preprocess_client_channel,
	#123: preprocess_client_survey_response,
	opcodes.CLIENT_TELEPORT: preprocess_client_teleport,
	opcodes.CLIENT_CHAT: preprocess_client_chat,
	opcodes.CLIENT_POLL_MAP: preprocess_client_pollmap,
	opcodes.CLIENT_DESTROY_ITEM: preprocess_client_destroyitem,
	#115: preprocess_client_craft,
	opcodes.CLIENT_PING: preprocess_client_ping,
	opcodes.CLIENT_TARGET: preprocess_client_target,
	opcodes.CLIENT_ATTACK: preprocess_client_attack,
	opcodes.CLIENT_SKILL: preprocess_client_skill,
	opcodes.CLIENT_USE_ITEM: preprocess_client_useitem,
	opcodes.CLIENT_ACTION: preprocess_client_action,
	opcodes.CLIENT_NPC_SHOP: preprocess_client_npcshop,
	opcodes.CLIENT_LOCATION: preprocess_client_location,
	#152: preprocess_client_askreply,
	opcodes.CLIENT_TALK_NPC: preprocess_client_talknpc,
	opcodes.CLIENT_CLOSE_NPC: preprocess_client_closenpc,
	opcodes.CLIENT_NPC_OPTION: preprocess_client_npcoption,
	opcodes.CLIENT_ABANDON_QUEST: preprocess_client_abandon_quest,
	#243: preprocess_client_loadend,
	#244: preprocess_client_wtf,
	#249: preprocess_client_mapchange,
	#252: preprocess_client_tick,
	opcodes.CLIENT_HARVEST: preprocess_client_harvest,
	opcodes.CLIENT_SHARE_QUEST: preprocess_client_share_quest,
	opcodes.CLIENT_REMOVE_EFFECT: preprocess_client_remove_effect
}

client_postprocessors = {
}

server_preprocessors = {
	opcodes.SERVER_NPC_SHOP_SELL: preprocess_server_shopsell,
	#11: preprocess_server_npc_move,
	opcodes.SERVER_NPC_REPLY: preprocess_server_npcreply,
	opcodes.SERVER_TARGET_INFO: preprocess_server_target_info,
	opcodes.SERVER_HARVEST_ACTION: preprocess_server_harvest_window,
	opcodes.SERVER_DESPAWN: preprocess_server_despawn,
	opcodes.SERVER_ITEM_DESTROYED: preprocess_server_itemdestroyed,
	#45: preprocess_server_itemupdate,
	#47: preprocess_server_newitem,
	opcodes.SERVER_SPAWN_OBJECT: preprocess_server_spawn_object,
	#52: preprocess_server_teleport,
	opcodes.SERVER_LOCATION: preprocess_server_location,
	opcodes.SERVER_SPAWN_NPC: preprocess_server_spawn_npc,
	#84: preprocess_server_flight_time,
	#97: preprocess_server_friend_login,
	opcodes.SERVER_QUEST_FAILED: preprocess_server_quest_failed,
	opcodes.SERVER_QUESTS_AVAILABLE: preprocess_server_questlist,
	opcodes.SERVER_INVENTORY_STATUS: preprocess_server_inventorystatus,
	opcodes.SERVER_QUEST_ACCEPTED: preprocess_server_quest_accepted,
	#205: preprocess_server_quest_progress,
	opcodes.SERVER_SYSTEM_MESSAGE: preprocess_server_system_message
}

server_postprocessors = {
	#4: postprocess_ignore,
	#9: postprocess_ignore,
	#11: postprocess_ignore,
	#22: postprocess_ignore,
	#24: postprocess_ignore,
	#25: postprocess_ignore,
	#26: postprocess_ignore,
	#31: postprocess_ignore,
	#32: postprocess_ignore,
	#37: postprocess_ignore,
	#42: postprocess_ignore,
	#44: postprocess_ignore,
	#45: postprocess_ignore,
	#47: postprocess_ignore,
	#49: postprocess_ignore,
	#50: postprocess_ignore,
	#69: postprocess_ignore,
	#105: postprocess_ignore,
	#112: postprocess_ignore,
	#148: postprocess_ignore,
	#206: postprocess_ignore,
	#241: postprocess_ignore,
	#0x12: postprocess_ignore,
	#0x24: postprocess_ignore,
	#0x31: postprocess_server_chat,
}

def preprocess_client(client, opcode, data):
	if opcode in client_preprocessors:
		return client_preprocessors[opcode](client, opcode, data)
	else:
		return preprocess_client_unknown(client, opcode, data)
	
def postprocess_client(client, opcode, data):
	if opcode in client_postprocessors:
		client_postprocessors[opcode](client, opcode, data)
	else:
		postprocess_client_unknown(client, opcode, data)
	
def preprocess_server(server, opcode, data):
	if opcode in server_preprocessors:
		return server_preprocessors[opcode](server, opcode, data)
	else:
		return preprocess_server_unknown(server, opcode, data)
	
def postprocess_server(server, opcode, data):
	if opcode in server_postprocessors:
		server_postprocessors[opcode](server, opcode, data)
	else:
		postprocess_server_unknown(server, opcode, data)

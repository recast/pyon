from modules import constructors, opcodes
import struct
import threading

COOKING_CRAFT_ID = 150000009
ARMORSMITHING_CRAFT_ID = 150000010
WEAPONSMITHING_CRAFT_ID = 150000011
HANDICRAFTING_CRAFT_ID = 150000012
ALCHEMY_CRAFT_ID = 150000013
TAILORING_CRAFT_ID = 150000015

success = 0
failure = 0

craft_id = WEAPONSMITHING_CRAFT_ID
expert_id = 0x4000c224
table_id = 0x800092f4
work_order_id = 5000
recipe_id = 155004001
ingredients = [(182290000, 4, 0)]

def postprocess_server(server, opcode, data):
	
	if opcode == 148:
		postprocess_server_craft_status(server, opcode, data)
	elif opcode == opcodes.SERVER_QUEST_FAILED:
		postprocess_server_quest_failed(server, opcode, data)
	elif opcode == opcodes.SERVER_QUESTS_AVAILABLE:
		postprocess_server_available_quest_list(server, opcode, data)
	elif opcode == opcodes.SERVER_QUEST_ACCEPTED:
		postprocess_server_quest_accepted(server, opcode, data)
	elif opcode == 205: 
		postprocess_server_quest_progress(server, opcode, data)

def postprocess_server_craft_status(server, opcode, data):
	global success, failure, expert_id, work_order_id, table_id, craft_id, recipe_id, ingredients
	
	(player_id, objid, unknown, status) = struct.unpack('=2IHB', data)
	
	if player_id != 0x30562:
		return
	
	if status == 0 or status == 1:
		return
	
	if status == 2:
		success += 1
	
	if status == 4:
		failure += 1
	
	if success+failure >= 4:
		
		if success < 3:
			constructors.client_abandon_quest(server.client, work_order_id)
		else:
			constructors.client_npcoption(server.client, expert_id, 17, 1, 5, work_order_id, 0)
		
		return
		
	constructors.client_craft(server.client, 128, craft_id, recipe_id, table_id, ingredients)

def postprocess_server_quest_failed(server, opcode, data):
	global expert_id, work_order_id
	
	(quest_id, unknown) = struct.unpack('=HB', data)
	
	if quest_id == 5400:
		constructors.client_npcoption(server.client, expert_id, 1002, 1, 4, work_order_id, 0)

def postprocess_server_available_quest_list(server, opcode, data):
	global expert_id, work_order_id
	
	(quests_length,) = struct.unpack('I', data[:4])
	
	quests = []
	
	for i in range(0, quests_length):
		quests.append(struct.unpack('I', data[4+(4*i):8+(4*i)])[0])
		
	if work_order_id in quests:
		#constructors.client_npcoption(server.client, expert_id, 1002, 1, 4, work_order_id, 0)
		pass

def postprocess_server_quest_accepted(server, opcode, data):
	global success, failure, table_id, work_order_id, craft_id, recipe_id, ingredients
	
	(quest_id, step, unk1, unk2) = struct.unpack('=H2BI', data)

	if quest_id == work_order_id:
		success = 0
		failure = 0
		threading.Timer(1.0, constructors.client_craft, [server.client, 128, craft_id, recipe_id, table_id, ingredients]).start()
		#constructors.client_craft(server.client, 128, 150000013, 155004165, table_id, [(182290164, 4, 0)])
		
def postprocess_server_quest_progress(server, opcode, data):
	global success, failure, expert_id, work_order_id
	
	(quest_id, step, unk1, unk2) = struct.unpack('=H2BI', data)
	
	if quest_id == work_order_id and step == 5:
		threading.Timer(1.0, constructors.client_npcoption, [server.client, expert_id, 1002, 1, 4, work_order_id, 0]).start()

#constructors.client_npcoption(client, 0x40010934, 1002, 1, 4, 5300, 0)
#constructors.client_craft(client, 128, 150000013, 155004165, 0x80009301, [(182290164, 4, 0)])
#constructors.client_npcoption(client, 0x4000ff8c, 17, 1, 5, 5400, 0)
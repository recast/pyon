from modules import quests, strings, constructors, opcodes
import struct


def postprocess_server(server, opcode, data):
	
	if opcode == opcodes.SERVER_QUESTS_AVAILABLE:
		postprocess_server_available_quest_list(server, opcode, data)

def postprocess_server_available_quest_list(server, opcode, data):
	(quests_length,) = struct.unpack('I', data[:4])

	quest_ids = []

	for i in range(0, quests_length):
		quest_ids.append(struct.unpack('I', data[4+(4*i):8+(4*i)])[0])

	print '-'*80
	print 'CURRENTLY AVAILABLE'.center(80)
	print '-'*80
	
	for quest_id in quest_ids:
		
		if quest_id&0x8000:
			continue
		
		quest = quests.get_quest_by_id(quest_id)
		
		print 'Level %2d %s' % (quest.client_level, strings.get_string_by_name(quest.desc.text).body)
		
	print '-'*80
	print 'AVAILABLE NEXT LEVEL'.center(80)
	print '-'*80
	
	for quest_id in quest_ids:
		
		if not quest_id&0x8000:
			continue
		
		quest_id -= 0x8000
		
		quest = quests.get_quest_by_id(quest_id)
		
		print 'Level %2d %s' % (quest.client_level, strings.get_string_by_name(quest.desc.text).body)
	
	print '-'*80
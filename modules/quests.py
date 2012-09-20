import lxml.etree
import lxml.objectify

quests = {}
tree = lxml.objectify.parse(open('quest.xml'))

for quest in tree.getroot().quest:
	quests[quest.id.pyval] = quest

def get_quest_by_id(id):
	global quests
	
	return quests[id]


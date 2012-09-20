import lxml.etree
import lxml.objectify

string_id_map = {}
string_name_map = {}

tree = lxml.objectify.parse(open('client_strings.xml'))

for string in tree.getroot().string:
	string_id_map[string.id.pyval] = string
	string_name_map[string.name.pyval] = string

def get_string_by_id(id):
	global string_id_map
	
	return string_id_map[id]

def get_string_by_name(name):
	global string_name_map
	
	return string_name_map[name]


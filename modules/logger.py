import sqlite3

db = sqlite3.connect('packets.db')
cursor = db.cursor()

def postprocess_client(client, opcode, data):
	cursor.execute("""INSERT INTO client_packets (opcode, data, time) VALUES (?, ?, DATETIME('NOW'))""", (opcode, sqlite3.Binary(data)))
	db.commit()

def postprocess_server(server, opcode, data):
	cursor.execute("""INSERT INTO server_packets (opcode, data, time) VALUES (?, ?, DATETIME('NOW'))""", (opcode, sqlite3.Binary(data)))
	db.commit()
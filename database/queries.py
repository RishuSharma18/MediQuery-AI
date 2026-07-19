import sqlite3

connection = sqlite3.connect("data/hospital.db")

cursor = connection.cursor()

cursor.execute("SELECT COUNT(*) FROM patients")

print(cursor.fetchone())
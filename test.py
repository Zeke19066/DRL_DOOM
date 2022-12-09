import sqlite3

#Open/Create SQLite DB
conn = sqlite3.connect('test.db')
print("Opened database successfully")
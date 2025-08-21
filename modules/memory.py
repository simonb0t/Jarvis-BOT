import sqlite3

conn = sqlite3.connect('jarvis.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS ideas(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    texto TEXT,
    categoria TEXT,
    prioridad INTEGER,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

def guardar_idea(texto, categoria="general", prioridad=1):
    cursor.execute("INSERT INTO ideas(texto, categoria, prioridad) VALUES (?, ?, ?)",
                   (texto, categoria, prioridad))
    conn.commit()

def consultar_ideas(limit=5):
    cursor.execute("SELECT id, texto, fecha FROM ideas ORDER BY fecha DESC LIMIT ?", (limit,))
    return cursor.fetchall()

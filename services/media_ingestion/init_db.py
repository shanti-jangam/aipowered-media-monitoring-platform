import psycopg2
import time

# Wait for the DB to be ready
for _ in range(10):
    try:
        conn = psycopg2.connect(
            dbname="smartmedia",
            user="postgres",
            password="postgres",
            host="db",
            port=5432
        )
        break
    except Exception as e:
        print("Waiting for database to be ready...", e)
        time.sleep(2)
else:
    raise Exception("Could not connect to the database after several attempts.")

cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS transcripts (
    id SERIAL PRIMARY KEY,
    stream_id VARCHAR(128),
    chunk_filename VARCHAR(256),
    transcript TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
''')
conn.commit()
cur.close()
conn.close()
print("Transcripts table created or already exists.") 
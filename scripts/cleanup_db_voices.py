import sqlite3
from pathlib import Path

db_path = Path("backend/storage/tastp.db")
if not db_path.exists():
    db_path = Path("storage/tastp.db")

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Hapus semua preset voices bawaan dan data uji coba unit test
stock_ids = [
    'id_ID-news_tts-medium',
    'piper_id_gadis_fast',
    'piper_id_bima_narrator',
    'piper_id_siti_podcast',
    'piper_id_dimas_news',
    'edge_ardi',
    'edge_gadis',
    'edge_dimas',
    'edge_siti',
    'gemini_kore',
    'gemini_puck',
    'gemini_fenrir',
    'gemini_aoede',
]

for vid in stock_ids:
    cur.execute("DELETE FROM voice_records WHERE id = ?", (vid,))

cur.execute("DELETE FROM voice_records WHERE id LIKE 'custom_suara_%'")
cur.execute("DELETE FROM voice_records WHERE name LIKE 'Suara Podcaster%'")
cur.execute("DELETE FROM voice_records WHERE name LIKE 'Suara Klon Uji%'")
cur.execute("DELETE FROM voice_records WHERE is_cloned = 0")

conn.commit()

cur.execute("SELECT id, name, engine, is_cloned FROM voice_records")
remaining = cur.fetchall()
print(f"Total suara tersisa di database: {len(remaining)}")
for r in remaining:
    print(" -", r)

conn.close()

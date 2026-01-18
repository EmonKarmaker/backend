import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM surahs")
    print(f"✅ Connected! Surahs: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT word_arabic FROM words WHERE ayah_id=1 ORDER BY word_position")
    words = [r[0] for r in cursor.fetchall()]
    print(f"✅ Sample: {' '.join(words)}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
import psycopg2
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def remove_harakat(text):
    """Remove all harakat/diacritics from Arabic text"""
    harakat = [
        '\u064B', '\u064C', '\u064D', '\u064E', '\u064F',
        '\u0650', '\u0651', '\u0652', '\u0653', '\u0654',
        '\u0655', '\u0656', '\u0657', '\u0658', '\u0670',
    ]
    for mark in harakat:
        text = text.replace(mark, '')
    return text.strip()

def populate_database():
    """Download and populate Quran with harakat"""
    print("="*60)
    print("📥 Downloading Quran with Harakat")
    print("="*60)
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    for surah_num in range(1, 115):
        print(f"\n📖 Surah {surah_num}/114...")
        
        # Get Surah info
        info_url = f"https://api.quran.com/api/v4/chapters/{surah_num}"
        info_resp = requests.get(info_url)
        surah = info_resp.json()['chapter']
        
        # Insert Surah
        cursor.execute("""
            INSERT INTO surahs (surah_number, name_arabic, name_english, name_transliteration, revelation_place, total_ayahs)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (surah_number) DO UPDATE
            SET name_arabic = EXCLUDED.name_arabic
            RETURNING id
        """, (
            surah_num,
            surah['name_arabic'],
            surah['name_simple'],
            surah.get('translated_name', {}).get('name', surah['name_simple']),
            surah.get('revelation_place', 'Makkah'),
            surah['verses_count']
        ))
        
        surah_id = cursor.fetchone()[0]
        
        # Get Verses with Harakat
        verses_url = f"https://api.quran.com/api/v4/quran/verses/uthmani?chapter_number={surah_num}"
        verses_resp = requests.get(verses_url)
        verses = verses_resp.json()['verses']
        
        # Get English translation
        trans_url = f"https://api.quran.com/api/v4/quran/translations/131?chapter_number={surah_num}"
        trans_resp = requests.get(trans_url)
        translations = trans_resp.json().get('translations', [])
        
        for idx, verse in enumerate(verses):
            _, ayah_num = verse['verse_key'].split(':')
            ayah_num = int(ayah_num)
            
            text_harakat = verse['text_uthmani']
            text_simple = remove_harakat(text_harakat)
            translation = translations[idx]['text'] if idx < len(translations) else ''
            
            # Insert Ayah
            cursor.execute("""
                INSERT INTO ayahs (surah_id, ayah_number, text_uthmani, text_simple, translation_en)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (surah_id, ayah_number) DO UPDATE
                SET text_uthmani = EXCLUDED.text_uthmani
                RETURNING id
            """, (surah_id, ayah_num, text_harakat, text_simple, translation))
            
            ayah_id = cursor.fetchone()[0]
            
            # Insert Words
            words = text_harakat.split()
            for pos, word_harakat in enumerate(words, 1):
                word_simple = remove_harakat(word_harakat)
                
                cursor.execute("""
                    INSERT INTO words (ayah_id, word_position, word_arabic_with_harakat, word_arabic_simple)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (ayah_id, word_position) DO NOTHING
                """, (ayah_id, pos, word_harakat, word_simple))
        
        conn.commit()
        print(f"  ✓ {len(verses)} ayahs")
        time.sleep(0.1)
    
    # Stats
    cursor.execute("SELECT COUNT(*) FROM surahs")
    print(f"\n✅ Surahs: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM ayahs")
    print(f"✅ Ayahs: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM words")
    print(f"✅ Words: {cursor.fetchone()[0]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("🎉 DATABASE POPULATED WITH HARAKAT!")
    print("="*60)

if __name__ == "__main__":
    try:
        populate_database()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
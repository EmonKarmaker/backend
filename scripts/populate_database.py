import psycopg2
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/quran_db")

def download_quran_data():
    """
    Download Quran data from Quran.com API
    """
    print("📥 Downloading Quran data from API...")
    
    all_verses = []
    
    # Get all 114 Surahs
    for surah_num in range(1, 115):  # 1 to 114
        print(f"  Downloading Surah {surah_num}...")
        
        url = f"https://api.quran.com/api/v4/quran/verses/uthmani?chapter_number={surah_num}"
        
        response = requests.get(url)
        data = response.json()
        
        verses = data.get('verses', [])
        
        for verse in verses:
            verse_key = verse['verse_key']  # e.g., "1:1"
            surah, ayah = verse_key.split(':')
            
            all_verses.append({
                'surah': int(surah),
                'ayah': int(ayah),
                'text_uthmani': verse['text_uthmani'],
                'text_simple': verse.get('text_imlaei', ''),  # Fallback to uthmani if imlaei not available
            })
        
        # Be nice to the API
        import time
        time.sleep(0.1)
    
    print(f"✓ Downloaded {len(all_verses)} verses")
    
    # Save to JSON file for backup
    with open('quran_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_verses, f, ensure_ascii=False, indent=2)
    
    print("✓ Saved to quran_data.json")
    
    return all_verses


def normalize_text(text):
    """Remove diacritics to create simple version"""
    from pyarabic import araby
    return araby.strip_tashkeel(text)


def populate_database(verses_data):
    """
    Populate PostgreSQL database with Quran data
    """
    print("\n📚 Populating database...")
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Step 1: Populate Surahs table
    print("\n1️⃣ Populating Surahs table...")
    
    surah_info = {
        1: ('الفاتحة', 'Al-Fatihah', 7),
        2: ('البقرة', 'Al-Baqarah', 286),
        3: ('آل عمران', 'Ali Imran', 200),
        # Add all 114 surahs or fetch from API
        # For simplicity, we'll auto-detect from verses
    }
    
    # Auto-detect surahs from verses
    surahs = {}
    for verse in verses_data:
        surah_num = verse['surah']
        if surah_num not in surahs:
            surahs[surah_num] = 0
        surahs[surah_num] += 1
    
    for surah_num, total_ayahs in sorted(surahs.items()):
        # Get surah name from API or use default
        if surah_num in surah_info:
            name_arabic, name_english, _ = surah_info[surah_num]
        else:
            name_arabic = f'سورة {surah_num}'
            name_english = f'Surah {surah_num}'
        
        cursor.execute("""
            INSERT INTO surahs (surah_number, name_arabic, name_english, total_ayahs)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (surah_number) DO NOTHING
        """, (surah_num, name_arabic, name_english, total_ayahs))
        
        print(f"  ✓ Surah {surah_num}: {name_arabic} ({total_ayahs} ayahs)")
    
    conn.commit()
    
    # Step 2: Populate Ayahs table
    print("\n2️⃣ Populating Ayahs table...")
    
    for verse in verses_data:
        surah_num = verse['surah']
        ayah_num = verse['ayah']
        text_uthmani = verse['text_uthmani']
        text_simple = normalize_text(text_uthmani)
        
        # Get surah_id
        cursor.execute("SELECT id FROM surahs WHERE surah_number = %s", (surah_num,))
        surah_id = cursor.fetchone()[0]
        
        # Insert ayah
        cursor.execute("""
            INSERT INTO ayahs (surah_id, ayah_number, text_uthmani, text_simple)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (surah_id, ayah_number) DO NOTHING
            RETURNING id
        """, (surah_id, ayah_num, text_uthmani, text_simple))
        
        result = cursor.fetchone()
        if result:
            ayah_id = result[0]
            
            # Step 3: Populate Words table
            words = text_simple.split()
            
            for word_pos, word in enumerate(words, start=1):
                cursor.execute("""
                    INSERT INTO words (ayah_id, word_position, word_arabic)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (ayah_id, word_position) DO NOTHING
                """, (ayah_id, word_pos, word))
        
        if ayah_num % 10 == 0:
            print(f"  ✓ Surah {surah_num}, Ayah {ayah_num}")
    
    conn.commit()
    
    # Verify data
    cursor.execute("SELECT COUNT(*) FROM surahs")
    total_surahs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM ayahs")
    total_ayahs = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM words")
    total_words = cursor.fetchone()[0]
    
    print(f"\n✅ Database populated successfully!")
    print(f"   Total Surahs: {total_surahs}")
    print(f"   Total Ayahs: {total_ayahs}")
    print(f"   Total Words: {total_words}")
    
    cursor.close()
    conn.close()


def main():
    print("=" * 60)
    print("🕌 Quran Database Population Script")
    print("=" * 60)
    
    # Step 1: Download data
    verses = download_quran_data()
    
    # Step 2: Populate database
    populate_database(verses)
    
    print("\n" + "=" * 60)
    print("✅ COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
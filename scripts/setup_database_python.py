import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:123456@localhost:5432/quran_db")

def setup_database():
    """Create tables with proper UTF-8 encoding"""
    
    print("="*60)
    print("🗄️ Setting up database with harakat support")
    print("="*60)
    
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Step 1: Drop existing tables
    print("\n1️⃣ Dropping existing tables...")
    cursor.execute("DROP TABLE IF EXISTS word_harakat_details CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS words CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS ayahs CASCADE;")
    cursor.execute("DROP TABLE IF EXISTS surahs CASCADE;")
    conn.commit()
    print("✓ Old tables dropped")
    
    # Step 2: Create surahs table
    print("\n2️⃣ Creating surahs table...")
    cursor.execute("""
        CREATE TABLE surahs (
            id SERIAL PRIMARY KEY,
            surah_number INTEGER UNIQUE NOT NULL,
            name_arabic VARCHAR(100) NOT NULL,
            name_english VARCHAR(100),
            name_transliteration VARCHAR(100),
            revelation_place VARCHAR(20),
            total_ayahs INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    print("✓ Surahs table created")
    
    # Step 3: Create ayahs table
    print("\n3️⃣ Creating ayahs table...")
    cursor.execute("""
        CREATE TABLE ayahs (
            id SERIAL PRIMARY KEY,
            surah_id INTEGER REFERENCES surahs(id) ON DELETE CASCADE,
            ayah_number INTEGER NOT NULL,
            text_uthmani TEXT NOT NULL,
            text_simple TEXT NOT NULL,
            text_imlaei TEXT,
            translation_en TEXT,
            translation_bn TEXT,
            juz_number INTEGER,
            page_number INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(surah_id, ayah_number)
        );
    """)
    conn.commit()
    print("✓ Ayahs table created")
    
    # Step 4: Create words table
    print("\n4️⃣ Creating words table...")
    cursor.execute("""
        CREATE TABLE words (
            id SERIAL PRIMARY KEY,
            ayah_id INTEGER REFERENCES ayahs(id) ON DELETE CASCADE,
            word_position INTEGER NOT NULL,
            word_arabic_with_harakat TEXT NOT NULL,
            word_arabic_simple TEXT NOT NULL,
            word_transliteration VARCHAR(100),
            word_translation_en TEXT,
            root_letters VARCHAR(10),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ayah_id, word_position)
        );
    """)
    conn.commit()
    print("✓ Words table created")
    
    # Step 5: Create word_harakat_details table
    print("\n5️⃣ Creating word_harakat_details table...")
    cursor.execute("""
        CREATE TABLE word_harakat_details (
            id SERIAL PRIMARY KEY,
            word_id INTEGER REFERENCES words(id) ON DELETE CASCADE,
            letter_position INTEGER NOT NULL,
            letter_arabic CHAR(1) NOT NULL,
            harakat_type VARCHAR(20),
            harakat_symbol CHAR(2),
            has_madd BOOLEAN DEFAULT FALSE,
            has_ghunnah BOOLEAN DEFAULT FALSE,
            has_qalqalah BOOLEAN DEFAULT FALSE,
            has_idgham BOOLEAN DEFAULT FALSE,
            pronunciation_note TEXT,
            UNIQUE(word_id, letter_position)
        );
    """)
    conn.commit()
    print("✓ Word harakat details table created")
    
    # Step 6: Create indexes
    print("\n6️⃣ Creating indexes...")
    cursor.execute("CREATE INDEX idx_ayahs_surah_ayah ON ayahs(surah_id, ayah_number);")
    cursor.execute("CREATE INDEX idx_ayahs_juz ON ayahs(juz_number);")
    cursor.execute("CREATE INDEX idx_words_ayah ON words(ayah_id);")
    cursor.execute("CREATE INDEX idx_harakat_word ON word_harakat_details(word_id);")
    conn.commit()
    print("✓ Indexes created")
    
    # Step 7: Insert sample data
    print("\n7️⃣ Inserting sample data...")
    
    # Insert Surah Al-Fatihah
    cursor.execute("""
        INSERT INTO surahs (surah_number, name_arabic, name_english, name_transliteration, revelation_place, total_ayahs)
        VALUES (1, 'الفاتحة', 'Al-Fatihah', 'Al-Faatiha', 'Makkah', 7);
    """)
    
    # Insert Ayah 1:1
    cursor.execute("""
        INSERT INTO ayahs (surah_id, ayah_number, text_uthmani, text_simple, translation_en, juz_number, page_number)
        VALUES (
            1, 1,
            'بِسۡمِ ٱللَّهِ ٱلرَّحۡمَـٰنِ ٱلرَّحِيمِ',
            'بسم الله الرحمن الرحيم',
            'In the name of Allah, the Entirely Merciful, the Especially Merciful',
            1, 1
        );
    """)
    
    # Insert words
    cursor.execute("""
        INSERT INTO words (ayah_id, word_position, word_arabic_with_harakat, word_arabic_simple, word_transliteration, word_translation_en, root_letters)
        VALUES
            (1, 1, 'بِسۡمِ', 'بسم', 'bismi', 'In the name', 'سمو'),
            (1, 2, 'ٱللَّهِ', 'الله', 'Allāhi', 'Allah', 'اله'),
            (1, 3, 'ٱلرَّحۡمَـٰنِ', 'الرحمن', 'ar-Raḥmāni', 'The Most Gracious', 'رحم'),
            (1, 4, 'ٱلرَّحِيمِ', 'الرحيم', 'ar-Raḥīmi', 'The Most Merciful', 'رحم');
    """)
    
    conn.commit()
    print("✓ Sample data inserted")
    
    # Step 8: Verify
    print("\n8️⃣ Verifying database...")
    cursor.execute("SELECT COUNT(*) FROM surahs;")
    print(f"✓ Surahs: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM ayahs;")
    print(f"✓ Ayahs: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM words;")
    print(f"✓ Words: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT word_arabic_with_harakat FROM words ORDER BY word_position;")
    words = [row[0] for row in cursor.fetchall()]
    print(f"✓ Sample words: {' '.join(words)}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ DATABASE SETUP COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    try:
        setup_database()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
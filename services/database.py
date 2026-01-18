import psycopg2
from typing import List, Dict

class QuranDatabase:
    """PostgreSQL database connection for Quran text with harakat"""
    
    def __init__(self, connection_string: str):
        print(f"📚 Connecting to database...")
        self.conn = psycopg2.connect(connection_string)
        print(f"✓ Database connected")
    
    def get_ayah_words(self, surah: int, ayah: int) -> List[Dict[str, str]]:
        """
        Get words with harakat for specific ayah
        
        Returns:
            [
                {'with_harakat': 'بِسۡمِ', 'simple': 'بسم'},
                {'with_harakat': 'ٱللَّهِ', 'simple': 'الله'},
                ...
            ]
        """
        print(f"\n📖 Fetching words for Surah {surah}, Ayah {ayah}")
        
        cursor = self.conn.cursor()
        
        # Get ayah_id
        cursor.execute("""
            SELECT id FROM ayahs 
            WHERE surah_id = (SELECT id FROM surahs WHERE surah_number = %s)
            AND ayah_number = %s
        """, (surah, ayah))
        
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"Ayah not found: {surah}:{ayah}")
        
        ayah_id = result[0]
        
        # Get words with harakat
        cursor.execute("""
            SELECT word_arabic_with_harakat, word_arabic_simple
            FROM words 
            WHERE ayah_id = %s 
            ORDER BY word_position
        """, (ayah_id,))
        
        words = [
            {
                'with_harakat': row[0],
                'simple': row[1]
            }
            for row in cursor.fetchall()
        ]
        
        print(f"✓ Found {len(words)} words")
        print(f"  With harakat: {' '.join([w['with_harakat'] for w in words])}")
        print(f"  Simple: {' '.join([w['simple'] for w in words])}")
        
        cursor.close()
        return words
    
    def close(self):
        """Close database connection"""
        self.conn.close()
        print("✓ Database connection closed")
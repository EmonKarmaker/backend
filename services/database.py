import psycopg2
from typing import List

class QuranDatabase:
    """
    PostgreSQL database connection for Quran text
    """
    
    def __init__(self, connection_string: str):
        """
        Initialize database connection
        
        Args:
            connection_string: postgresql://user:pass@host:port/dbname
        """
        print(f"📚 Connecting to database...")
        self.conn = psycopg2.connect(connection_string)
        print(f"✓ Database connected")
    
    def get_ayah_words(self, surah: int, ayah: int) -> List[str]:
        """
        Get list of words for specific ayah
        
        Args:
            surah: Surah number (1-114)
            ayah: Ayah number
            
        Returns:
            List of Arabic words
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
        
        # Get individual words
        cursor.execute("""
            SELECT word_arabic 
            FROM words 
            WHERE ayah_id = %s 
            ORDER BY word_position
        """, (ayah_id,))
        
        words = [row[0] for row in cursor.fetchall()]
        
        print(f"✓ Found {len(words)} words: {' '.join(words)}")
        
        cursor.close()
        return words
    
    def get_expected_word(self, surah: int, ayah: int, word_index: int) -> str:
        """
        Get expected word at specific position
        
        Args:
            surah: Surah number
            ayah: Ayah number
            word_index: Word position (0-based)
            
        Returns:
            Arabic word
        """
        words = self.get_ayah_words(surah, ayah)
        
        if word_index >= len(words):
            raise ValueError(f"Word index {word_index} out of range (max {len(words)-1})")
        
        return words[word_index]
    
    def close(self):
        """Close database connection"""
        self.conn.close()
        print("✓ Database connection closed")
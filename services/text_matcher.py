from pyarabic import araby
from difflib import SequenceMatcher

class ArabicTextMatcher:
    """
    Compare Arabic text and calculate similarity
    """
    
    def __init__(self):
        print("🔤 Text Matcher initialized")
    
    def normalize(self, text: str) -> str:
        """
        Normalize Arabic text for comparison
        
        Args:
            text: Arabic text with diacritics
            
        Returns:
            Normalized text without diacritics
        """
        # Remove diacritics (tashkeel)
        text = araby.strip_tashkeel(text)
        
        # Remove tatweel
        text = araby.strip_tatweel(text)
        
        # Normalize hamza variations
        text = text.replace('أ', 'ا')
        text = text.replace('إ', 'ا')
        text = text.replace('آ', 'ا')
        text = text.replace('ٱ', 'ا')
        
        # Normalize alef maksura
        text = text.replace('ى', 'ي')
        
        # Normalize taa marbuta
        text = text.replace('ة', 'ه')
        
        # Clean whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def compare_words(self, expected: str, user_said: str) -> dict:
        """
        Compare expected word with user's spoken word
        
        Args:
            expected: Correct word from Quran
            user_said: What user said (from Whisper)
            
        Returns:
            {
                'expected': 'الرحمن',
                'user_said': 'الرحمان',
                'similarity': 85.7,
                'status': 'similar',
                'color': 'yellow',
                'message': '...'
            }
        """
        print(f"\n🔍 Comparing words:")
        print(f"  Expected: '{expected}'")
        print(f"  User said: '{user_said}'")
        
        # Normalize both
        expected_clean = self.normalize(expected)
        user_clean = self.normalize(user_said)
        
        print(f"  Expected (normalized): '{expected_clean}'")
        print(f"  User (normalized): '{user_clean}'")
        
        # Calculate similarity using SequenceMatcher
        similarity = SequenceMatcher(None, expected_clean, user_clean).ratio() * 100
        
        print(f"  Similarity: {similarity:.2f}%")
        
        # Determine status and color
        if expected_clean == user_clean:
            status = 'correct'
            color = 'green'
            message = 'ممتاز! نطق صحيح'
            print(f"  ✅ CORRECT")
        elif similarity >= 85:
            status = 'similar'
            color = 'yellow'
            message = f'قريب جداً، الصواب: {expected}'
            print(f"  ⚠️ SIMILAR (close)")
        elif similarity >= 70:
            status = 'similar'
            color = 'orange'
            message = f'خطأ بسيط، الصواب: {expected}'
            print(f"  ⚠️ SIMILAR (minor error)")
        else:
            status = 'wrong'
            color = 'red'
            message = f'خطأ، الصواب: {expected}'
            print(f"  ❌ WRONG")
        
        return {
            'expected': expected,
            'user_said': user_said,
            'expected_normalized': expected_clean,
            'user_normalized': user_clean,
            'similarity': round(similarity, 2),
            'status': status,
            'color': color,
            'message': message
        }
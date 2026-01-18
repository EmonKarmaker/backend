-- Drop existing tables
DROP TABLE IF EXISTS word_harakat_details CASCADE;
DROP TABLE IF EXISTS words CASCADE;
DROP TABLE IF EXISTS ayahs CASCADE;
DROP TABLE IF EXISTS surahs CASCADE;

-- Create tables with harakat support
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

-- Create indexes
CREATE INDEX idx_ayahs_surah_ayah ON ayahs(surah_id, ayah_number);
CREATE INDEX idx_ayahs_juz ON ayahs(juz_number);
CREATE INDEX idx_words_ayah ON words(ayah_id);
CREATE INDEX idx_harakat_word ON word_harakat_details(word_id);

-- Insert sample data
INSERT INTO surahs (surah_number, name_arabic, name_english, name_transliteration, revelation_place, total_ayahs)
VALUES (1, 'الفاتحة', 'Al-Fatihah', 'Al-Faatiha', 'Makkah', 7);

INSERT INTO ayahs (surah_id, ayah_number, text_uthmani, text_simple, translation_en, juz_number, page_number)
VALUES (
    1, 1,
    'بِسۡمِ ٱللَّهِ ٱلرَّحۡمَـٰنِ ٱلرَّحِيمِ',
    'بسم الله الرحمن الرحيم',
    'In the name of Allah, the Entirely Merciful, the Especially Merciful',
    1, 1
);

INSERT INTO words (ayah_id, word_position, word_arabic_with_harakat, word_arabic_simple, word_transliteration, word_translation_en, root_letters)
VALUES
    (1, 1, 'بِسۡمِ', 'بسم', 'bismi', 'In the name', 'سمو'),
    (1, 2, 'ٱللَّهِ', 'الله', 'Allāhi', 'Allah', 'اله'),
    (1, 3, 'ٱلرَّحۡمَـٰنِ', 'الرحمن', 'ar-Raḥmāni', 'The Most Gracious', 'رحم'),
    (1, 4, 'ٱلرَّحِيمِ', 'الرحيم', 'ar-Raḥīmi', 'The Most Merciful', 'رحم');

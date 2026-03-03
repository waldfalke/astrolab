# Task Log: ASTRO-025 - Skill: knowledge-ingestion

**Date:** 2026-03-04
**Workspace:** `D:\Dev\CATMEastrolab`
**Status:** TODO
**Priority:** P2
**Cynefin Domain:** Complex

## Objective

Create the `knowledge-ingestion` skill that processes multilingual astrology methodology sources (RU/EN). This skill extracts terms, aligns glossaries, disambiguates concepts, and updates the vector store for context retrieval.

## Skill Location

```
.qwen/skills/knowledge-ingestion/
├── SKILL.md
├── scripts/
│   ├── extract_terms.py
│   ├── align_glossaries.py
│   └── update_vector_store.py
└── references/
    ├── term-categories.md
    └── ru-en-term-mapping.md
```

## SKILL.md Frontmatter

```yaml
---
name: knowledge-ingestion
description: Processes multilingual astrology methodology sources (RU/EN). Extracts terms, aligns glossaries, disambiguates concepts, updates vector store. Use when user provides new methodology documents, wants to add terms to glossary, or needs to process astrology texts for context retrieval.
license: Apache-2.0
metadata:
  author: CATMEastrolab Team
  version: 0.1.0
  glossary: docs/ASTRO_GLOSSARY.md
  vector-store: context_portal/
---
```

## Implementation Steps

### Step 1: Load Source Documents

Accept multiple input formats:

```python
def load_source(file_path):
    """Load methodology source document."""
    
    if file_path.endswith('.md'):
        return load_markdown(file_path)
    elif file_path.endswith('.pdf'):
        return load_pdf(file_path)
    elif file_path.endswith('.docx'):
        return load_docx(file_path)
    elif file_path.endswith('.txt'):
        return load_text(file_path)
```

### Step 2: Extract Terms

Identify astrology terms:

```python
def extract_terms(text, language='auto'):
    """
    Extract astrology terms from text.
    
    Categories:
    - planets (планеты)
    - signs (знаки)
    - houses (дома)
    - aspects (аспекты)
    - techniques (методики)
    - interpretations (трактовки)
    """
    
    # Pattern-based extraction
    patterns = {
        'planet': r'\b(Солнце|Луна|Меркурий|Венера|Марс|Юпитер|Сатурн|Уран|Нептун|Плутон)\b',
        'sign': r'\b(Овен|Телец|Близнецы|Рак|Лев|Дева|Весы|Скорпион|Стрелец|Козерог|Водолей|Рыбы)\b',
        'house': r'\b(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)\s+дом\b',
        'aspect': r'\b(соединение|оппозиция|трин|квадрат|секстиль|квинконс)\b',
        'technique': r'\b(прогрессии|дирекции|соляр|синастрия|транзиты)\b'
    }
    
    terms = []
    for category, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            terms.append({
                'term': match,
                'category': category,
                'language': detect_language(match),
                'context': extract_context(text, match)
            })
    
    return terms
```

### Step 3: Align with Existing Glossary

Map new terms to existing glossary:

```python
def align_with_glossary(new_terms, existing_glossary):
    """
    Match new terms to existing glossary entries.
    
    Returns:
    - matched: terms found in glossary
    - new: terms not in glossary (candidates for addition)
    - ambiguous: terms with multiple possible matches
    """
    
    matched = []
    new = []
    ambiguous = []
    
    for term in new_terms:
        # Find potential matches
        matches = find_glossary_matches(term, existing_glossary)
        
        if len(matches) == 0:
            new.append(term)
        elif len(matches) == 1:
            matched.append({
                'term': term,
                'glossary_entry': matches[0]
            })
        else:
            ambiguous.append({
                'term': term,
                'possible_matches': matches
            })
    
    return {
        'matched': matched,
        'new': new,
        'ambiguous': ambiguous
    }
```

### Step 4: RU-EN Term Mapping

Create bilingual term mappings:

```python
ru_en_mapping = {
    'Солнце': 'Sun',
    'Луна': 'Moon',
    'Меркурий': 'Mercury',
    'Венера': 'Venus',
    'Марс': 'Mars',
    'Юпитер': 'Jupiter',
    'Сатурн': 'Saturn',
    'Уран': 'Uranus',
    'Нептун': 'Neptune',
    'Плутон': 'Pluto',
    
    'Овен': 'Aries',
    'Телец': 'Taurus',
    'Близнецы': 'Gemini',
    'Рак': 'Cancer',
    'Лев': 'Leo',
    'Дева': 'Virgo',
    'Весы': 'Libra',
    'Скорпион': 'Scorpio',
    'Стрелец': 'Sagittarius',
    'Козерог': 'Capricorn',
    'Водолей': 'Aquarius',
    'Рыбы': 'Pisces',
    
    'соединение': 'conjunction',
    'оппозиция': 'opposition',
    'трин': 'trine',
    'квадрат': 'square',
    'секстиль': 'sextile',
    'квинконс': 'quincunx',
    
    'прогрессии': 'progressions',
    'дирекции': 'directions',
    'соляр': 'solar return',
    'синастрия': 'synastry',
    'транзиты': 'transits',
    
    'дома': 'houses',
    'асцендент': 'ascendant',
    'кулмидация': 'culmination',
    'десцендент': 'descendant',
    'имум цели': 'imum coeli',
    
    'экзальтация': 'exaltation',
    'обитель': 'domicile',
    'изгнание': 'detriment',
    'падение': 'fall',
    
    'диспозитор': 'dispositor',
    'ретроградность': 'retrograde',
    'орб': 'orb'
}
```

### Step 5: Update Glossary

Add new terms to ASTRO_GLOSSARY.md:

```markdown
## Term: Фазовый анализ (Phase Analysis)

**Category:** technique

**Language:** RU

**Definition:**
Метод анализа состояния планеты через фазу по знаку (Z.z), фазу по дому (H.h), и фазу диспозитора (D).

**Related Terms:**
- State vector (EN)
- Микрофаза (microphase)
- Диспозитор (dispositor)

**Source:**
Семинар Захарьяна, 2025

**Example:**
P <7.3 : 10.8 : D=5.2>
```

### Step 6: Update Vector Store

Embed documents for semantic search:

```python
def update_vector_store(documents, vector_db_path):
    """
    Add documents to vector store for semantic retrieval.
    
    Steps:
    1. Chunk documents into passages
    2. Generate embeddings
    3. Store with metadata
    """
    
    chunks = chunk_documents(documents, chunk_size=500)
    
    for chunk in chunks:
        embedding = generate_embedding(chunk['text'])
        
        vector_db.insert({
            'id': generate_id(),
            'embedding': embedding,
            'metadata': {
                'source': chunk['source'],
                'category': chunk['category'],
                'language': chunk['language'],
                'terms': chunk['terms']
            }
        })
```

### Step 7: Generate Ingestion Report

```yaml
ingestion_report:
  processed_at: 2026-03-04T16:00:00Z
  source_file: docs/phase_analysis_methodology.md
  
  extraction_result:
    total_terms_found: 45
    by_category:
      technique: 12
      interpretation: 18
      calculation: 15
    
  alignment_result:
    matched_existing: 30
    new_candidates: 10
    ambiguous: 5
    
  glossary_updates:
    terms_added: 8
    terms_pending_review: 2
    
  vector_store_updates:
    documents_chunked: 1
    chunks_added: 15
    embeddings_generated: 15
    
  quality_checks:
    duplicate_terms: 0
    orphaned_references: 0
    language_detection_confidence: 0.95
```

## Important Nuances

### 1. Language Detection

Auto-detect term language:
```python
def detect_language(text):
    """Detect if text is Russian or English."""
    ru_chars = sum(1 for c in text if c in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
    en_chars = sum(1 for c in text if c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    if ru_chars > en_chars:
        return 'ru'
    elif en_chars > ru_chars:
        return 'en'
    else:
        return 'unknown'
```

### 2. Term Disambiguation

Handle terms with multiple meanings:
```
"Дом" can mean:
1. House (astrology) - IV дом, VII дом
2. Home (general) - домашняя страница

Context determines meaning.
```

### 3. Hierarchy Tracking

Track term relationships:
```yaml
term: "Трин"
parent: "Мажорные аспекты"
siblings: ["Секстиль"]
children: ["Трин в знаках", "Трин по дому"]
```

### 4. Source Attribution

Always track source:
```yaml
term: "Фазовый анализ"
source:
  type: seminar
  author: "Захарьян"
  year: 2025
  location: "Москва"
```

### 5. Version Control

Glossary is versioned:
```
docs/ASTRO_GLOSSARY.md
docs/ASTRO_GLOSSARY_v1.md (archived)
docs/ASTRO_GLOSSARY_v2.md (current)
```

### 6. Review Workflow

New terms require review:
```
Extracted → Pending Review → Approved → Added to Glossary
```

## Examples

### Example 1: Process Methodology Document

**User says:** "Add phase analysis methodology to knowledge base"

**Actions:**
1. Load source document
2. Extract terms (45 terms)
3. Align with existing glossary
4. Add new terms (pending review)
5. Update vector store

**Result:**
```yaml
ingestion_report:
  terms_extracted: 45
  new_candidates: 10
  terms_added: 8
  vector_chunks_added: 15
```

### Example 2: Bilingual Term Lookup

**User says:** "What is Russian term for 'quincunx'?"

**Actions:**
1. Search glossary for 'quincunx'
2. Find RU-EN mapping
3. Return Russian equivalent

**Result:**
```
quincunx = квинконс (150°)
```

### Example 3: Disambiguation Request

**User says:** "What does 'дом' mean in this context: IV дом?"

**Actions:**
1. Parse context "IV дом"
2. Recognize Roman numeral + "дом"
3. Disambiguate as "house" (not "home")

**Result:**
```
дом = house (astrological)
IV дом = 4th house (IC, roots, family)
```

## Troubleshooting

### Error: Language detection fails

- **Cause:** Term is same in both languages (e.g., "аспект" / "aspect")
- **Solution:** Mark as bilingual, store both variants

### Error: Duplicate term detected

- **Cause:** Term already exists with different spelling
- **Solution:** Merge entries, add variant spelling

### Error: Vector store corruption

- **Cause:** Embedding dimension mismatch
- **Solution:** Rebuild vector store from sources

## Related Tasks

| Task | Relationship |
|---|---|
| ASTRO-006 | Multilingual knowledge ingestion — this skill implements the ingestion flow |
| ASTRO-011 | Core backbone — skill provides terminology backbone |
| ASTRO-017 | Skills architecture — this is a knowledge management skill |

## Available Code / Tools

### Source Documents
- `docs/ASTRO_GLOSSARY.md` — Existing glossary (RU/EN terms)
- `docs/HANDOFF_PROMPT_NEXT_AI.md` — Phase analysis methodology
- `docs/CONTEXT_REBUILD_METHOD.md` — Context reconstruction method
- `docs/MCP_PROVIDER_RESEARCH_20260301.md` — Provider research

### Vector Store
- `context_portal/context.db` — SQLite database for embeddings
- `context_portal/alembic/` — Database migrations
- `context_portal/conport_vector_data/` — Vector data files

### Term Mapping (from project)
- RU-EN astrology dictionary (see ASTRO-025 SKILL.md for full list)
- Phase dictionary (1..12): Impulse, Resource, Link, Base, Play, Service, Mirror, Transformation, Strategy, Result, Optimization, Archive

### Reference (from anthropics-skills repo)
- `.qwen/skills-source/anthropics-skills/skills/skill-creator/` — Skill creation patterns
- `.qwen/skills-source/anthropics-skills/skills/doc-coauthoring/` — Document processing

### Python Libraries (context_portal)
- SQLite for vector storage
- Alembic for migrations
- Embedding generation (model TBD)

## Acceptance Criteria

- [ ] SKILL.md created in `.qwen/skills/knowledge-ingestion/`
- [ ] Source documents loaded and parsed
- [ ] Terms extracted and categorized
- [ ] New terms aligned with existing glossary
- [ ] RU-EN term mappings created/updated
- [ ] Glossary updated with new terms
- [ ] Vector store updated with embeddings
- [ ] Ingestion report generated
- [ ] Review workflow for new terms defined

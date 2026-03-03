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

# Knowledge Ingestion

Process multilingual astrology methodology sources (RU/EN).

## Quick Start

**Input:**
```yaml
source_file: docs/phase_analysis_methodology.md
source_type: markdown
language: ru | en | auto
update_glossary: true
```

**Output:**
```yaml
terms_extracted: 45
matched_existing: 30
new_candidates: 10
glossary_updated: 8
vector_chunks_added: 15
```

## Core Workflow

### 1. Load Source

Support: `.md`, `.pdf`, `.docx`, `.txt`

### 2. Extract Terms

Categories:
- planets (планеты)
- signs (знаки)
- houses (дома)
- aspects (аспекты)
- techniques (методики)

### 3. Detect Language

Russian vs English character analysis.

### 4. Align with Glossary

```
matched → linked to existing entry
new → candidate for addition
ambiguous → multiple matches (manual review)
```

### 5. RU-EN Mapping

```
Солнце → Sun
Овен → Aries
трин → trine
прогрессии → progressions
```

### 6. Update Glossary

Add to `docs/ASTRO_GLOSSARY.md`:
```markdown
## Term: Фазовый анализ (Phase Analysis)
**Category:** technique
**Definition:** ...
```

### 7. Update Vector Store

Chunk → Embed → Store in `context_portal/context.db`.

## Reference Documents

- `docs/ASTRO_GLOSSARY.md` — Existing glossary
- `docs/HANDOFF_PROMPT_NEXT_AI.md` — Phase analysis methodology

## Term Categories

| Category | Examples |
|---|---|
| planets | Солнце, Луна, Меркурий |
| signs | Овен, Телец, Близнецы |
| aspects | соединение, трин, квадрат |
| techniques | прогрессии, дирекции, соляр |

## Examples

**Process doc:** `45 terms, 8 added to glossary`

**Term lookup:** `quincunx = квинконс (150°)`

**Disambiguation:** `дом = house (astro), not home`

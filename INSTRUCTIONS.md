# INSTRUCTIONS.md
# Medical Conference Scraper — Data Rules & Field Specifications

---

## 1. General Rules

- Extract only data **explicitly visible** on the page or API. Never infer or fabricate.
- Missing string field → `""`. Missing array field → `[]`. Never use `null` or omit a key.
- Every record must be a valid JSON object with all 9 top-level fields.
- Never carry over data from a previous record.

---

## 2. Text Cleaning

Apply to **all plain-text string fields** (in order):
1. Decode HTML entities (`&amp;` → `&`, `&nbsp;` → ` `)
2. Strip all HTML tags
3. Remove special/non-printable characters (`©`, `®`, `\u00a0`, `\u200b`, etc.)
4. Collapse multiple spaces or newlines into a single space
5. Strip leading and trailing whitespace

- **`abstract_html`** — exception: keep HTML exactly as-is from source.
- **`abstract_markdown`** — always `""`, never populate.
- Preserve meaningful Unicode: Greek letters (α, β, μ), `°`, mathematical symbols.

---

## 3. Required Top-Level Fields (9)

| # | Field | Type | Rule |
|---|-------|------|------|
| 1 | `link` | string | Direct URL to abstract page |
| 2 | `title` | string | Plain text, cleaned |
| 3 | `doi` | string | e.g. `10.1234/abc.567`; else `""` |
| 4 | `number` | string | Abstract/presentation ID; else `""` |
| 5 | `author_info` | string | Authors + affiliations, plain text, cleaned |
| 6 | `abstract` | string | Full abstract body, plain text, cleaned |
| 7 | `abstract_html` | string | Full abstract body, raw HTML preserved |
| 8 | `abstract_markdown` | string | **Always `""`** |
| 9 | `abstract_metadata` | object | See Section 4 |

---

Note: In the author information, the format should strictly follow: 'author_name; affiliation, author_name; affiliation' and it should not be anything else. If the author information is not available, then it should be an empty string. 
- **Location Filtering**: Strip out room names, hall numbers, or session times (e.g., "Richardson A", "Room 201") that may be erroneously merged into the author string in the source HTML.

## 4. `abstract_metadata` — 21 Sub-Fields

Below are the field which may or may not be present in the source website or api.
Default: `""` for strings, `[]` for arrays.

```json
{
  "session_name":         "",
  "session_id":           "",
  "session_type":         "",
  "session_track":        "",
  "session_description":  "",
  "date":                 "",
  "session_time":         "",
  "location":             "",
  "presentation_id":      "",
  "presentation_time":    "",
  "speaker_type":         "",
  "learning_objectives":  [],
  "ce_credit":            "",
  "ce_credit_hours":      "",
  "ce_credit_type":       "",
  "attendance_type":      "",
  "accreditation_status": "",
  "grant_disclosure":     "",
  "conflict_of_interest": "",
  "tags":                 [],
  "social_share_links":   []
}
```

### Field Rules

- **`session_name`** — Official session title. Plain text, cleaned.
- **`session_id`** — Session code. Take exactly as shown (e.g. `"SES-204"`).
- **`session_type`** — Take as-is (e.g. `"Oral Session"`, `"Poster Session"`, `"Plenary"`).
- **`session_track`** — Thematic track. Plain text, cleaned (e.g. `"Oncology - Thoracic"`).
- **`session_description`** — Session summary. Plain text, cleaned.
- **`date`** — Use session date if available; fall back to presentation date if not. Never both.
  - Formats (match source exactly, do not convert):
    - `"Month YYYY"` → `"May 2026"`
    - `"Month DD, YYYY"` → `"May 14, 2026"`
    - `"Day, Month DD, YYYY"` → `"Thursday, May 14, 2026"`
    - `"YYYY/MM/DD"` → `"2026/05/14"`
- **`session_time`** — Take exactly as written (e.g. `"8:00 AM - 10:00 AM"`).
- **`location`** — Room or hall. Plain text, cleaned (e.g. `"Hall B, Room 201"`).
- **`presentation_id`** — Presentation code. Take exactly as shown (e.g. `"OR-21"`).
- **`presentation_time`** — Take exactly as written (e.g. `"8:15 AM"`). Populate both `session_time` and `presentation_time` if both exist on source; otherwise only the one available.
- **`speaker_type`** — Take as-is (e.g. `"Invited Speaker"`, `"Keynote"`, `"Moderator"`).
- **`learning_objectives`** — Array of strings, one per objective. Plain text, cleaned.
- **`ce_credit`** — Take as-is from source (e.g. `"Yes"`, `"No"`).
- **`ce_credit_hours`** — String, not number (e.g. `"1.0"`).
- **`ce_credit_type`** — Take as-is (e.g. `"AMA PRA Category 1"`, `"CNE"`).
- **`attendance_type`** — Take as-is (e.g. `"In-Person"`, `"Virtual"`, `"Hybrid"`).
- **`accreditation_status`** — Plain text, cleaned (e.g. `"Accredited by ACCME"`).
- **`grant_disclosure`** — Full disclosure text. Plain text, cleaned.
- **`conflict_of_interest`** — Full COI text. Plain text, cleaned.
- **`tags`** — Array of keyword strings. Plain text, cleaned.
- **`social_share_links`** — Array of share URLs. Take exactly as-is, do not clean or encode.

---

## 5. Duplicate Handling

A record is a duplicate if any one matches:
1. Same `link`
2. Same `doi` (when non-empty)
3. Same `number` + `title` (case-insensitive)

When duplicates differ, keep the more complete record (more non-empty fields).

---

## 6. Advanced DOM Scenarios

- **Fragmented Titles**: If a title is split across multiple tags (e.g., `<h2><span>Part 1</span> Part 2</h2>`), ensure all text nodes are concatenated with a single space.
- **Hidden Session Logic**: For SPAs, verify that the session being scraped is the *correct* one by matching the title or index against the metadata from `urls.json`.

## 7. Output Format

- UTF-8 encoded JSON array.
- No trailing commas. Validate JSON before saving.
- URL file name: `{meeting_name}_{year}_urls.json`
- Raw file name: `{meeting_name}_{year}_raw.json`
- Dupliacte file name: `{meeting_name}_{year}_duplicates.json`
- Filename: `{meeting_name}_{year}.json`


### Example Record

```json
{
  "link": "https://example.com/abstract/123",
  "title": "Effect of Drug X on Tumor Microenvironment in Stage III NSCLC",
  "doi": "10.1234/example.2026.123",
  "number": "AB-123",
  "author_info": "Jane Doe1, John Smith2; 1City Cancer Center, 2Research Institute",
  "abstract": "Background: ... Methods: ... Results: ... Conclusion: ...",
  "abstract_html": "<p><strong>Background:</strong> ...</p>",
  "abstract_markdown": "",
  "abstract_metadata": {
    "session_name": "Late-Breaking Trials in Thoracic Oncology",
    "session_id": "SES-204",
    "session_type": "Oral Session",
    "session_track": "Oncology - Thoracic",
    "session_description": "Latest RCTs in lung and thoracic cancers.",
    "date": "Thursday, May 14, 2026",
    "session_time": "8:00 AM - 10:00 AM",
    "location": "Hall B, Room 201",
    "presentation_id": "OR-21",
    "presentation_time": "8:15 AM",
    "speaker_type": "Invited Speaker",
    "learning_objectives": ["Describe the mechanism of Drug X", "Identify eligible patient populations"],
    "ce_credit": "Yes",
    "ce_credit_hours": "1.0",
    "ce_credit_type": "AMA PRA Category 1",
    "attendance_type": "In-Person",
    "accreditation_status": "Accredited by ACCME",
    "grant_disclosure": "Supported by an educational grant from PharmaCo Inc.",
    "conflict_of_interest": "Jane Doe reports consulting fees from BioTech Ltd.",
    "tags": ["NSCLC", "Phase III", "PD-L1 inhibitor"],
    "social_share_links": ["https://twitter.com/intent/tweet?url=https://example.com/abstract/123"]
  }
}
```
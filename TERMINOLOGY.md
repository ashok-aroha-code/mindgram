## The Full Picture — A Medical Conference

The **whole thing** is called a **Conference** (or Meeting).
> Example: **SAWC Spring 2026**

***

## The 3 Levels

### 1. 🗂️ Session
A **session** is a **scheduled block of time** on the agenda dedicated to a specific topic.

> Example: **"WHS Session K: Concurrent Oral Abstracts I"**
- Has a start/end time: `10:30 AM – 11:30 AM`
- Has a room/location: `Richardson A`
- Has a type: `Concurrent Oral`, `Workshop`, `Pre-Conference`
- Has a track: `K2: Acute Wounds`
- One session contains **many presentations**

***

### 2. 🎤 Presentation
A **presentation** is a **single speaker's or group's slot** within a session.

> Example: **K2.01 — "Innovative Peptide-Based Technology..."**
- The number `K2.01` = **presentation ID** within the session
- Has its own authors, affiliation
- Is a **child of the session**
- One presentation is based on **one abstract**

***

### 3. 📄 Abstract
An **abstract** is the **written summary** of the research being presented.

> Example: The paragraph text — *"This hands-on experiential workshop delivers..."*
- Submitted by the researcher before the conference
- Describes the study: background, methods, results, conclusion
- The abstract is the **content** behind the presentation

***

## How It All Connects

```
CONFERENCE (SAWC Spring 2026)
└── SESSION (WHS Session K — 10:30 to 11:30 AM)
        ├── PRESENTATION K2.01
        │       └── ABSTRACT (the research text)
        ├── PRESENTATION K2.02
        │       └── ABSTRACT
        └── PRESENTATION K2.03
                └── ABSTRACT
```

***

## In Your JSON Schema

| JSON Field | Represents |
|---|---|
| `meeting_name` | Conference |
| `session_name`, `session_time`, `location` | Session |
| `number`, `title`, `author_info`, `presentation_time` | Presentation |
| `abstract`, `abstract_html`, `doi` | Abstract |

So your JSON is essentially storing **presentation-level records**, each enriched with its **parent session metadata** and the **abstract body text**. That's the perfect structure for this data!
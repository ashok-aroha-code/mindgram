# Medical Conference Scraper — Execution Flow

## 1. `url_scraper.py`

### Purpose

Collect all abstract or presentation URLs from the target website.

### Responsibilities

* Crawl all listing/index pages
* Handle pagination completely
* Collect every abstract URL
* Avoid missing pages or URLs
* Support resume capability

### Output

Generate a JSON file containing all collected URLs:

```text
{meeting_name}_{year}_urls.json
```

---

## 2. `abstract_scraper.py`

### Purpose

Scrape all abstract data from the collected URLs.

### Input

```text
{meeting_name}_{year}_urls.json
```

### Responsibilities

* Read all URLs from the URLs file
* Extract all required fields from each abstract page
* Preserve duplicate entries
* Do not perform duplicate removal at this stage
* If a field is missing:

  * Use `""` for string fields
  * Use `[]` for array fields
* Support resume capability

### Output

Generate a raw data file containing all records, including duplicates:

```text
{meeting_name}_{year}_raw.json
```

---

## 3. `duplicate_analysis.py`

### Purpose

Analyze duplicate entries from the raw dataset.

### Input

```text
{meeting_name}_{year}_raw.json
```

### Responsibilities

* Identify duplicate records
* A record is considered duplicate if:

  * `link` matches, OR
  * `doi` matches, OR
  * `number` + `title` match
* Create a separate file containing only duplicate records
* Include proper comparison context for human analysis
* Include both duplicate entries for comparison
* Do not remove duplicates automatically

### Output

Generate a duplicate analysis file:

```text
{meeting_name}_{year}_duplicates.json
```

---

# Human Review Step (Mandatory)

### Purpose

Manual verification of duplicate entries.

### Responsibilities

* Review `{meeting_name}_{year}_duplicates.json`
* Analyze duplicate records manually
* Make necessary corrections directly in:

```text
{meeting_name}_{year}_raw.json
```

### Important Rule

* Duplicate removal or modification must only happen after human verification.

---

## 4. `abstract_cleaner.py`

### Purpose

Clean and standardize the final dataset.

### Input

```text
{meeting_name}_{year}_raw.json
```

### Responsibilities

* Remove HTML tags
* Remove special characters
* Remove unnecessary whitespace
* Remove empty or invalid fields
* Format data according to the required schema
* Clean all plain-text fields
* Do not clean `abstract_html`
* Always set:

```json
"abstract_markdown": ""
```

* Remove empty fields from `abstract_metadata`
* Apply all formatting and validation rules from `INSTRUCTIONS.md`

### Date Rules

* Use `session_date` as the primary `date`
* Use `presentation_date` only if `session_date` is unavailable
* Preserve `presentation_time` exactly as provided
* Preserve `session_time` exactly as provided

### Validation

* Ensure all required fields are present
* Validate JSON structure
* Ensure UTF-8 encoding

### Output

Generate the final cleaned dataset file in the required format.

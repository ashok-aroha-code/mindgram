1. Read first FLOW.md file.
2. Read second INSTRUCTIONS.md file.
3. Collect all data with duplicate entries from the website or API.
4. Remove all duplicate entries from the collected data.
5. Clean the data by removing any special characters or html tags.
6. Format the data according to the specified format.
7. Save the data to the specified format.


# FLOW.md
# Medical Conference Scraper — Agent Execution Flow

---

1. **Read `INSTRUCTIONS.md`**
   - Understand all field rules, cleaning rules, date formats, and output format before doing anything else.

2. **Discover all abstract URLs**
   - Crawl the listing/index page(s).
   - Follow pagination until all pages are exhausted.
   - Build a complete list of individual abstract URLs before extracting anything.

3. **Scrape raw data from each URL**
   - For each URL, extract all 9 required fields.
   - If a field is not found, set it to `""` or `[]` — do not skip the record.
   - create file with output file with all fields with duplicates name it as {meeting_naem}_{year}_raw.json



4. **Remove duplicate records**
   - A record is a duplicate if it shares the same `link`, same `doi`, or same `number` + `title`.
   - create a file with records of duplicate entries name it as {meeting_naem}_{year}_duplicates.json

5. **Clean all text fields**
   - Apply cleaning rules from `INSTRUCTIONS.md § 2` to all plain-text fields.
   - Do not clean `abstract_html`.
   - Always set `abstract_markdown` to `""`.

6. **Apply date and time rules**
   - Use `session_date` as the value for `date` — fall back to `presentation_date` only if session date is absent.
   - Keep `presentation_time` and `session_time` exactly as written on the source.

7. **Validate all records**
   - Ensure all 9 top-level fields are present in every record.
   - Ensure only valid `abstract_metadata` sub-fields are present.
   - Flag and log any invalid records.

8. **Save output**
    - Save as a UTF-8 JSON array in 
    - Verify the file is valid JSON before finishing.

9. ***Resume Cabililty*** alwasy be there in script. Means if the script is stopped in between, it should be able to resume from where it left off.
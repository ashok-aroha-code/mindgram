# Scraping Learnings: SAWC Spring 2026 (HMP Global Events)

## 1. Messy DOM Architecture (The "Ghost Sessions" Problem)
**Discovery**: The website structure for the agenda is not strictly isolated by tabs. 
*   **The Issue**: Clicking a "Day" tab (e.g., Wednesday) updates the UI, but in the underlying HTML, sessions from OTHER days (like Friday's WHS track) remain present and sometimes even marked as "visible" or non-hidden.
*   **Impact**: A standard scraper picking up all `.session` elements will get a mix of days, often hitting a limit or duplicate-filter before finding the actual sessions for the current day.
*   **Solution**: Always use the specific parent container IDs (e.g., `#wednesday-april-08-2026`) to isolate sessions, rather than relying on tab-click visibility alone.

## 2. Parallel Tracks and Hidden Sessions
**Discovery**: Some sessions are parallel or part of specialized tracks (like WHS vs. SAWC Plenary).
*   **The Issue**: The "WHS" track is often hard-coded into the first day's container even if the sessions take place later in the week. This pushes "real" afternoon sessions (like *Lymphedema Management*) further down or into different sub-containers.
*   **Solution**: Perform a "Brute Force" scroll to the bottom of the page to ensure all dynamic tracks and lazy-loaded sessions are fully rendered in the DOM before scraping.

## 3. Metadata Quality: Authors vs. Locations
**Discovery**: The faculty list often includes room labels (e.g., "Richardson A") inside the same CSS classes as author names.
*   **The Issue**: Simply grabbing all `.faculty-group-name` text results in "Richardson A" being appended to author lists.
*   **Solution**: Use a Regex filter or negative-match list to strip known room names/locations from the `author_info` field and move them to `abstract_metadata.location`.

## 4. Title Fallbacks
**Discovery**: Some session descriptions contain multiple abstracts but no clear bold titles for each talk.
*   **The Issue**: Fragmented HTML makes it hard to distinguish where one talk ends and another begins.
*   **Solution**: 
    1. Use the `session__header` as the primary title.
    2. If the header is generic (e.g., "WHS Session A"), use the first line of the abstract text as a sub-title.
    3. Use the `urls.json` identifier as a final safety fallback to ensure no session is saved without a name.

## 5. Script Stability (Driver Cleanup)
**Discovery**: The `undetected-chromedriver` can sometimes throw `WinError 6` during shutdown.
*   **Solution**: This is a known behavior of the driver cleanup process. It does not affect data integrity. The `BaseScraper` should gracefully catch this or ignore it if the data has already been saved.

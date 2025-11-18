# Advanced Search

Use the search features below to find specific information across the Epstein Estate Documents collection.

## Quick Search

Use the search bar at the top of this page to search across all content.

## Search Tips

### Basic Search

- Enter any keyword to search across all documents and entities
- Search is case-insensitive
- Searches both document text and entity names

### Advanced Operators

The search functionality supports several operators:

- **Exact phrase:** Use quotes `"Jeffrey Epstein"`
- **Multiple terms:** Space-separated terms find documents containing all terms
- **Exclude terms:** Use `-` before a word to exclude it (e.g., `Epstein -email`)

### Search Scope

The search covers:

- **Document text:** Full OCR text from all 2,897 documents
- **Entity names:** All 6,607 extracted entities
- **Metadata:** Document dates, custodians, email headers
- **Relationships:** Entity connections and co-occurrences

## Browse by Category

If you're not sure what to search for, try browsing by category:

### [👥 People](entities/people/index.md)
Search through 2,099 individuals mentioned in the documents

### [🏢 Organizations](entities/organizations/index.md)
Search through 1,882 organizations, companies, and institutions

### [📍 Locations](entities/locations/index.md)
Search through 565 geographic locations and properties

### [📅 Events & Dates](entities/events/index.md)
Search through 1,965 significant dates and events

### [📄 Documents](documents/index.md)
Browse all 2,897 documents with full text

## Common Searches

Here are some common search queries to get you started:

- Jeffrey Epstein <!-- Use search bar above to search for: Jeffrey Epstein -->
- Bill Clinton <!-- Use search bar above to search for: Bill Clinton -->
- Donald Trump <!-- Use search bar above to search for: Donald Trump -->
- Email communications <!-- Use search bar above to search for: email -->
- Financial documents <!-- Use search bar above to search for: financial -->
- House Oversight <!-- Use search bar above to search for: House Oversight -->
- [2008 events](entities/events/2008.md)
- New York locations <!-- Use search bar above to search for: New York -->

## Filter by Type

You can filter search results by entity type:

- **People only:** Add `people:` prefix (e.g., `people:Clinton`)
- **Organizations only:** Add `organizations:` prefix (e.g., `organizations:FBI`)
- **Locations only:** Add `locations:` prefix (e.g., `locations:Florida`)
- **Events only:** Add `events:` prefix (e.g., `events:2008`)

## Search Examples

### Find all documents from a specific person

```
email_from:"john@example.com"
```

### Find documents within a date range

```
date_created:2008
```

### Find entities connected to a specific person

Navigate to the person's entity page and view the "Related Entities" section.

### Find documents mentioning multiple people

```
"Jeffrey Epstein" AND Clinton
```

## Visual Search

For a visual exploration of entity relationships, use the search and entity pages to explore connections between people, organizations, locations, and events.

## Export Search Results

MkDocs search results cannot be exported directly, but you can:

1. Navigate to specific entity pages
2. View the "Mentioned in Documents" section
3. Access document pages with full metadata and text
4. Copy or download information as needed

## Troubleshooting

**No results found?**

- Check spelling and try alternative names
- Try broader search terms
- Use the browse categories to explore
- Browse entity pages for connections

**Too many results?**

- Use exact phrases with quotes
- Add more specific terms
- Filter by entity type
- Use date ranges or metadata filters

**Looking for related information?**

- Visit entity pages to see "Related Entities"
- Browse entity pages to explore connections
- Check document metadata for cross-references

---

## About the Search Index

The search index includes:

- **2,897 documents** with full text (43,351 pages)
- **6,607 entities** across all types
- **500,000 relationships** between entities
- **Complete metadata** including dates, custodians, and email headers

The search is powered by MkDocs' built-in search functionality, which uses a client-side search index for fast, privacy-preserving searches.

---

*Last updated: November 2025*

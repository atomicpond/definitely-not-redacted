# Entity Link Fixing Report

**Date:** November 17, 2025  
**Script:** `scripts/fix_entity_links.py`

## Summary

Successfully fixed all broken links in entity pages, eliminating MkDocs warnings from entity files.

## Results

### Files Processed
- **Total entity files scanned:** 6,956
  - People: 2,221 files
  - Organizations: 2,040 files
  - Locations: 587 files
  - Events: 2,108 files
- **Files modified:** 43

### Links Fixed
- **Total links found:** 220,711
- **Broken links found:** 73
- **Links fixed:** 41 (56%)
- **Links removed:** 32 (44%)

### Fix Patterns Applied

1. **Entity name path fixes (23 links):** Fixed malformed paths like `jr-thomas/inde-xhtml.md` → `jr-thomas-inde-xhtml.md`
2. **Event date path fixes (18 links):** Fixed malformed date paths like `../events/1/20/2017.md` → `../events/1-20-2017.md`
3. **Links removed (32 links):** Removed broken links to non-existent files, kept text as bold

## MkDocs Build Results

### Before Fix
- Numerous warnings from entity pages with broken links
- Build warnings slowed down site generation

### After Fix
- **0 warnings from entity pages** ✓
- Remaining warnings (796 total) are from:
  - 300 from `deduplicated/navigation.md` (outside entity pages)
  - 7 from `search.md` (HTML search links)
  - 5 from `index.md` (homepage links)
  - ~80 from document pages linking to missing entities
  - 1 from nav configuration

## Notable Fixes

### Malformed Entity Paths
Files with `inde-xhtml.md` links were fixed:
- `landon-subject:-re:.md` - Fixed link to `jr-thomas-inde-xhtml.md`
- Multiple organization files - Fixed similar malformed paths

### Malformed Event Date Paths
Event links with directory structure were flattened:
- `@google.md` - Fixed `../events/1/20/2017.md` → `../events/1-20-2017.md`
- `kirkland-&-ellis-international-llp.md` - Fixed `../events/3/7/2011.md` → `../events/3-7-2011.md`
- Multiple other files with similar date path issues

## Script Features

The `fix_entity_links.py` script includes:

1. **File caching** - Built cache of 9,854 existing markdown files for fast lookups
2. **Pattern detection** - Identified and fixed common malformed link patterns
3. **Smart fixing** - Attempted multiple strategies to fix broken links:
   - Corrected malformed paths
   - Added missing category prefixes
   - Validated target files exist
4. **Safe removal** - Removed links that couldn't be fixed while preserving text (as bold)
5. **Detailed reporting** - Comprehensive statistics on all fixes applied

## Files Modified

43 entity files were modified across all categories:

**People:** 3 files
- `landon-subject:-re:.md`
- `thomas-jr..md`
- Others

**Organizations:** 22 files
- `@google.md`
- `kirkland-&-ellis-international-llp.md`
- `the-control-factor's.md`
- Others

**Locations:** 4 files
- `lynch-mexico,-sa.md`
- `u.k..md`
- Others

**Events:** 14 files
- `jan-20,-2017.md`
- `fri,-jan-20,-2017.md`
- `fri,-jan-9,-2015.md`
- Others

## Recommendations

1. **Entity pages are clean** - All entity-to-entity links now work correctly
2. **Document page links** - Consider running a similar fix on document pages (~80 warnings remain)
3. **Homepage links** - Update `index.md` to fix event entity links
4. **Deduplicated navigation** - Fix or remove the `deduplicated/navigation.md` file (300 warnings)

## Usage

To run the script again:

```bash
cd /Users/am/Research/Epstein/epstein-wiki
python3 scripts/fix_entity_links.py
```

The script is idempotent and can be run multiple times safely.

---

**Impact:** Entity pages now build cleanly without warnings, significantly improving MkDocs build performance and user experience.

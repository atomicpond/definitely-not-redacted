# Duplicate Analysis Statistics

## Overview

This page provides detailed statistics about the duplicate document analysis.

### Analysis Configuration

- **Analysis Date:** 2025-11-17 14:59:12
- **Similarity Threshold:** 95%
- **Email Header Stripping:** Enabled
- **Total Documents Analyzed:** 2,897

### Results Summary

| Metric | Count |
|--------|-------|
| Total Duplicate Groups | 681 |
| Exact Duplicate Groups | 9 |
| Similar Groups (≥95%) | 672 |
| Total Duplicate Documents | 681 |
| Canonical Documents | 681 |
| Unique Documents | 2,216 |

### Similarity Distribution

| Similarity Range | Groups |
|-----------------|--------|
| 100% (Perfect Match) | 6 |
| 98-99.9% | 217 |
| 95-97.9% | 431 |
| 95-94.9% | 0 |


### Deduplication Impact

By identifying duplicates, researchers can:
- **Focus on unique content** - Avoid reading the same document multiple times
- **Understand document relationships** - See how documents are connected
- **Save time** - Skip redundant analysis
- **Improve accuracy** - Ensure comprehensive coverage without double-counting

### Methodology

**Exact Duplicates:**
- Identified using SHA-256 content hashing
- 100% identical file contents
- Different Bates IDs may point to same document

**Similar Documents:**
- Identified using text similarity analysis
- Email headers stripped before comparison
- Uses sequence matching algorithms
- Minimum similarity threshold enforced

**Canonical Selection:**
- First document in each group chosen as canonical
- Typically the lowest Bates ID
- All duplicates reference the canonical version

---

[← Back to Duplicates Overview](index.md)

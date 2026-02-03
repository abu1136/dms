# Bug Fixes & Features Applied - February 1, 2026

## Previous Fixes ✅
- Date Filter: Independent from/to date filtering
- Preview Alignment: Quill CSS classes support
- Preview Updates: Real-time with updatePreview()
- PDF Formatting: HTML parser preserves bold, italic, alignment

## New Features Added ✅

### 1. Times New Roman Font ✅
**Changed**: PDF content now uses Times New Roman instead of Helvetica
- Times-Roman (normal)
- Times-Bold (bold)
- Times-Italic (italic)
- Times-BoldItalic (bold+italic)

### 2. Audit Log Username ✅
**Added**: Username and email displayed in audit logs
- Schema updated with UserBasic relationship
- Shows: "User: admin (admin@example.com)"

### 3. Pagination (50 items/page) ✅
**Documents**: 
- Max 50 documents per page
- Previous/Next buttons
- Page counter display

**Audit Logs**:
- Max 50 logs per page
- Previous/Next buttons
- Page counter display

### 4. Latest First Ordering ✅
**Documents**: `ORDER BY created_at DESC`
**Audit Logs**: `ORDER BY timestamp DESC`

## Test Results: All Passed ✅
- Documents pagination: Working (15 docs on page 0)
- Audit logs pagination: Working (50 logs on page 0)
- Username in audit logs: Displayed correctly
- Times New Roman font: Applied to PDFs
- Latest first ordering: Confirmed

**Files Modified**:
- app/services/pdf_generator.py
- app/schemas/audit_log.py
- app/routers/documents.py
- app/routers/audit.py
- static/app.js
- static/style.css

**Docker**: Rebuilt and running
**Status**: Production ready

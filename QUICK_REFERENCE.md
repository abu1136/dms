# DMS Quick Reference Guide - All Features

## 🚀 Quick Start
- **URL**: http://localhost:8000
- **Default Login**: admin / admin123
- **Default User**: user / user123 (if created)

## 📁 Where Are My Files Stored?

| File Type | Location | Docker Location |
|-----------|----------|-----------------|
| Generated Documents (PDF) | `/home/shuser/DMS/storage/uploads/` | `/app/storage/uploads/` |
| Document Templates | `/home/shuser/DMS/storage/uploads/templates/` | `/app/storage/uploads/templates/` |
| Backup Files (ZIP) | `/home/shuser/DMS/storage/backups/` | `/app/storage/backups/` |

**Document naming format**: `DOC-YYYYMMDD-XXXX.pdf`
- Example: `DOC-20260131-0001.pdf`, `DOC-20260201-0002.pdf`

## 📋 Tab Guide

| Tab | Role | Features |
|-----|------|----------|
| **Create Document** | User/Admin | Write content with CKEditor 5, select template, generate PDF |
| **Documents** | User/Admin | View, search, preview, download all documents |
| **Templates** | Admin | Upload letterhead templates, manage document designs |
| **Users** | Admin | Create/manage user accounts and roles |
| **Audit Logs** | Admin | View all system activities with timestamps and user tracking |
| **Backup & Restore** | Admin | Backup/restore documents + templates, download backup files |

## ✨ Key Features

### 1. Create Documents with Advanced Editor
- **Editor**: CKEditor 5 with full toolbar
- **Supported Elements**: Tables, lists, headings (H1-H3), bold/italic, colors, page breaks
- **Special Characters**: Rupee symbol (₹) renders correctly
- **Live Preview**: See formatted output while typing (in create tab)

### 2. Preview Before Download
- Click **Preview** button next to any document
- Opens PDF in modal showing exact printed output
- Includes page numbers, footer, and formatting

### 3. Multi-Page Documents
- Create long documents with automatic page breaks
- Each page includes company letterhead (template)
- Footer shows: Document number | Page X | Generated timestamp
- Perfect for reports, contracts, proposals

### 4. Document Management
- **Search**: Filter by document number, title, creator, date
- **Pagination**: 50 documents per page
- **Ordering**: Newest documents first (descending)
- **Download**: Get PDF anytime
- **Preview**: See exactly how PDF looks

### 5. Backup & Restore (Admin Only)
- **Backup Now**: Creates ZIP with all documents + templates
- **View Backups**: List all backup files with size and date
- **Download**: Save backup to your computer
- **Restore**: Upload and restore from any previous backup

### 6. Audit Logs (Admin Only)
- Track all document creation
- See who accessed what and when
- JSON format logging with timestamps
- Pagination with 50 entries per page

## 🎮 How To...

### Create a New Document
1. Click **Create Document** tab
2. Enter document title (e.g., "Invoice #123")
3. Select a template (or use default)
4. Type/paste content in CKEditor
5. Click **Generate Document**
✅ Done! Document created with unique number

### Preview a Document
1. Go to **Documents** tab
2. Find document in list
3. Click **Preview** button
4. PDF opens in modal
5. Close modal to return

### Add Tables to Document
1. In CKEditor, place cursor where you want table
2. Click table icon in toolbar
3. Select table size (e.g., 3x3)
4. Fill in content
5. Generate document - table renders perfectly in PDF

### Use Page Breaks
1. In CKEditor, position cursor where you want page break
2. Click menu → Insert page break (or use keyboard shortcut)
3. Continue typing on next page
4. Generate document - page break applied, letterhead on each page

### Backup Everything
1. Click **Backup & Restore** tab (admin only)
2. Click **Backup Now**
✅ Creates ZIP with all documents and templates
3. Optional: Click **Download** to save backup file

### Restore from Backup
1. Go to **Backup & Restore** tab
2. Click **View Backups**
3. Find the backup to restore
4. Click **Restore**
5. Confirm when prompted
✅ Done! All data restored

## 🔐 Security Features

- **JWT Authentication**: Secure token-based login
- **Password Hashing**: Bcrypt encryption (argon2 for future)
- **No URL Credentials**: Credentials no longer appear in URL bar
- **Role-Based Access**: Separate permissions for admin and user
- **Audit Trail**: All actions logged with user and timestamp
- **Secure Storage**: Files stored in protected Docker volumes

## 🛠 Technical Details

| Component | Details |
|-----------|---------|
| **Backend** | FastAPI 0.111.0, Python 3.11 |
| **Database** | MySQL 8.0 with SQLAlchemy |
| **Editor** | CKEditor 5 (CDN-based) |
| **PDF Generator** | ReportLab 4.2.2, PyPDF2 3.0.1 |
| **Authentication** | JWT tokens, bcrypt passwords |
| **Timezone** | Asia/Kolkata (IST) |
| **Font** | Times New Roman + DejaVu Sans |
| **Logging** | Structlog JSON format |
| **Container** | Docker Compose (3 services) |

## 📊 Pagination & Limits

- **Documents per page**: 50 (newest first)
- **Audit logs per page**: 50 (newest first)
- **Search results**: Paginated, 50 per page
- **Max document size**: Limited by PDF generation (typically 50-100 pages safe)

## ⚙️ Docker Commands

Start system:
```bash
cd /home/shuser/DMS
sudo docker compose up -d
```

Stop system:
```bash
sudo docker compose down
```

View logs:
```bash
sudo docker compose logs app --tail 50
```

Check status:
```bash
sudo docker compose ps
```

## 🆘 Troubleshooting

**Q: Preview modal not showing?**
- A: CSS fix applied in Phase 13 - restart container: `sudo docker compose restart app`

**Q: Rupee symbol (₹) showing as box?**
- A: DejaVu fonts installed - rebuild: `sudo docker compose up --build`

**Q: Login not working?**
- A: Check browser console for errors, clear cookies, try incognito mode

**Q: Can't find output files?**
- A: Check `/home/shuser/DMS/storage/uploads/` - files named as DOC-YYYYMMDD-XXXX.pdf

**Q: Backup button not visible?**
- A: Only admins see Backup tab - login as admin user

## 📞 Support Resources

- **Swagger UI**: http://localhost:8000/docs (API documentation)
- **Database**: MySQL on port 3306 (accessible to containers)
- **Logs**: `sudo docker compose logs app`
- **File Storage**: Check actual directories for verification
- **Code**: Located in `/home/shuser/DMS/app/` directory

## 🎯 Next Steps

1. **Test all features**: Create document → Preview → Download → Backup
2. **Create templates**: Upload custom letterhead templates
3. **Manage users**: Create additional user accounts with different roles
4. **Review audit logs**: See system activity history
5. **Try advanced formatting**: Tables, page breaks, special characters

## ✅ Feature Checklist

- ✅ Create documents with advanced editor
- ✅ Preview documents before download
- ✅ Multi-page support with automatic page breaks
- ✅ Company letterhead on each page
- ✅ Auto document numbering
- ✅ Search and filter documents
- ✅ Audit logging with timestamps
- ✅ Admin user management
- ✅ Backup and restore functionality
- ✅ Rupee symbol support (₹)
- ✅ Secure JWT authentication
- ✅ Role-based access control

**All features implemented and working! ✨**

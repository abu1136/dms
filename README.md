# Document Management System (DMS)

A production-ready web-based Document Management System built with FastAPI, MySQL, and modern web technologies. Generate, store, and manage company documents on official letterhead with automatic document numbering and comprehensive audit logging.

## Features

- **User Authentication**: Secure JWT-based login system with no credentials in URL
- **Role-Based Access Control**: Admin and User roles with different permissions
- **Document Generation**: Create documents using predefined templates with company letterhead
- **Advanced Text Editor**: CKEditor 5 with table insertion, page breaks, and rich formatting
- **Auto Document Numbering**: Unique sequential document numbers (format: DOC-YYYYMMDD-XXXX)
- **Document Storage**: Store and manage PDF documents with secure file handling
- **Search & Filter**: Find documents by number, title, user, or date with pagination (50 items/page)
- **Audit Logging**: Track all document creation and access events in JSON format
- **Document Preview**: Preview generated PDF documents in a modal before downloading
- **Multi-Page Support**: Automatic page breaking with company letterhead template on each page
- **Universal Font Support**: Comprehensive Unicode support for 150+ languages
- **Special Characters**: Supports rupee (₹), currency symbols, mathematical operators, and emoji
- **Document Templates**: Upload custom letterhead templates
- **Backup & Restore**: Complete data backup and restore functionality (admin only)

## Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Database**: MySQL 8.0 with SQLAlchemy ORM
- **Authentication**: JWT tokens with passlib bcrypt
- **PDF Generation**: ReportLab
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Migrations**: Alembic
- **Logging**: Structlog
- **Containerization**: Docker & Docker Compose

## Project Structure

```
DMS/
│   │   ├── document.py
│   │   ├── audit_log.py
│   │   └── document_sequence.py
│   ├── routers/              # API endpoints
│   │   ├── auth.py
│   │   ├── documents.py
│   │   ├── users.py
│   │   └── audit.py
│   ├── schemas/              # Pydantic schemas
│   │   ├── user.py
│   │   ├── document.py
│   │   └── audit_log.py
│   └── services/             # Business logic
│       ├── audit.py
│       ├── document_number.py
│       └── pdf_generator.py
├── alembic/                  # Database migrations
│   ├── versions/
│   └── env.py
├── static/                   # Frontend assets
│   ├── style.css
│   └── app.js
├── templates/                # HTML templates
│   └── index.html
├── storage/                  # Document storage
│   └── uploads/
├── tests/                    # Test files
├── main.py                   # FastAPI application
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── alembic.ini             # Alembic configuration
└── README.md               # This file
```

MYSQL_HOST=db
MYSQL_PORT=3306
MYSQL_DB=dms
MYSQL_USER=dms_user
MYSQL_PASSWORD=dms_password

JWT_SECRET_KEY=change_me_to_a_random_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com

COMPANY_NAME=Example Company Ltd.
COMPANY_ADDRESS=123 Business Road, City, Country

STORAGE_DIR=/app/storage/uploads
```

**Important**: Change `JWT_SECRET_KEY` and `ADMIN_PASSWORD` in production!

## Installation & Setup

### Using Docker (Recommended)

1. **Clone the repository**:
   ```bash
   cd /path/to/DMS
   ```

2. **Copy environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env`** and set your configuration (especially `JWT_SECRET_KEY` and `ADMIN_PASSWORD`)

4. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

5. **Access the application**:
   - Web UI: http://localhost:8000
   - API Docs: http://localhost:8000/docs

6. **Default login credentials**:
   - Username: `admin`
   - Password: `admin123` (or what you set in `.env`)

### Manual Setup (Without Docker)

1. **Install Python 3.11+**

2. **Install MySQL 8.0+** and create database:
   ```sql
   CREATE DATABASE dms;
   CREATE USER 'dms_user'@'localhost' IDENTIFIED BY 'dms_password';
   GRANT ALL PRIVILEGES ON dms.* TO 'dms_user'@'localhost';
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Copy and edit `.env`**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

6. **Run the application**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Access the application**:
   - Web UI: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## API Documentation

Once the application is running, visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

### Key API Endpoints

#### Authentication
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/register` - Register new user (admin only)

#### Users
- `GET /api/users/me` - Get current user info
- `GET /api/users/` - List all users (admin only)

#### Documents
- `POST /api/documents/` - Create new document
- `GET /api/documents/` - List all documents
- `GET /api/documents/search` - Search documents
- `GET /api/documents/{id}` - Get document details
- `GET /api/documents/{id}/download` - Download document PDF

#### Audit Logs
- `GET /api/audit/` - List audit logs
- `GET /api/audit/user/{user_id}` - Get user's audit logs

### Example API Calls

**Login**:
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**Create Document**:
```bash
curl -X POST "http://localhost:8000/api/documents/?content=This%20is%20my%20document%20content" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sample Document",
    "template_name": "standard"
  }'
```

**List Documents**:
```bash
curl -X GET "http://localhost:8000/api/documents/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Download Document**:
```bash
curl -X GET "http://localhost:8000/api/documents/1/download" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  --output document.pdf
```

## Usage Guide

### 1. Login
- Navigate to http://localhost:8000
- Login with admin credentials (default: admin/admin123)

### 2. Create Documents
- Click "Create Document" tab
- Enter document title
- Select a template
- Add content
- Click "Generate Document"
- Document will be created with a unique number (e.g., DOC-20260131-0001)

### 3. View & Search Documents
- Click "Documents" tab to view all documents
- Use search bar to filter by title or document number
- Click "Download PDF" to get the document file

### 4. Audit Logs
- Click "Audit Logs" tab to view all system activities
- Track document creation, access, and user logins

### 5. User Management (Admin Only)
- Use API endpoint `/api/auth/register` to create new users
- Assign roles: "admin" or "user"
### 6. Backup & Restore (Admin Only)
- Click "Backup & Restore" tab (admin users only)
- **Backup Now**: Creates a ZIP file containing all documents and templates
- **View Backups**: Lists all available backup files with download and restore options
- **Download Backup**: Save a backup ZIP file to your computer
- **Upload & Restore**: Upload a previously downloaded backup file to restore data
- Backups are stored in `/app/storage/backups/` with timestamp naming

## API Endpoints - Backup & Restore (Admin Only)

#### Backup Operations
- `POST /api/admin/backup/create` - Create a new backup ZIP file
- `GET /api/admin/backup/list` - List all available backups with metadata
- `GET /api/admin/backup/download/{backup_name}` - Download a specific backup file
- `POST /api/admin/backup/restore` - Restore documents and templates from a backup ZIP

**Example Backup API Call**:
```bash
# Create backup
curl -X POST "http://localhost:8000/api/admin/backup/create" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE"

# List backups
curl -X GET "http://localhost:8000/api/admin/backup/list" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE"

# Download backup
curl -X GET "http://localhost:8000/api/admin/backup/download/backup_2025-01-30_120000.zip" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN_HERE" \
  --output backup.zip
```
## Database Models

### User
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email
- `hashed_password`: Bcrypt hashed password
- `role`: "admin" or "user"
- `is_active`: Account status
- `created_at`: Timestamp

### Document
- `id`: Primary key
- `document_number`: Unique (DOC-YYYYMMDD-XXXX)
- `title`: Document title
- `template_name`: Template used
- `requested_by_id`: Foreign key to User
- `created_at`: Timestamp
- `file_path`: PDF file path
- `file_name`: PDF filename
- `mime_type`: File MIME type

### AuditLog
- `id`: Primary key
- `user_id`: Foreign key to User
- `action`: Action performed
- `document_id`: Foreign key to Document (optional)
- `timestamp`: When action occurred
- `details`: Additional information

### DocumentSequence
- `id`: Primary key
- `sequence_date`: Date for sequence
- `last_number`: Last number used for the day

## Development

### Running Tests
```bash
pytest tests/
```

### Database Migrations

**Create new migration**:
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations**:
```bash
alembic upgrade head
```

**Rollback migration**:
```bash
alembic downgrade -1
```

### Adding New Document Templates

Edit `app/services/pdf_generator.py` to customize PDF generation and add new template styles.

## Production Deployment

### Security Features

This application includes comprehensive security hardening:

✅ **No Hardcoded Credentials**: All secrets use environment variables  
✅ **Rate Limiting**: 5 login attempts per minute per IP address  
✅ **Secure File Uploads**: UUID filenames, 50MB size limit, path traversal prevention  
✅ **Input Validation**: Pydantic validators on all user inputs  
✅ **Error Handling**: Generic client messages, detailed server-side logging  
✅ **Production Template**: `.env.production` with secure configuration guide

### Production Setup

1. **Configure Environment**:
   ```bash
   # Copy production template
   cp .env.production .env
   
   # Generate secure credentials
   # JWT Secret (64 characters)
   openssl rand -hex 32
   
   # Strong passwords
   openssl rand -base64 32
   
   # Edit .env and replace all "CHANGE_THIS" values
   nano .env
   
   # Secure the file
   chmod 600 .env
   ```

2. **Deploy**:
   ```bash
   docker compose up -d --build
   ```

3. **Verify**:
   ```bash
   # Check containers
   docker compose ps
   
   # Test API
   curl http://localhost:8000/docs
   
   # Test login (should work)
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=YOUR_ADMIN_PASSWORD"
   ```

### Additional Production Recommendations

1. **HTTPS/TLS**:
   - Use reverse proxy (nginx/Caddy) for HTTPS
   - Obtain SSL certificate (Let's Encrypt recommended)
   - Redirect HTTP to HTTPS

2. **Database**:
   - Use managed MySQL service or properly secured MySQL instance
   - Enable SSL for database connections
   - Regular automated backups
   - Enable encryption at rest

3. **Storage**:
   - Use persistent volumes for document storage
   - Implement backup strategy for uploaded files
   - Consider using object storage (S3, MinIO) for scalability

4. **Monitoring**:
   - Set up log aggregation (ELK stack, Loki)
   - Monitor application health and rate limiting
   - Set up alerts

5. **Performance**:
   - Use gunicorn with multiple workers instead of uvicorn directly
   - Set up reverse proxy (nginx)
   - Enable caching where appropriate

## Troubleshooting

**Database connection errors**:
- Ensure MySQL is running
- Check credentials in `.env`
- Wait for database to be ready (Docker health check)

**PDF generation fails**:
- Check storage directory permissions
- Ensure ReportLab is installed

**Token errors**:
- Check JWT_SECRET_KEY is set
- Verify token hasn't expired

## License

MIT License - feel free to use this project for any purpose.

## Support

For issues and questions, please check:
- API Documentation: http://localhost:8000/docs
- Application logs
- Database logs

---

**Built with ❤️ using FastAPI and Python**

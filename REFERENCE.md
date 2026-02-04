# DMS Reference Guide

Quick reference for deployment, security, and testing of the Document Management System.

## Quick Start

### Installation
```bash
git clone https://github.com/abu1136/dms.git
cd dms
cp .env.production .env
# Edit .env with your values
sudo docker compose up -d
```

### Access
- Application: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Default Login: admin / admin123 (change immediately)

## Configuration

### Environment Variables (.env)
```env
# Database
DATABASE_URL=mysql+pymysql://user:password@db:3306/dms
MYSQL_ROOT_PASSWORD=your_secure_password
MYSQL_USER=dms_user
MYSQL_PASSWORD=your_db_password

# Security
JWT_SECRET_KEY=your_secure_random_key_32chars
ADMIN_PASSWORD=your_secure_admin_password

# Application
ENVIRONMENT=production
DEBUG=False
```

### Generate Secure Keys
```bash
# JWT Secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Passwords (use password manager)
python -c "import secrets; print(secrets.token_urlsafe(16))"
```

## Security Features

### Active Security Measures
- ✅ JWT-based authentication with secure token handling
- ✅ Rate limiting: 5 requests/minute on login endpoint
- ✅ Input validation with Pydantic on all endpoints
- ✅ Secure file uploads (UUID filenames, 50MB limit)
- ✅ Role-based access control (Admin/User)
- ✅ Comprehensive audit logging
- ✅ Secure error handling (generic client messages)
- ✅ Environment-based configuration

### Best Practices
1. **Never commit** .env files to version control
2. **Change default** admin password immediately
3. **Use HTTPS** in production (configure reverse proxy)
4. **Regular backups** of database and uploads
5. **Monitor logs** for suspicious activity
6. **Keep dependencies** updated

## Testing

### Run Endpoint Tests
```bash
python test_phase8.py
```

### Expected Results
All critical endpoints should return:
- Authentication: 200 (login), 401 (unauthorized), 429 (rate limit)
- Data Access: 200 (documents, users, templates, audit)
- User Creation: 201 (created)
- Input Validation: 422 (invalid data)

## Common Tasks

### Start Application
```bash
sudo docker compose up -d
```

### Stop Application
```bash
sudo docker compose down
```

### View Logs
```bash
sudo docker compose logs -f app
```

### Backup Database
```bash
sudo docker exec dms-db mysqldump -u dms_user -p dms > backup.sql
```

### Restore Database
```bash
sudo docker exec -i dms-db mysql -u dms_user -p dms < backup.sql
```

### Database Migration
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration (admin only)

### Documents
- `GET /api/documents/` - List documents
- `POST /api/documents/` - Create document
- `GET /api/documents/{id}` - Get document
- `DELETE /api/documents/{id}` - Delete document

### Users
- `GET /api/users/` - List users (admin only)
- `PUT /api/users/{id}` - Update user (admin only)

### Templates
- `GET /api/templates/` - List templates
- `POST /api/templates/upload` - Upload template (admin only)

### Audit
- `GET /api/audit/` - Audit logs (admin only)

## Troubleshooting

### Database Connection Error
```bash
# Check database status
sudo docker compose ps

# Restart database
sudo docker compose restart db

# Check logs
sudo docker compose logs db
```

### Port Already in Use
```bash
# Find process on port 8000
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

### Permission Issues
```bash
# Fix storage permissions
sudo chown -R 1000:1000 storage/
sudo chmod -R 755 storage/
```

## Production Deployment

### Pre-Deployment Checklist
- [ ] Environment variables configured
- [ ] Default passwords changed
- [ ] HTTPS/SSL configured
- [ ] Firewall rules configured
- [ ] Backup strategy implemented
- [ ] Monitoring setup
- [ ] Log rotation configured

### Recommended Setup
1. Use reverse proxy (nginx/Traefik) for HTTPS
2. Configure firewall (allow 80, 443 only)
3. Setup automated backups
4. Configure log rotation
5. Enable monitoring (Prometheus/Grafana)
6. Setup CI/CD pipeline

## Support

For issues and questions:
- Check API documentation: http://localhost:8000/docs
- Review logs: `sudo docker compose logs`
- Consult README.md for detailed information

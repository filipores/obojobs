# Docker Deployment Guide

## Quick Start

### 1. Prerequisites
- Docker & Docker Compose installed
- Anthropic API Key

### 2. Setup

1. **Clone repository:**
```bash
cd /path/to/mailer
```

2. **Create .env file:**
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
nano .env
```

3. **Build and start:**
```bash
docker-compose up -d
```

4. **Check logs:**
```bash
docker-compose logs -f
```

### 3. Access

- **Frontend**: http://localhost
- **Backend API**: http://localhost:5001/api/health

### 4. Default User

After first start, a test user is created:
- **Email**: test@example.com
- **Password**: test123
- **Credits**: 50

---

## Commands

### Start services
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart services
```bash
docker-compose restart
```

### Rebuild (after code changes)
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Access backend container
```bash
docker exec -it mailer-backend /bin/bash
```

---

## Production Deployment

### 1. Environment Variables

**Required:**
- `ANTHROPIC_API_KEY`: Your Claude API key

**Recommended to change:**
- `SECRET_KEY`: Random 32+ character string
- `JWT_SECRET_KEY`: Random 32+ character string

**Optional:**
- `DATABASE_URL`: PostgreSQL URL (default: SQLite)
- `CORS_ORIGINS`: Comma-separated allowed origins

### 2. Generate secure keys

```bash
# Generate random keys
openssl rand -hex 32
```

### 3. Use PostgreSQL (optional)

Update docker-compose.yml:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: mailer
      POSTGRES_PASSWORD: your-secure-password
      POSTGRES_DB: mailer
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    environment:
      - DATABASE_URL=postgresql://mailer:your-secure-password@postgres/mailer
    depends_on:
      - postgres

volumes:
  postgres_data:
```

### 4. HTTPS with Nginx

Add nginx service:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
```

### 5. Backup

**Database:**
```bash
docker exec mailer-backend sqlite3 /app/db/mailer.db .dump > backup.sql
```

**Uploads:**
```bash
docker cp mailer-backend:/app/uploads ./backup_uploads
```

---

## Troubleshooting

### Backend won't start
```bash
docker-compose logs backend
# Check if ANTHROPIC_API_KEY is set
```

### Frontend can't reach backend
```bash
# Check if backend is running
docker-compose ps

# Check backend logs
docker-compose logs backend

# Test backend directly
curl http://localhost:5001/api/health
```

### Port already in use
```bash
# Change ports in docker-compose.yml
ports:
  - "8080:80"  # Frontend on port 8080
  - "5002:5001"  # Backend on port 5002
```

### Database locked
```bash
docker-compose down
docker volume rm mailer_database
docker-compose up -d
```

---

## Monitoring

### Health checks
```bash
curl http://localhost:5001/api/health
curl http://localhost/
```

### Resource usage
```bash
docker stats
```

### Logs
```bash
# Follow all logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Only backend
docker-compose logs -f backend
```

---

## Scaling

### Increase backend workers

Edit backend/Dockerfile:
```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--timeout", "120", "wsgi:app"]
```

### Load balancing

Use nginx or traefik to load balance multiple backend containers.

---

## Security Checklist

- [ ] Changed SECRET_KEY
- [ ] Changed JWT_SECRET_KEY
- [ ] ANTHROPIC_API_KEY is set
- [ ] HTTPS enabled (production)
- [ ] Database backups configured
- [ ] Firewall rules configured
- [ ] CORS_ORIGINS set to allowed domains only


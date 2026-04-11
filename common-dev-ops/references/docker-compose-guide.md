# Docker Compose Guide

## Overview

Best practices for orchestrating multi-container applications with Docker Compose.

---

## Compose File Structure

### Basic Structure

```yaml
# docker-compose.yml
version: '3.8'  # Optional in Compose V2

services:
  app:
    # Service definition
    
volumes:
  # Named volumes
  
networks:
  # Custom networks
  
secrets:
  # External secrets (Swarm mode)
  
configs:
  # External configs (Swarm mode)
```

---

## Service Configuration

### Complete Service Example

```yaml
services:
  api:
    # Build configuration
    build:
      context: ./api
      dockerfile: Dockerfile
      args:
        NODE_ENV: production
      target: production
    
    # Image (alternative to build)
    # image: myregistry/api:1.2.3
    
    # Container settings
    container_name: api
    hostname: api
    restart: unless-stopped
    
    # Port mapping
    ports:
      - "3000:3000"           # host:container
      - "127.0.0.1:3001:3001" # localhost only
    
    # Environment
    environment:
      NODE_ENV: production
      LOG_LEVEL: info
    env_file:
      - .env
      - .env.local
    
    # Volumes
    volumes:
      - ./src:/app/src:ro    # Bind mount (read-only)
      - node_modules:/app/node_modules  # Named volume
      - /app/dist            # Anonymous volume
    
    # Networking
    networks:
      - frontend
      - backend
    
    # Dependencies
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

---

## 🔴 BLOCKING Rules

### 1. Always Pin Versions

```yaml
# ✅ CORRECT
services:
  db:
    image: postgres:16.1-alpine3.19

# 🔴 WRONG
services:
  db:
    image: postgres:latest
```

### 2. Use Health Checks

```yaml
# ✅ CORRECT
services:
  db:
    image: postgres:16.1-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    depends_on:
      db:
        condition: service_healthy  # Wait for healthy
```

### 3. Separate Networks

```yaml
# ✅ CORRECT: Isolated networks
services:
  frontend:
    networks:
      - frontend-net
  
  api:
    networks:
      - frontend-net
      - backend-net
  
  db:
    networks:
      - backend-net  # Not accessible from frontend

networks:
  frontend-net:
  backend-net:
```

### 4. Use Named Volumes for Data

```yaml
# ✅ CORRECT: Named volume (persists)
volumes:
  postgres-data:

services:
  db:
    volumes:
      - postgres-data:/var/lib/postgresql/data

# 🔴 WRONG: Bind mount for database
services:
  db:
    volumes:
      - ./data:/var/lib/postgresql/data
```

### 5. Never Hardcode Secrets

```yaml
# ✅ CORRECT: Environment variable
services:
  api:
    environment:
      DATABASE_URL: ${DATABASE_URL}

# ✅ BETTER: External secret file
services:
  api:
    env_file:
      - .env  # Add to .gitignore!

# 🔴 WRONG: Hardcoded
services:
  api:
    environment:
      DATABASE_PASSWORD: supersecret123
```

---

## Environment Management

### Development vs Production

```yaml
# docker-compose.yml (base)
services:
  api:
    build: ./api
    environment:
      NODE_ENV: ${NODE_ENV:-development}

# docker-compose.override.yml (dev, auto-loaded)
services:
  api:
    volumes:
      - ./api/src:/app/src  # Hot reload
    ports:
      - "3000:3000"
      - "9229:9229"  # Debug port

# docker-compose.prod.yml
services:
  api:
    image: myregistry/api:${VERSION}
    restart: always
    deploy:
      replicas: 2
```

### Usage

```bash
# Development (uses override automatically)
docker compose up

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up
```

---

## Networking Patterns

### Service Discovery

```yaml
services:
  api:
    networks:
      - backend
  
  db:
    networks:
      - backend

networks:
  backend:

# api can reach db at: db:5432 (service name = hostname)
```

### External Access

```yaml
services:
  nginx:
    ports:
      - "80:80"      # All interfaces
      - "443:443"
    networks:
      - frontend
      - backend

  api:
    expose:
      - "3000"       # Internal only
    networks:
      - backend
```

---

## Volume Patterns

### Development: Bind Mounts

```yaml
services:
  api:
    volumes:
      - ./src:/app/src:ro           # Source code (read-only)
      - ./config:/app/config:ro     # Config files
      - node_modules:/app/node_modules  # Persist deps
```

### Production: Named Volumes

```yaml
services:
  db:
    volumes:
      - postgres-data:/var/lib/postgresql/data
  
  api:
    volumes:
      - uploads:/app/uploads

volumes:
  postgres-data:
    driver: local
  uploads:
    driver: local
```

### Backup Strategy

```yaml
# Backup volume to host
docker run --rm \
  -v postgres-data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/postgres-data.tar.gz /data
```

---

## Logging Configuration

```yaml
services:
  api:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service"
        tag: "{{.Name}}/{{.ID}}"
```

---

## Scaling

### Basic Scaling

```bash
docker compose up --scale api=3
```

### With Load Balancer

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api

  api:
    build: ./api
    expose:
      - "3000"
    # No ports - accessed through nginx
```

```nginx
# nginx.conf
upstream api {
    server api:3000;
}

server {
    listen 80;
    location / {
        proxy_pass http://api;
    }
}
```

---

## Complete Example: Full Stack App

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Frontend
  frontend:
    build:
      context: ./frontend
      target: production
    ports:
      - "80:80"
    depends_on:
      api:
        condition: service_healthy
    networks:
      - frontend-net
    restart: unless-stopped

  # API
  api:
    build:
      context: ./api
      target: production
    environment:
      DATABASE_URL: postgres://postgres:${DB_PASSWORD}@db:5432/app
      REDIS_URL: redis://redis:6379
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - frontend-net
      - backend-net
    restart: unless-stopped

  # Database
  db:
    image: postgres:16.1-alpine
    environment:
      POSTGRES_DB: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend-net
    restart: unless-stopped

  # Cache
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
    networks:
      - backend-net
    restart: unless-stopped

volumes:
  postgres-data:
  redis-data:

networks:
  frontend-net:
  backend-net:
```

---

## Useful Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f api

# Execute command in service
docker compose exec api npm run migrate

# Rebuild and restart
docker compose up -d --build

# Stop and remove
docker compose down

# Stop and remove with volumes
docker compose down -v

# View service status
docker compose ps

# View resource usage
docker compose top
```

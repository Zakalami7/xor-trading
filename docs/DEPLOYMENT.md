# XOR Trading Platform - Deployment Guide

## 📦 Deployment Options

1. **Docker Compose** - Development / Small scale
2. **Kubernetes** - Production / Scale
3. **Cloud Managed** - AWS/GCP/Azure

---

## 1. Docker Compose Deployment

### Prerequisites
- Docker 24+
- Docker Compose 2.20+
- 4GB RAM minimum
- 20GB disk space

### Steps

```bash
# 1. Clone repository
git clone https://github.com/yourusername/xor-trading.git
cd xor-trading

# 2. Configure environment
cd infrastructure/docker
cp .env.example .env

# 3. Edit .env with production values
nano .env
```

**.env Configuration:**
```env
# IMPORTANT: Change all these in production!
SECRET_KEY=<generate-32-char-random-string>
JWT_SECRET_KEY=<generate-32-char-random-string>
ENCRYPTION_KEY=<generate-32-byte-key>
POSTGRES_PASSWORD=<strong-password>

# Domain
FRONTEND_URL=https://app.yourdomain.com
API_URL=https://api.yourdomain.com
```

```bash
# 4. Start services
docker-compose -f docker-compose.yml up -d

# 5. Initialize database
docker-compose exec backend alembic upgrade head

# 6. Create admin user
docker-compose exec backend python -m scripts.create_admin

# 7. Verify services
docker-compose ps
```

---

## 2. Kubernetes Deployment

### Prerequisites
- Kubernetes 1.28+
- Helm 3.13+
- kubectl configured
- Ingress controller (nginx)
- Cert-manager for TLS

### Using Helm

```bash
# 1. Add Helm repo
helm repo add xor-trading ./infrastructure/helm

# 2. Create namespace
kubectl create namespace trading

# 3. Create secrets
kubectl create secret generic xor-secrets \
  --from-literal=secret-key="<your-secret>" \
  --from-literal=jwt-secret="<your-jwt-secret>" \
  --from-literal=encryption-key="<your-encryption-key>" \
  --from-literal=db-password="<db-password>" \
  -n trading

# 4. Install chart
helm install xor-trading ./infrastructure/helm/xor-trading \
  --namespace trading \
  --values ./infrastructure/helm/xor-trading/values-prod.yaml

# 5. Verify deployment
kubectl get pods -n trading
```

### values-prod.yaml Example

```yaml
global:
  environment: production
  domain: yourdomain.com

backend:
  replicas: 3
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 2000m
      memory: 2Gi
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPU: 70

executionEngine:
  replicas: 2
  resources:
    requests:
      cpu: 1000m
      memory: 256Mi

database:
  persistence:
    size: 100Gi
    storageClass: ssd

redis:
  persistence:
    size: 10Gi

ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  tls:
    - secretName: xor-tls
      hosts:
        - app.yourdomain.com
        - api.yourdomain.com
```

---

## 3. Multi-Region Setup

For optimal latency to exchanges:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Singapore   │     │  Frankfurt   │     │  New York    │
│  (Binance)   │────▶│  (Primary)   │◀────│  (Backup)    │
│              │     │  Database    │     │              │
│  Execution   │     │  + Backend   │     │  Execution   │
│  Engine      │     │              │     │  Engine      │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Recommended VPS Locations

| Exchange | Recommended Region |
|----------|-------------------|
| Binance | Singapore / Tokyo |
| Bybit | Singapore |
| OKX | Hong Kong |
| Kraken | New York / London |

---

## 4. SSL/TLS Configuration

### Using Cert-Manager (Kubernetes)

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
```

### Using Docker Compose (with Traefik)

```yaml
services:
  traefik:
    image: traefik:v2.11
    command:
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.le.acme.httpchallenge=true"
      - "--certificatesresolvers.le.acme.email=admin@yourdomain.com"
      - "--certificatesresolvers.le.acme.storage=/letsencrypt/acme.json"
    ports:
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./letsencrypt:/letsencrypt
```

---

## 5. Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 6. Backup Strategy

### Database Backups

```bash
# Manual backup
pg_dump -h localhost -U postgres xor_trading > backup.sql

# Automated (cron)
0 2 * * * pg_dump -h localhost -U postgres xor_trading | gzip > /backups/xor_$(date +\%Y\%m\%d).sql.gz
```

### Encrypted Backups

```bash
# Backup with encryption
pg_dump xor_trading | gpg --encrypt -r backup@yourdomain.com > backup.sql.gpg

# Restore
gpg --decrypt backup.sql.gpg | psql xor_trading
```

---

## 7. Monitoring Setup

### Prometheus + Grafana

Already included in docker-compose. Access:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

### Key Metrics to Monitor

| Metric | Alert Threshold |
|--------|----------------|
| API Latency P99 | > 500ms |
| Error Rate | > 1% |
| CPU Usage | > 80% |
| Memory Usage | > 85% |
| Order Success Rate | < 99% |
| WebSocket Connections | > 10k |

---

## 8. Health Checks

```bash
# API Health
curl https://api.yourdomain.com/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:00:00Z"
}
```

---

## 9. Troubleshooting

### Common Issues

**Database connection refused:**
```bash
# Check if postgres is running
docker-compose ps postgres
# Check logs
docker-compose logs postgres
```

**Redis connection issues:**
```bash
# Test Redis connection
docker-compose exec redis redis-cli ping
```

**High latency:**
- Check network connectivity to exchanges
- Verify VPS is in optimal region
- Monitor CPU/memory usage

---

## 10. Rollback Procedure

```bash
# List deployments
helm history xor-trading -n trading

# Rollback to previous version
helm rollback xor-trading [REVISION] -n trading

# For Docker
docker-compose down
docker-compose pull
docker-compose up -d
```

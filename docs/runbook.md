# Runbook — URL Shortener

## Alert: Service Down

**Symptoms:** `/health` returns non-200 or times out

**Steps:**
1. Check containers: `sudo docker ps`
2. If app container missing, wait 10s — `restart: always` will revive it
3. If it doesn't restart: `sudo docker compose up -d`
4. Check logs: `sudo docker compose logs app1 --tail=50`
5. If DB is down: `sudo docker compose restart db`
6. Verify: `curl http://localhost:8080/health`

## Alert: High Error Rate

**Symptoms:** Many 500 responses in logs

**Steps:**
1. Check logs: `sudo docker compose logs app1 --tail=100`
2. If DB connection errors: `sudo docker compose restart db`
3. If Redis errors: `sudo docker compose restart redis` (app works without Redis)
4. Verify recovery: `curl http://localhost:8080/health`

## Alert: Container Keeps Crashing

**Symptoms:** App container repeatedly exits

**Steps:**
1. Check crash logs: `sudo docker compose logs app1 --tail=30`
2. Common causes:
   - DB not ready → wait 30s, self-heals
   - Bad env var → check docker-compose.yml environment section
   - Port conflict → `lsof -i :8080`
3. Fix root cause then: `sudo docker compose up --build`

## Useful Commands

| Command | Purpose |
|---------|---------|
| `sudo docker compose ps` | Check container status |
| `sudo docker compose logs app1` | View app logs |
| `sudo docker compose restart app1` | Restart app only |
| `sudo docker compose down && sudo docker compose up -d` | Full restart |
| `curl http://localhost:8080/health` | Verify app is alive |

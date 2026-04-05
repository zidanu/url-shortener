# Capacity Plan

## Infrastructure
- 2 app containers (Flask + Gunicorn, 8 workers each)
- 1 PostgreSQL container
- 1 Redis cache
- 1 Nginx load balancer

## Load Test Results

### Bronze Baseline — 50 Concurrent Users
- **Tool:** k6
- **Concurrent Users:** 50
- **Error Rate:** 0%
- **p95 Response Time:** 783ms
- **Requests/sec:** 69

### Silver — 200 Concurrent Users (2 containers + Nginx)
- **Concurrent Users:** 200
- **Error Rate:** 0%
- **p95 Response Time:** 651ms
- **Requests/sec:** 396

### Gold — 500 Concurrent Users (+ Redis + 8 workers)
- **Concurrent Users:** 500
- **Error Rate:** 0%
- **p95 Response Time:** 2.01s
- **Requests/sec:** 304

## Bottleneck Report
**What was slow:** Flask dev server is single-threaded, causing 30% errors at 200 users.
The database was also hit on every redirect request with no caching.

**What we fixed:** Replaced Flask dev server with Gunicorn (8 workers per container),
added Redis caching so repeated redirects skip the database entirely, and added a
second app container behind Nginx for horizontal scaling.

**Result:** 0% error rate at 500 concurrent users, up from 30% errors at 200 users.

## Scaling Limits
| Setup | Estimated Capacity |
|-------|--------------------|
| Current (2 containers, Redis) | ~500 concurrent users |
| 4 containers + Redis | ~1000 concurrent users |
| Managed DB (RDS) + 4 containers | ~2000+ concurrent users |

## Breaking Points
1. **Database write throughput** — `/shorten` hits DB every time, no write caching
2. **Single PostgreSQL instance** — no read replicas
3. **Single Redis instance** — no Redis clustering

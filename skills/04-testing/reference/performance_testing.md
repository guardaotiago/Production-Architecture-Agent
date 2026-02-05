# Performance Testing

## Why Performance Test?

Performance bugs are insidious. Code that works in development can collapse under production traffic. Performance testing reveals bottlenecks, capacity limits, and degradation patterns before users hit them.

Test performance when:
- Launching a new service or feature
- Expecting traffic growth (marketing campaigns, launches)
- Changing infrastructure (new database, cloud migration)
- Modifying hot paths (auth, search, checkout)
- After significant refactoring

---

## Types of Performance Tests

### Load Testing

Simulate **expected** production traffic to verify the system handles normal load.

- **Goal**: Confirm response times and error rates stay within SLAs under typical load.
- **Example**: 500 concurrent users browsing and purchasing for 30 minutes.
- **Key metrics**: p50/p95/p99 response time, throughput (requests/sec), error rate.

### Stress Testing

Push **beyond** expected load to find the breaking point.

- **Goal**: Identify the maximum capacity and how the system degrades.
- **Example**: Ramp from 100 to 5000 concurrent users over 20 minutes.
- **Key metrics**: At what load do errors spike? Does the system recover after load drops?

### Soak Testing (Endurance)

Run at **moderate** load for an **extended** period.

- **Goal**: Detect memory leaks, connection pool exhaustion, disk usage growth, and slow degradation.
- **Example**: 200 concurrent users for 8-24 hours.
- **Key metrics**: Memory usage over time, response time trends, garbage collection pauses.

### Spike Testing

Apply a **sudden burst** of traffic.

- **Goal**: Verify the system handles sudden spikes (flash sales, viral content).
- **Example**: Jump from 100 to 3000 users in 10 seconds, sustain for 2 minutes, drop back.
- **Key metrics**: Recovery time, error rate during spike, autoscaling response time.

### Scalability Testing

Incrementally increase load while adding resources (horizontal/vertical scaling).

- **Goal**: Validate that adding capacity produces proportional improvement.
- **Example**: Double traffic, double servers -- does throughput double?

---

## Tools

### k6 (Recommended)

Modern, developer-friendly load testing tool. Write tests in JavaScript.

```javascript
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "2m", target: 100 },   // Ramp up to 100 users
    { duration: "5m", target: 100 },   // Stay at 100 users
    { duration: "2m", target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"],   // 95% of requests under 500ms
    http_req_failed: ["rate<0.01"],     // Less than 1% errors
  },
};

export default function () {
  const res = http.get("https://api.example.com/products");
  check(res, {
    "status is 200": (r) => r.status === 200,
    "response time < 500ms": (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

**Run**: `k6 run loadtest.js`

- Free and open source
- CI/CD friendly (exit code based on thresholds)
- Output to Grafana, Datadog, InfluxDB
- Excellent documentation

### Artillery

YAML-based configuration, good for API testing.

```yaml
config:
  target: "https://api.example.com"
  phases:
    - duration: 300
      arrivalRate: 10
      name: "Sustained load"

scenarios:
  - name: "Browse products"
    flow:
      - get:
          url: "/products"
      - think: 2
      - get:
          url: "/products/{{ $randomNumber(1, 100) }}"
```

**Run**: `artillery run loadtest.yml`

- YAML config, low learning curve
- Good for API-focused testing
- Built-in reporting

### Apache JMeter

GUI-based, enterprise-grade load testing.

- Wide protocol support (HTTP, JDBC, LDAP, FTP, SOAP)
- Visual test plan builder
- Extensive plugin ecosystem
- Heavy JVM footprint
- Better for teams that prefer GUI tools

### Locust

Python-based, code-first load testing.

```python
from locust import HttpUser, task, between

class WebUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def browse_products(self):
        self.client.get("/products")

    @task(1)
    def checkout(self):
        self.client.post("/checkout", json={"product_id": 1})
```

**Run**: `locust -f locustfile.py --host=https://api.example.com`

- Pythonic and extensible
- Real-time web UI for monitoring
- Distributed testing support
- Good for Python teams

---

## Performance Budgets

A performance budget is a set of limits that the application must meet. Define them before testing.

### Example Budgets

| Metric | Target | Critical |
|--------|--------|----------|
| Page load time (LCP) | < 2.5s | < 4.0s |
| API response time (p95) | < 200ms | < 500ms |
| API response time (p99) | < 500ms | < 1000ms |
| Time to First Byte | < 200ms | < 600ms |
| Error rate under load | < 0.1% | < 1.0% |
| Throughput | > 1000 rps | > 500 rps |
| Memory usage growth (soak) | < 5% / hour | < 10% / hour |

### How to Set Budgets

1. **Baseline**: Measure current performance in production.
2. **SLA requirements**: What does the business promise customers?
3. **User expectations**: Research shows users abandon pages after 3 seconds.
4. **Competitive benchmarks**: What do competitors achieve?
5. **Infrastructure cost**: What throughput justifies current infrastructure spend?

---

## Interpreting Results

### Key Metrics to Watch

- **p50 (median)**: The typical user experience.
- **p95**: 1 in 20 users is slower than this. This is what matters for SLAs.
- **p99**: 1 in 100. Often reveals outlier issues (GC pauses, cold caches, slow queries).
- **Throughput (rps)**: Requests per second the system can sustain.
- **Error rate**: Percentage of requests that fail (5xx, timeouts).
- **Apdex score**: Application Performance Index -- ratio of satisfied to total requests.

### Reading a Load Test Graph

```
Response Time (ms)
|
|            ___________
|           /           \____
|    ______/                  \___
|   /                              \____
|  /
| /
|/__________________________________ Requests/sec
```

- **Flat line**: System is handling load. Good.
- **Gradual climb**: System is degrading under load. Investigate.
- **Sudden spike**: A bottleneck was hit (connection pool, memory, CPU). Find and fix.
- **Sawtooth pattern**: Garbage collection or resource cycling. Check GC tuning.

### Red Flags

- Response times that keep climbing even after load stabilizes
- Error rate exceeding 1% under expected load
- Memory that grows continuously during soak tests (leak)
- CPU pinned at 100% with moderate load (inefficient code)
- Connection pool exhaustion messages in logs
- p99 more than 10x the p50 (high variance = inconsistent experience)

---

## Common Bottlenecks

### Database

- **Slow queries**: Missing indexes, full table scans, N+1 queries
- **Connection pool exhaustion**: Too few connections, too many concurrent requests
- **Lock contention**: Row-level locks causing request queuing
- **Fix**: Add indexes, optimize queries, use connection pooling, read replicas

### Application

- **CPU-bound code**: Inefficient algorithms, synchronous processing of heavy work
- **Memory leaks**: Growing heap, unreleased resources
- **Blocking I/O**: Synchronous HTTP calls in async frameworks
- **Fix**: Profile with flame graphs, optimize hot paths, use async I/O, add caching

### Network

- **Large payloads**: Sending too much data per response
- **No compression**: Missing gzip/brotli on responses
- **DNS resolution**: Repeated DNS lookups instead of connection pooling
- **Fix**: Paginate responses, enable compression, use persistent connections

### Infrastructure

- **Underprovisioned resources**: Not enough CPU/memory for the load
- **Single points of failure**: One server handling all traffic
- **No autoscaling**: Fixed capacity with variable load
- **Fix**: Right-size resources, horizontal scaling, autoscaling policies, CDN

---

## Performance Testing in CI/CD

### When to Run

| Test Type | When | Duration |
|-----------|------|----------|
| Smoke (5 VUs, 30s) | Every PR | 30 seconds |
| Load (expected traffic) | Nightly / pre-release | 10-30 minutes |
| Stress (2-3x traffic) | Weekly / pre-release | 15-30 minutes |
| Soak (sustained load) | Weekly | 4-24 hours |

### CI Integration with k6

```yaml
# GitHub Actions example
- name: Run load tests
  run: |
    k6 run --out json=results.json loadtest.js
  env:
    K6_CLOUD_TOKEN: ${{ secrets.K6_TOKEN }}

- name: Check thresholds
  run: |
    if [ $? -ne 0 ]; then
      echo "Performance test failed - thresholds not met"
      exit 1
    fi
```

### Baseline Comparison

Store results from each run and compare against the previous baseline:
1. Track p95 response time per endpoint over time.
2. Alert if any endpoint degrades by more than 20% from baseline.
3. Update baselines after intentional architecture changes.

---

## Checklist

Before running performance tests:
- [ ] Performance budgets are defined
- [ ] Test environment mirrors production (or is proportionally scaled)
- [ ] Test data is realistic (volume and distribution)
- [ ] Monitoring is set up (APM, logs, metrics)
- [ ] External dependencies are accounted for (mocked or real)

After running:
- [ ] Results are documented with test parameters
- [ ] Bottlenecks are identified and triaged
- [ ] Critical issues are filed as bugs
- [ ] Baseline metrics are updated
- [ ] Results are shared with the team

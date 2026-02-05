# Observability Guide

This reference covers the three pillars of observability, standard methodologies for monitoring services and infrastructure, structured logging, distributed tracing, and guidance on choosing tools.

---

## The Three Pillars of Observability

Observability is the ability to understand the internal state of a system by examining its external outputs. The three pillars are complementary — you need all three for full observability.

| Pillar | Purpose | Answers |
|--------|---------|---------|
| **Metrics** | Quantitative measurements over time | "What is happening?" |
| **Logs** | Discrete, immutable event records | "Why is it happening?" |
| **Traces** | Request lifecycle across services | "Where is it happening?" |

### When to use each

- **Metrics** for dashboards, alerting, and trend analysis. They are cheap to store and fast to query. Start here for all monitoring.
- **Logs** for debugging specific issues. They provide context that metrics cannot. Use structured logging to make them queryable.
- **Traces** for understanding latency and failures in distributed systems. Essential when a request touches more than one service.

---

## The RED Method (for Services)

The RED method focuses on monitoring **request-driven services** (APIs, web servers, microservices). For every service, track:

### Rate
- **What:** Requests per second (throughput).
- **Why:** Establishes baseline load. Sudden changes indicate traffic anomalies.
- **Metric:** `http_requests_total` (counter, use `rate()` in Prometheus).

### Errors
- **What:** Failed requests per second (or error percentage).
- **Why:** Directly measures user-facing reliability.
- **Metric:** `http_requests_total{code=~"5.."}` or a dedicated error counter.
- **Tip:** Track both server errors (5xx) and client errors (4xx) separately. A spike in 4xx may indicate a broken client or API contract change.

### Duration
- **What:** Response time distribution (latency).
- **Why:** Latency affects user experience even when there are zero errors.
- **Metric:** `http_request_duration_seconds` (histogram).
- **Tip:** Always track percentiles (p50, p95, p99), not averages. Averages hide tail latency that affects your worst-off users.

### RED Dashboard Layout
```
[ Request Rate (req/s) ] [ Error Rate (%) ] [ Latency p50/p95/p99 ]
```

---

## The USE Method (for Resources)

The USE method focuses on monitoring **infrastructure resources** (CPU, memory, disk, network, connections). For every resource, track:

### Utilization
- **What:** Percentage of the resource being used (over a time interval).
- **Examples:** CPU utilization, memory usage, disk space used, connection pool fill percentage.
- **Threshold:** Alert at 85% (warning) and 95% (critical) to catch exhaustion before it happens.

### Saturation
- **What:** The degree to which the resource has extra work it cannot service (queue depth).
- **Examples:** CPU run queue length, disk I/O queue, network interface packet drops, thread pool queue.
- **Why:** Saturation often appears before utilization hits 100% and is a leading indicator of performance degradation.

### Errors
- **What:** Error events on the resource.
- **Examples:** Disk read/write errors, network packet errors, ECC memory corrections, OOM kills.
- **Why:** Even low utilization can be a problem if error rates are high.

### USE Dashboard Layout
```
[ CPU Util (%) | CPU Saturation (queue) ] [ Memory Util (%) | OOM Events ]
[ Disk Util (%) | Disk I/O Queue ]        [ Network Util (%) | Packet Drops ]
```

---

## Structured Logging Best Practices

Unstructured logs (`printf`-style) are hard to parse, search, and aggregate. Structured logs (JSON) are machine-readable and enable powerful querying.

### Format

Always log in JSON format:

```json
{
  "timestamp": "2026-01-15T10:23:45.123Z",
  "level": "ERROR",
  "service": "payment-api",
  "version": "1.4.2",
  "trace_id": "abc123def456",
  "span_id": "789ghi",
  "request_id": "req-a1b2c3",
  "method": "POST",
  "path": "/api/v1/charge",
  "status_code": 500,
  "duration_ms": 342,
  "user_id": "usr-12345",
  "error": "connection refused",
  "message": "Failed to process payment: upstream timeout"
}
```

### Log Levels Guide

| Level | When to use | Examples |
|-------|-------------|---------|
| **ERROR** | Something failed and needs attention. A user-facing operation did not complete. | Unhandled exception, database connection failure, external API 5xx. |
| **WARN** | Something unexpected happened but the operation completed (possibly degraded). | Retry succeeded after failure, cache miss fallback, deprecated API called. |
| **INFO** | Normal operational events worth recording. | Request completed, user logged in, deployment started, config loaded. |
| **DEBUG** | Detailed diagnostic info for development and troubleshooting. Disabled in production by default. | SQL queries, cache hit/miss details, parsed request bodies. |

### Rules of Thumb

1. **Never log secrets.** No passwords, tokens, API keys, PII, or credit card numbers. Use allowlists, not blocklists.
2. **Always include a correlation ID.** Every log line for a request should share a `trace_id` or `request_id` so you can reconstruct the full journey.
3. **Log at the boundary.** Log when a request enters and exits your service. Log when you call an external dependency.
4. **Keep messages human-readable.** The `message` field should make sense to someone reading it without looking at other fields.
5. **Include context, not noise.** Log the user ID, request method, path, and status code. Do not log every loop iteration.

---

## Distributed Tracing

### Concepts

- **Trace:** The complete journey of a request through all services. Identified by a unique `trace_id`.
- **Span:** A single unit of work within a trace (e.g., one HTTP call, one database query). Each span has a `span_id` and a `parent_span_id`.
- **Context Propagation:** Passing the `trace_id` and `span_id` between services, typically via HTTP headers (`traceparent`, `X-Request-ID`).

### How It Works

```
Client -> API Gateway -> Auth Service -> Payment Service -> Database
  |           |              |                |                |
  |-- Span 1 -|-- Span 2 ---|--- Span 3 -----|--- Span 4 ----|
  |<======================== Trace ============================|
```

Each service:
1. Reads the incoming trace context from the request headers.
2. Creates a child span with its own `span_id`.
3. Propagates the context to any outgoing requests.
4. Reports the span to the tracing backend when finished.

### Setup Checklist

1. **Choose a tracing backend:** Jaeger, Zipkin, Tempo (Grafana), Datadog APM, AWS X-Ray.
2. **Instrument your code:** Use OpenTelemetry SDKs (the industry standard). Most frameworks have auto-instrumentation.
3. **Propagate context:** Use W3C `traceparent` header format. Ensure all inter-service calls propagate the header.
4. **Configure sampling:** For high-traffic services, trace 1-10% of requests (head-based sampling) or use tail-based sampling to capture only slow/error traces.
5. **Correlate with logs:** Include `trace_id` in every log line so you can jump from a log entry to the full trace.

### Sampling Strategies

| Strategy | Pros | Cons |
|----------|------|------|
| **Head-based** (decide at start) | Simple, low overhead | May miss interesting traces |
| **Tail-based** (decide at end) | Captures all errors/slow requests | More complex, higher resource usage |
| **Adaptive** (adjust rate dynamically) | Balances cost and coverage | Most complex to configure |

**Recommendation:** Start with head-based sampling at 10%. Add tail-based sampling for errors and latency outliers as your tracing infrastructure matures.

---

## Correlation IDs

A correlation ID ties together all the logs, metrics, and traces for a single user request. Without it, debugging distributed systems is nearly impossible.

### Implementation

1. At the entry point (API gateway or load balancer), generate a unique ID if one is not present in the incoming request.
2. Pass it through all internal service calls as an HTTP header (e.g., `X-Request-ID` or `traceparent`).
3. Include it in every log line, metric label (sparingly), and trace span.
4. Return it to the client in the response headers so users can reference it in support tickets.

### Example Header Flow

```
Client -> API Gateway                   : (no header)
API Gateway -> Auth Service             : X-Request-ID: req-a1b2c3
Auth Service -> Payment Service         : X-Request-ID: req-a1b2c3
Payment Service -> Database             : X-Request-ID: req-a1b2c3
API Gateway -> Client (response header) : X-Request-ID: req-a1b2c3
```

---

## Choosing an Observability Stack

### Open Source (Self-Hosted)

| Component | Tool | Notes |
|-----------|------|-------|
| Metrics | **Prometheus** + **Grafana** | Industry standard. PromQL is powerful. Use Thanos or Cortex for long-term storage. |
| Logs | **Loki** (Grafana) or **ELK** (Elasticsearch + Logstash + Kibana) | Loki is simpler and cheaper (indexes labels only). ELK is more powerful but resource-hungry. |
| Traces | **Tempo** (Grafana) or **Jaeger** | Tempo integrates well with Grafana. Jaeger is mature and battle-tested. |

**Pros:** No vendor lock-in, full control, free software.
**Cons:** Operational burden (you run the infrastructure), scaling requires expertise.

### Managed / SaaS

| Tool | Strengths | Best For |
|------|-----------|----------|
| **Datadog** | All-in-one (metrics, logs, traces, APM, RUM). Excellent UX. | Teams that want a single pane of glass and can afford it. |
| **AWS CloudWatch** | Deep AWS integration. X-Ray for traces. | AWS-native workloads. |
| **Google Cloud Operations** (formerly Stackdriver) | GCP integration. Good Kubernetes support. | GCP-native workloads. |
| **New Relic** | Strong APM. Generous free tier. | Application performance focus. |
| **Grafana Cloud** | Managed Prometheus, Loki, Tempo. | Teams that like open-source tools but want managed hosting. |

### Decision Framework

1. **Small team / startup:** Start with Grafana Cloud free tier or Datadog free tier. Avoid operational overhead of self-hosting.
2. **Mid-size, cloud-native:** Use your cloud provider's tools (CloudWatch, GCP Operations) for infrastructure. Add Datadog or Grafana Cloud for application-level observability.
3. **Large / multi-cloud:** Self-host Prometheus + Grafana + Loki + Tempo with Thanos for federation. Or use Datadog/Grafana Cloud for a unified view.
4. **Regulated industry:** Self-host if data residency is a concern. Otherwise, ensure your SaaS vendor meets your compliance requirements.

---

## Quick Reference: What to Monitor First

If you are starting from zero, implement monitoring in this order:

1. **Health check endpoint** — A `/health` or `/ready` endpoint that returns 200 when the service is operational. Monitor it externally (uptime check).
2. **Error rate** — Percentage of 5xx responses. This is the single most important metric.
3. **Latency percentiles** — p50, p95, p99 response times. Catch tail latency before users complain.
4. **Resource utilization** — CPU, memory, disk for each host/container. Prevent outages from resource exhaustion.
5. **Structured logging** — Switch from unstructured to JSON logs. Add correlation IDs.
6. **Alerting** — Set up alerts for error rate and latency based on SLOs (use `alert_generator.py`).
7. **Dashboards** — Build a service overview dashboard with RED metrics.
8. **Distributed tracing** — Add OpenTelemetry instrumentation and a tracing backend.

Do not try to do everything at once. Each step above provides value on its own.

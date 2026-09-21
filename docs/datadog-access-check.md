# Datadog MCP Access Check

**Date:** 2026-09-21  
**Asana task:** test  
**Result:** Datadog MCP access is working.

## Summary

The Datadog MCP integration is authenticated and can read data from the Asana Datadog organization (`app.datadoghq.com`). Multiple product areas were queried successfully: service catalog, events, hosts, incidents, dashboards, and monitors.

## What Was Accessible

### Service catalog

- Queried the entity graph for services (`search_datadog_entities`).
- Returned at least 10 services (page truncated), including: `agent`, `airpedal-cell`, `airpedal-go`, `api`, `alerter`, and others.
- Infrastructure appears to be organized around Asana cell-based production (`prod-us1`, `prod-eu1`, etc.).

### Recent events (last 24h)

- Queried with `search_datadog_events` (`query: *`).
- **20,336,403** matching events in the last 24 hours.
- Recent activity includes:
  - Kubernetes deployment updates (e.g. Kyverno, Istio ingress gateway sync server)
  - Pod readiness probe failures (webservers in `asana-cell12`)
  - Container lifecycle events (search-infra-ops cron jobs)
  - CronJob updates across multiple cells and regions

### Host inventory

- Queried with `search_datadog_hosts`.
- Sample hosts are AWS EC2 instances running GNU/Linux in EKS cell clusters.
- Instance types include `m8g.8xlarge`, `r8g.2xlarge`, `c8g.8xlarge`, etc.
- Clusters span prod, canary, and CI environments across `us-east-1`, `us-west-2`, and other regions.

### Incidents

- Queried with `search_datadog_incidents` (`state:(active OR stable)`).
- **4** matching incidents:

| ID  | Title | Severity | State |
|-----|-------|----------|-------|
| 434 | PyPI Download Issues Affecting All Builds Intermittently | SEV-2 | stable |
| 418 | lunadb beta perf regression | SEV-3 | active |
| 301 | Cannot update Experiment flag's launch status | SEV-1 | active |
| 223 | Jamie is testing | SEV-3 | active |

### Dashboards

- Queried with `search_datadog_dashboards` (sorted by `-modified_at`).
- Returned 73+ dashboards (response truncated), including:
  - `[ASANA_DEV] GitHub Integration`
  - `[ASANA_DEV] Coding Agent - Integration Platform`
  - `Webservers`, `LunaServer Heap OOM`, `Cell Costs Overview`
  - `AI Orchestration`, `Remote Jobs`, `Kafka CDC Pipeline`
  - Cost and CI/CD dashboards

### Monitors (currently alerting)

- Queried with `search_datadog_monitors` (`status:alert`).
- Returned 13+ alerting monitors (response truncated), including:
  - **Datadog cost forecast over $475k** (cost alert)
  - **[Webservers][Composite Component] low sync traffic** (App Down component)
  - **[All Prod] Core Action Search Result Load & Render - P95 Over Threshold**
  - **[Gmail] Email Sync Webhook Processing - High latency**
  - Budget and synthetics alerts

## Tools Verified

| Tool | Status |
|------|--------|
| `search_datadog_entities` | OK |
| `search_datadog_events` | OK |
| `search_datadog_hosts` | OK |
| `search_datadog_incidents` | OK |
| `search_datadog_dashboards` | OK |
| `search_datadog_monitors` | OK |
| `load_datadog_skill` | OK |

## Conclusion

Datadog MCP access is fully functional for read operations across core observability surfaces. The connected org appears to be Asana's production observability environment with extensive Kubernetes/cell-based infrastructure monitoring, active incidents, and a large catalog of dashboards and monitors.

# Datadog Access Check

**Date:** 2026-09-21  
**Asana task:** test  
**Result:** Datadog MCP access is working.

## Summary

The Datadog MCP integration is authenticated and can read logs, metrics, service entities, monitors, dashboards, and host inventory from the connected Datadog organization.

## What was checked

| Area | Access | Notes |
|------|--------|-------|
| Logs | Yes | 4,705 log entries in the last hour |
| Metrics | Yes | 225+ metrics matching `system.cpu*` |
| Service entities | Yes | Service catalog lookup works |
| Monitors | Yes | Alerting monitors are visible |
| Dashboards | Yes | 48+ dashboards returned (truncated) |
| Host inventory | Yes | 4,434 AWS EC2 hosts |
| Incidents | Yes | 0 active incidents in the last 7 days |

## Sample observations

### Logs (last 1 hour)

- Most recent activity is from the `remote-jobs` service.
- Environments seen: `prod`, `beta`, and `canary`.
- Example message: `Remote Jobs Db Metrics Aggregated`.
- No error log patterns were found in the last hour (`status:error`).

### Service entity

- **Service:** Remote Jobs (`remote-jobs`)
- **Owner:** api-lsi

### Host inventory

- **Cloud provider:** AWS
- **Resource type:** `aws_ec2_instance`
- **Host count:** 4,434

### Monitors currently in Alert (sample)

- Datadog cost forecast over $475k
- Database underutilization alerts
- Gmail email sync webhook high latency
- Core Action Search Result Load & Render P95 threshold
- Budget monitor: FY27 - GitHub
- Webservers low sync traffic (App Down component)

### Dashboards (recent sample)

- Metronome API Monitoring
- Remote Jobs
- AI Orchestration
- Webservers
- Event System
- Remote Job Scheduling Investigation

## Conclusion

Datadog access from this coding agent session is fully functional. The connected account appears to be Asana's production Datadog organization with broad read access across core observability surfaces.

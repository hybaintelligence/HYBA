# Incident Response Template

This template serves as a starting point for documenting specific incidents and ensuring a structured response. Copy this file and fill in the details for each real incident.

## Summary

- **Incident ID**: [unique ID or timestamp]
- **Date/Time detected**: 
- **Detected by**: [monitoring alert / user report / other]
- **Service affected**:
- **Impact severity**: [minor, major, critical]

## Description

Provide a high-level description of what happened, including symptoms observed (e.g., API latency spikes, mining pool disconnection) and how the issue was confirmed.

## Timeline

| Time (UTC) | Event |
|------------|-------|
| T0 | Incident detected via monitoring alert |
| ... | ... |

## Investigation

Outline the investigative steps taken. Include logs examined, metrics analysed, commands run, and any hypotheses tested.

## Mitigation & Resolution

Describe the actions taken to mitigate the issue and restore service (e.g., restarting services, switching to a backup pool, scaling resources). Note whether the issue was fully resolved or a workaround is in place.

## Root Cause Analysis (RCA)

Summarise the underlying cause of the incident once identified. If the root cause is still unknown, note next steps for deeper analysis.

## Lessons Learned

List any lessons or improvements resulting from this incident, such as:

- Improvements to monitoring or alert thresholds.
- Updates to runbooks or documentation.
- Code or infrastructure changes to prevent recurrence.

## Follow-Up Actions

- [ ] Action item 1 (owner / due date)
- [ ] Action item 2 (owner / due date)

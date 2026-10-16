# Privacy

- Memory storage is the default and is cleared on process restart.
- Persistent storage must be explicitly enabled by the operator.
- Do not log raw email addresses, phone numbers, API keys or full investigation payloads by default.
- Document what data is collected, why, where it is stored and how to delete it.
- The delete endpoint must remove stored investigation data.
- Production deployments must define retention, access control, backup deletion and incident response.
- Operators are responsible for lawful basis and appropriate notice/consent where required.

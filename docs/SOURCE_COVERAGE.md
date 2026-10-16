# Source Coverage Matrix

The implementation agent must maintain this matrix as modules are implemented and tested. Do not mark a source as supported merely because it is planned.

| Module ID | Source | Access type | Status | Automated tests | Limitations |
|---|---|---|---|---|---|
| username.github | GitHub public profile | Public web URL / official API if configured | planned until implemented | required | A profile match is not identity proof |
| username.gitlab | GitLab public profile | Public web URL / official API if configured | planned until implemented | required | Rate limiting and soft-404 behavior |
| email.syntax | Local parser | Local computation | planned until implemented | required | No mailbox existence claim |
| email.dns_mx | DNS MX lookup | Public DNS | planned until implemented | required | MX is not mailbox verification |
| phone.numbering | libphonenumber metadata | Local library | planned until implemented | required | No owner identity or live status |

For every implemented module, record last tested version/date and any known source behavior changes. No unsupported count or coverage percentage may be advertised.

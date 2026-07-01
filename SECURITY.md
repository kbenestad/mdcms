# Security Policy

## Supported versions

Only the latest release of mdcms receives security fixes.

| Version | Supported |
|---------|-----------|
| Latest  | Yes       |
| Older   | No        |

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report them privately via [GitHub's private vulnerability reporting](https://github.com/kbenestad/mdcms/security/advisories/new), or email **kristian@benestad.net** if you prefer.

Include:
- A description of the vulnerability
- Steps to reproduce it
- The version of mdcms affected
- Any suggested fix, if you have one

You can expect an acknowledgement within a few days and a fix or response within 30 days depending on severity.

## Scope

mdcms is a local CLI tool and static site renderer. It does not run a server or handle untrusted network input in normal use. The main areas of concern are:

- **Template download** (`mdcms register`) — fetches files from GitHub over HTTPS using `certifi` for SSL verification.
- **YAML parsing** — uses `yaml.safe_load()` throughout; `yaml.load()` with an untrusted loader is never used.
- **File path handling** — paths are resolved relative to a user-supplied site directory; symlink traversal or path escape bugs would be in scope.

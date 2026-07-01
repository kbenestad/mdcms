---
title: Authentication
sort: 110
section-id: configuration
keywords: authentication, API keys, mTLS, RBAC, SSO, pg_hba, security
description: Configuring NeuralDB authentication — API keys, mTLS, role-based access control, and SSO
language: en
---

# Authentication

NeuralDB supports multiple authentication methods, from simple password auth to mutual TLS and enterprise SSO. This page explains how to configure each.

## Host-Based Authentication (pg_hba.conf)

The `pg_hba.conf` file controls which clients can connect and how they must authenticate. It is evaluated top-to-bottom and the first matching rule applies.

```
# pg_hba.conf
# FORMAT: TYPE  DATABASE  USER  ADDRESS  METHOD

# Local Unix socket connections (no password needed for postgres superuser)
local   all     neuraldb               trust
local   all     all                    md5

# IPv4 connections from local network
host    all     all     127.0.0.1/32   scram-sha-256
host    all     all     10.0.0.0/8     scram-sha-256

# Reject all other connections
host    all     all     0.0.0.0/0      reject
```

Reload after changes:

```sql
SELECT pg_reload_conf();
```

## Authentication Methods

| Method | Security | Use case |
|--------|---------|---------|
| `trust` | None | Local socket, trusted environments |
| `md5` | Weak | Legacy compatibility |
| `scram-sha-256` | Strong (default) | Standard password auth |
| `cert` | Very strong | Mutual TLS authentication |
| `ldap` | Strong | Enterprise LDAP/AD integration |
| `radius` | Strong | RADIUS server |
| `gss` | Strong | Kerberos |
| `jwt` | Strong | Token-based auth |

### Enabling scram-sha-256

```ini
# neuraldb.conf
password_encryption = scram-sha-256
```

Set passwords for users:

```sql
CREATE USER app_user WITH PASSWORD 'secure-random-password';
ALTER USER app_user PASSWORD 'new-secure-password';
```

## Role-Based Access Control (RBAC)

### Creating Roles

```sql
-- Application read-only role
CREATE ROLE app_readonly;
GRANT CONNECT ON DATABASE myapp TO app_readonly;
GRANT USAGE ON SCHEMA public TO app_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO app_readonly;

-- Application read-write role
CREATE ROLE app_readwrite;
GRANT app_readonly TO app_readwrite;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT INSERT, UPDATE, DELETE ON TABLES TO app_readwrite;

-- Vector operations role (needed for ANN searches)
CREATE ROLE vector_user;
GRANT USAGE ON SCHEMA public TO vector_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO vector_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO vector_user;

-- Application user
CREATE USER my_app WITH PASSWORD 'app-password';
GRANT app_readwrite TO my_app;
GRANT vector_user TO my_app;
```

### Row-Level Security (RLS)

For multi-tenant applications, use Row-Level Security to enforce tenant isolation at the database level:

```sql
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Tenants can only see their own documents
CREATE POLICY tenant_isolation ON documents
  USING (tenant_id = current_setting('app.tenant_id')::UUID);

-- Admin can see everything
CREATE POLICY admin_access ON documents
  TO admin_role
  USING (true);
```

In your application, set the tenant context before querying:

```python
with connection.cursor() as cursor:
    cursor.execute("SET app.tenant_id = %s", [tenant_id])
    cursor.execute("SELECT * FROM documents ORDER BY embedding <=> %s LIMIT 10", [embedding])
```

## API Key Authentication

NeuralDB supports an API key table for token-based authentication — useful for microservices and CI pipelines that cannot use password auth:

```sql
-- Enable the API key extension
CREATE EXTENSION neuraldb_apikeys;

-- Create an API key for a service account
SELECT neuraldb_apikeys.create_key(
  label => 'my-service',
  role  => 'app_readwrite'
);
-- Returns: ndb_live_abcdefghij123456...
```

Clients authenticate by passing the key in the connection string:

```
postgresql://apikey:ndb_live_abc123@host:5432/mydb
```

Revoke a key:

```sql
SELECT neuraldb_apikeys.revoke_key('ndb_live_abc123');
```

## Mutual TLS (mTLS)

For the highest security, require clients to present a certificate signed by your CA.

### 1. Generate a CA

```bash
# Generate CA key and certificate
openssl genrsa -out ca.key 4096
openssl req -new -x509 -key ca.key -out ca.crt -days 3650 \
  -subj "/CN=NeuralDB CA/O=My Org"
```

### 2. Issue a Server Certificate

```bash
openssl genrsa -out server.key 2048
openssl req -new -key server.key -out server.csr \
  -subj "/CN=neuraldb.example.com"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out server.crt -days 365
```

### 3. Configure NeuralDB

```ini
# neuraldb.conf
ssl = on
ssl_cert_file = '/etc/neuraldb/ssl/server.crt'
ssl_key_file = '/etc/neuraldb/ssl/server.key'
ssl_ca_file = '/etc/neuraldb/ssl/ca.crt'
ssl_crl_file = '/etc/neuraldb/ssl/crl.pem'  # optional certificate revocation list
```

### 4. Require Client Certificates

```
# pg_hba.conf
hostssl  all  all  0.0.0.0/0  cert  clientcert=verify-full
```

## LDAP / Active Directory

```
# pg_hba.conf
host  all  all  0.0.0.0/0  ldap  \
  ldapserver=ldap.example.com  \
  ldapport=636  \
  ldaptls=1  \
  ldapbasedn="dc=example,dc=com"  \
  ldapbinddn="cn=neuraldb,dc=example,dc=com"  \
  ldapbindpasswd=bindpassword  \
  ldapsearchfilter="(sAMAccountName=%s)"
```

## Auditing

Enable connection and statement auditing:

```sql
CREATE EXTENSION pgaudit;
```

```ini
# neuraldb.conf
pgaudit.log = 'ddl, write, role'
pgaudit.log_catalog = on
pgaudit.log_client = on
pgaudit.log_level = log
```

Audit logs are written to the standard NeuralDB log file in a structured format, suitable for ingestion by SIEM systems.

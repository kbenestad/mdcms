---
title: Local Development
sort: 130
section-id: installation
keywords: local, development, binary, homebrew, winget, install, macOS, Linux, Windows
description: Installing NeuralDB locally for development using binaries, Homebrew, or winget
language: en
---

# Local Development

For local development, you can run NeuralDB as a native binary without Docker. This provides lower latency for development workflows and avoids container overhead.

## System Requirements

| Platform | Minimum | Recommended |
|----------|---------|-------------|
| macOS | 13.0 (Ventura) | 14.x+ |
| Linux | Ubuntu 22.04 / RHEL 9 | Ubuntu 24.04 |
| Windows | Windows 10 22H2 | Windows 11 |
| CPU | x86-64 or ARM64 | ARM64 (Apple Silicon) |
| RAM | 4 GB | 16 GB+ |
| Disk | 2 GB free | SSD recommended |

## macOS

### Homebrew (Recommended)

```bash
brew tap neuraldb/tap
brew install neuraldb

# Start as a service (auto-restart on login)
brew services start neuraldb

# Or start manually (foreground)
neuraldb start

# Check status
neuraldb status
```

The Homebrew formula installs:
- `neuraldb` — the server binary
- `neuraldb-cli` — an enhanced SQL shell (psql-compatible)
- Configuration at `$(brew --prefix)/etc/neuraldb/neuraldb.conf`
- Data directory at `$(brew --prefix)/var/neuraldb`

### Direct Binary

```bash
# Apple Silicon (M1/M2/M3/M4)
curl -LO https://releases.neuraldb.io/1.0/neuraldb-macos-arm64.tar.gz
tar -xzf neuraldb-macos-arm64.tar.gz
sudo mv neuraldb /usr/local/bin/
sudo mv neuraldb-cli /usr/local/bin/

# Intel Mac
curl -LO https://releases.neuraldb.io/1.0/neuraldb-macos-amd64.tar.gz
tar -xzf neuraldb-macos-amd64.tar.gz
sudo mv neuraldb /usr/local/bin/
sudo mv neuraldb-cli /usr/local/bin/
```

## Linux

### Ubuntu / Debian

```bash
# Add the NeuralDB APT repository
curl -fsSL https://packages.neuraldb.io/gpg | sudo gpg --dearmor -o /usr/share/keyrings/neuraldb-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/neuraldb-keyring.gpg] https://packages.neuraldb.io/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/neuraldb.list

sudo apt update
sudo apt install -y neuraldb

# Start and enable the service
sudo systemctl enable --now neuraldb
```

### RHEL / Fedora / CentOS

```bash
# Add the NeuralDB YUM repository
sudo rpm --import https://packages.neuraldb.io/gpg
sudo tee /etc/yum.repos.d/neuraldb.repo <<'EOF'
[neuraldb]
name=NeuralDB Repository
baseurl=https://packages.neuraldb.io/rpm/stable
enabled=1
gpgcheck=1
gpgkey=https://packages.neuraldb.io/gpg
EOF

sudo dnf install -y neuraldb
sudo systemctl enable --now neuraldb
```

### Direct Binary (Linux)

```bash
# x86-64
curl -LO https://releases.neuraldb.io/1.0/neuraldb-linux-amd64.tar.gz
tar -xzf neuraldb-linux-amd64.tar.gz
sudo mv neuraldb neuraldb-cli /usr/local/bin/
```

## Windows

### winget

```powershell
winget install NeuralDB.NeuralDB
```

This installs NeuralDB and registers it as a Windows Service. It starts automatically after installation.

### Chocolatey

```powershell
choco install neuraldb
```

### MSI Installer

Download the MSI installer from [neuraldb.io/download](https://neuraldb.io/download) and run it. The installer:
1. Installs `neuraldb.exe` and `neuraldb-cli.exe` to `C:\Program Files\NeuralDB\`
2. Adds them to `PATH`
3. Creates a `NeuralDB` Windows Service
4. Initialises the data directory at `%APPDATA%\NeuralDB\data`

## First-Time Setup

After installation, initialise the database:

```bash
# Linux / macOS
neuraldb init
neuraldb start

# Connect
neuraldb-cli
# psql prompt: neuraldb=#
```

### Change the Default Password

```sql
ALTER USER neuraldb PASSWORD 'your-new-password';
```

### Create a Development Database

```sql
CREATE DATABASE myapp;
\c myapp

CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content TEXT,
  embedding VECTOR(1536)
);

CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
```

## Configuration

The default configuration file locations:

| Platform | Path |
|----------|------|
| macOS (Homebrew) | `$(brew --prefix)/etc/neuraldb/neuraldb.conf` |
| Linux | `/etc/neuraldb/neuraldb.conf` |
| Windows | `%PROGRAMDATA%\NeuralDB\neuraldb.conf` |

For local development, create a `neuraldb.conf` in your project directory and point to it:

```bash
neuraldb start --config ./neuraldb.conf
```

Useful development settings:

```ini
# neuraldb.conf (development)
listen_addresses = 'localhost'
port = 5432
max_connections = 50
shared_buffers = 256MB
vector_buffer = 1GB
log_min_duration_statement = 100   # log slow queries (>100ms)
log_statement = 'all'              # log all SQL (useful for debugging)
```

## Uninstalling

```bash
# macOS
brew services stop neuraldb
brew uninstall neuraldb

# Ubuntu
sudo systemctl stop neuraldb
sudo apt remove neuraldb

# Windows
winget uninstall NeuralDB.NeuralDB
# Or: Settings → Apps → Installed Apps → NeuralDB → Uninstall
```

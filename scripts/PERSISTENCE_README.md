# OpenClaw Persistence Storage Configuration Guide

## Overview

This configuration is implemented OpenClaw exist Hugging Face Space in**Complete persistent storage**, to ensure that all states can be restored after the container is restarted.

### Core features

- **Full directory backup**: persist the entire `~/.openclaw` Table of contents
- **Atomic operations**: use tar.gz Archiving ensures backup consistency
- **automatic rotation**: keep recent 5 backups and automatically clean up old backups
- **graceful closing**: Automatically perform final backup when container is stopped

---

## Persistent directories and files

### 1. Core configuration
```
~/.openclaw/
├── openclaw.json              # Main configuration file (models, plugins, gateway settings)
└── credentials/               # Login credentials for all channels
    ├── whatsapp/
    │   └── default/
    │       └── auth_info_multi.json
    └── telegram/
        └── session.data
```

### 2. workspace
```
~/.openclaw/workspace/
├── AGENTS.md                 # agent definition
├── SOUL.md                   # Soul (personality, speaking style)
├── TOOLS.md                  # List of available tools
├── MEMORY.md                 # long term aggregated memory
├── memory/                   # daily memory file
│   ├── 2025-01-15.md
│   └── 2025-01-16.md
└── skills/                   # Skill definition
    ├── my-skill/
    │   └── SKILL.md
    └── ...
```

### 3. session history
```
~/.openclaw/agents/<agentId>/sessions/
├── <sessionId>.jsonl          # Complete conversation history for every conversation
└── sessions.json             # session index
```

### 4. memory index (SQLite)
```
~/.openclaw/memory/
└── <agentId>.sqlite          # Semantic search index
```

### 5. QMD backend (if enabled)
```
~/.openclaw/agents/<agentId>/qmd/
├── xdg-config/              # QMD Configuration
├── xdg-cache/               # QMD cache
└── sessions/                # QMD Session export
```

---

## Excluded files/Table of contents

The following content**Won't**Persisted (temporary files, cache, lock files):

- `*.lock` - lock file
- `*.tmp` - temporary files
- `*.socket` - Unix socket document
- `*.pid` - PID document
- `node_modules/` - Node rely
- `.cache/` - cache directory
- `logs/` - Log directory

---

## Environment variable configuration

exist Hugging Face Space of Settings > Variables Medium settings:

| variable name | required | default value | illustrate |
|--------|------|--------|------|
| `HF_TOKEN` | ✅ | - | Hugging Face Access token (requires write permission) |
| `OPENCLAW_DATASET_REPO` | ✅ | - | Dataset Warehouse ID,like `username/openclaw-state` |
| `OPENCLAW_HOME` | ❌ | `~/.openclaw` | OpenClaw Home directory |
| `SYNC_INTERVAL` | ❌ | `300` | Automatic backup interval (seconds) |
| `ENABLE_AUX_SERVICES` | ❌ | `false` | Whether to enable auxiliary services (WA Guardian, QR Manager) |

### Quick configuration steps

1. **Create a dataset warehouse**
   ```
   exist Hugging Face Create a new one on Dataset Warehouse, for example:username/openclaw-state
   set to Private(private)
   ```

2. **Get access token**
   ```
   access:https://huggingface.co/settings/tokens
   create new Token, check "Write" Permissions
   ```

3. **Configuration Space variable**
   ```
   HF_TOKEN = hf_xxxxx...(your Token)
   OPENCLAW_DATASET_REPO = username/openclaw-state(Your dataset ID)
   ```

---

## Script description

### openclaw_persist.py

The core persistence module provides backup and recovery functions.

```bash
# Back up current state
python3 openclaw_persist.py save

# restore state
python3 openclaw_persist.py load

# View status
python3 openclaw_persist.py status
```

### openclaw_sync.py

Primary sync manager, is entrypoint.sh call.

Function:
1. Restore state from data set on startup
2. start up OpenClaw gateway
3. Regular background backup
4. Execute final backup upon graceful shutdown

---

## Backup file naming

File naming format in backup data set:

```
backup-YYYYMMDD_HHMMSS.tar.gz
```

For example:`backup-20250116_143022.tar.gz`

The system will automatically keep the most recent 5 backups, deleting older ones.

---

## troubleshooting

### Backup failed

1. examine `HF_TOKEN` Do you have write permission?
2. examine `OPENCLAW_DATASET_REPO` Is it correct?
3. Check the error message in the log

### Recovery failed

1. It's normal for the dataset to be empty (first run)
2. Check network connection
3. Try manual recovery:`python3 openclaw_persist.py load`

### WhatsApp Lost credentials

Backup contains WhatsApp credentials, it should be able to connect automatically after restoration. If you need to scan the code again:

1. Log in Hugging Face Space
2. Find the QR code in the log
3. use mobile phone WhatsApp Scan code to log in

---

## Yohara sync_hf.py The difference

| characteristic | sync_hf.py | openclaw_sync.py |
|------|------------|------------------|
| sync mode | Folder-by-folder synchronization | Complete catalog tar Archive |
| Configuration complexity | High (requires mapping path) | Low (automatic processing) |
| atomicity | no | yes |
| rollback capability | none | Yes (reserved 5 backup) |
| file integrity | part | whole |

---

## Manual backup/restore command

### local test

```bash
# Set environment variables
export HF_TOKEN="hf_..."
export OPENCLAW_DATASET_REPO="username/openclaw-state"

# Manual backup
cd /home/node/scripts
python3 openclaw_persist.py save

# Manual recovery
python3 openclaw_persist.py load

# View status
python3 openclaw_persist.py status
```

---

## Technical implementation details

### Backup process

1. examine `~/.openclaw` Table of contents
2. create tar.gz Archive (apply exclusion rules)
3. upload to Hugging Face Dataset
4. Rotate backup (keep latest 5 indivual)
5. Update local state file

### recovery process

1. Get the latest backup from the dataset
2. Download to temporary directory
3. If there is a local state, create a local backup first
4. Unzip to `~/.openclaw`
5. Verify file integrity

### Exclusion rules

```python
EXCLUDE_PATTERNS = [
    "*.lock", "*.tmp", "*.pyc", "*__pycache__*",
    "*.socket", "*.pid", "node_modules", ".DS_Store", ".git",
]

SKIP_DIRS = {".cache", "logs", "temp", "tmp"}
```

---

## Change log

- **v8** (2025-01-16): To achieve full directory persistence, use tar Archiving method
- **v7** (Before): use sync_hf.py Folder-by-folder synchronization

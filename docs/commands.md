# px commands

## Global options

| Option | Description |
|--------|-------------|
| `--version` | Show version (`px X.Y.Z`) and exit |
| `--help` | Show help and exit |
| `--install-completion` | Install shell completion |
| `--show-completion` | Show shell completion |

---

## `px login`

Authenticate with username/password and create a reusable API token.

This is the recommended way to configure the CLI for the first time.
It asks for your Proxmox credentials, creates an API token automatically,
and saves it to `~/.proxmox/config`.

### Synopsis

```
px login [--endpoint <url>] [--username <user>]
```

### Options

| Option | Shorthand | Description |
|--------|-----------|-------------|
| `--endpoint` | `-e` | Proxmox endpoint URL |
| `--username` | `-u` | Proxmox username |

### Interactive flow

```
$ px login

  Proxmox endpoint [https://192.168.1.100:8006]:     ← enter or accept default
  Username (e.g. root@pam): root@pam
  Password: [hidden]

  ✓ Authenticated as root@pam
  ✓ Creating API token 'px-cli'... done
  ✓ Configuration saved to ~/.proxmox/config
  ✓ Verifying token... ok

  Ready. Try:
    px vm list
```

The token ID `px-cli` is fixed. If you need to reconfigure, run `px logout` first
or revoke the old token in the Proxmox UI.

---

## `px logout`

Remove your Proxmox configuration from `~/.proxmox/config`.

### Synopsis

```
px logout
```

### Interactive flow

```
$ px logout

  This will remove your Proxmox configuration. Continue? [y/N]: y
  ✓ Configuration removed (backup saved to ~/.proxmox/config.bak)
```

The existing config is backed up as `~/.proxmox/config.bak` before removal.

---

## `px vm`

### `px vm list`

List VMs and containers.

#### Synopsis

```
px vm list [--type vm|container|all]
           [--status running|stopped]
           [--name <pattern>]
           [--pool <name>]
           [--node <name>]
           [--vmid <number>]
           [--output table|json]
           [--color]
```

#### Options

| Option | Shorthand | Description | Default |
|--------|-----------|-------------|---------|
| `--type` | `-t` | Resource type: `vm`, `container`, `all` | `all` |
| `--status` | | Filter by status (`running`, `stopped`) | — |
| `--name` | | Filter by name (supports `*` and `?` wildcards) | — |
| `--pool` | | Filter by pool name | — |
| `--node` | | Filter by node name | — |
| `--vmid` | | Filter by VMID number | — |
| `--output` | `-o` | Output format: `table` or `json` | `table` |
| `--color` | `-c` | Enable colored output | off |

#### Examples

```bash
px vm list
px vm list --status running
px vm list --name "*web*" --color
px vm list --pool production --output json
```

---

### `px vm start`

Start one or more stopped VMs or containers.

#### Synopsis

```
px vm start <vmid>... [--force] [--dry-run] [--wait]
```

#### Options

| Option | Shorthand | Description |
|--------|-----------|-------------|
| `--force` | `-f` | Skip confirmation prompt |
| `--dry-run` | | Show what would be done without executing |
| `--wait` | | Wait for the action to complete before returning |

#### Examples

```bash
px vm start 100
px vm start 101 102 103 --force
px vm start 100 --wait
px vm start 101 --dry-run
```

---

### `px vm stop`

Force power-off one or more running VMs or containers.

#### Synopsis

```
px vm stop <vmid>... [--force] [--dry-run] [--wait]
```

---

### `px vm shutdown`

Gracefully shut down one or more running VMs or containers (ACPI signal).

#### Synopsis

```
px vm shutdown <vmid>... [--force] [--dry-run] [--wait]
```

---

### `px vm reboot`

Reboot one or more running VMs or containers.

#### Synopsis

```
px vm reboot <vmid>... [--force] [--dry-run] [--wait]
```

---

### `px vm suspend`

Suspend/pause one or more running VMs or containers.

#### Synopsis

```
px vm suspend <vmid>... [--force] [--dry-run] [--wait]
```

---

### `px vm resume`

Resume one or more suspended VMs or containers.

#### Synopsis

```
px vm resume <vmid>... [--force] [--dry-run] [--wait]
```

---

### `px vm status`

Show detailed status information for one or more VMs or containers.

#### Synopsis

```
px vm status <vmid>...
```

#### Output

- VMID, Name, Status, Node, Type, Pool, Tags
- CPU: core count and usage percentage
- Memory: used / total with percentage
- Disk: total size
- Uptime: human-readable duration
- Network: bytes in / out
- I/O: bytes read / written

#### Examples

```bash
px vm status 100
px vm status 100 117 120
```

---

### `px vm snapshot`

Manage VM/container snapshots.

#### Commands

| Command | Description |
|---------|-------------|
| `px vm snapshot list <vmid>` | List snapshots for a VM or container |
| `px vm snapshot create <vmid> <name>` | Create a snapshot |
| `px vm snapshot delete <vmid> <name>` | Delete a snapshot |
| `px vm snapshot rollback <vmid> <name>` | Rollback to a snapshot |

#### Options for `create`

| Option | Shorthand | Description |
|--------|-----------|-------------|
| `--description` | `-d` | Snapshot description |
| `--vmstate` | | Include RAM state |
| `--wait` | | Wait for the task to complete |

#### Options for `delete`, `rollback`

| Option | Shorthand | Description |
|--------|-----------|-------------|
| `--force` | `-f` | Skip confirmation |
| `--wait` | | Wait for the task to complete |

#### Examples

```bash
px vm snapshot list 100
px vm snapshot create 100 before-upgrade --vmstate
px vm snapshot delete 100 before-upgrade --force
px vm snapshot rollback 100 before-upgrade --wait
```

---

## `px storage`

Manage storage pools and contents.

### Commands

| Command | Description |
|---------|-------------|
| `px storage list` | List storage pools |
| `px storage content <storage>` | List contents of a storage pool |
| `px storage info <storage>` | Show detailed info about a storage pool |

### `px storage content` options

| Option | Shorthand | Description |
|--------|-----------|-------------|
| `--node` | `-n` | Node name |
| `--type` | `-t` | Content type (iso, vztmpl, backup, rootdir, images) |
| `--output` | `-o` | Output format (table, json) |
| `--color` | `-c` | Enable colored output |

### `px storage info` options

| Option | Shorthand | Description |
|--------|-----------|-------------|
| `--color` | `-c` | Enable colored output |

### Examples

```bash
px storage list
px storage content local
px storage content nfs-storage --type backup --output json
px storage info local-lvm
```

---

## `px backup`

Manage VM/container backups (vzdump).

### Commands

| Command | Description |
|---------|-------------|
| `px backup create <vmid>...` | Create on-demand backups |
| `px backup list` | List available backups |
| `px backup restore <vmid> <file>` | Restore from a backup |
| `px backup delete <vmid>` | Delete backups for a VM |

### `px backup list` options

| Option | Shorthand | Description |
|--------|-----------|-------------|
| `--storage` | `-s` | Storage pool to list backups from |
| `--node` | `-n` | Node name |
| `--output` | `-o` | Output format (table, json) |
| `--color` | `-c` | Enable colored output |

### `px backup create` options

| Option | Shorthand | Default | Description |
|--------|-----------|---------|-------------|
| `--storage` | `-s` | `local` | Target storage |
| `--mode` | `-m` | `snapshot` | Backup mode (snapshot, stop, suspend) |
| `--compress` | | `zstd` | Compression (zstd, gzip, lzo, none) |
| `--force` | `-f` | | Skip confirmation |
| `--wait` | | | Wait for completion |

### `px backup delete` options

| Option | Shorthand | Description |
|--------|-----------|-------------|
| `--keep` | `-k` | Volume name pattern to keep (delete all others) |
| `--storage` | `-s` | Storage pool (default: local) |
| `--node` | `-n` | Node name |
| `--force` | `-f` | Skip confirmation |

### Examples

```bash
px backup create 100 101
px backup create 100 --storage nfs --mode stop --wait
px backup list --storage nfs
px backup restore 100 vzdump-qemu-100-2024-01-01.vma.zst --storage nfs --wait
px backup delete 100
px backup delete 100 --keep weekly
```

---

## `px template`

Manage LXC templates.

### Commands

| Command | Description |
|---------|-------------|
| `px template list` | List available LXC templates |
| `px template download <template>` | Download an LXC template |
| `px template remove <template>` | Remove a downloaded template |

### `px template list` options

| Option | Shorthand | Description |
|--------|-----------|-------------|
| `--node` | `-n` | Node name |
| `--output` | `-o` | Output format (table, json) |
| `--color` | `-c` | Enable colored output |

### `px template download` options

| Option | Shorthand | Description |
|--------|-----------|-------------|
| `--node` | `-n` | Node name |
| `--wait` | | Wait for download to complete |

### `px template remove` options

| Option | Shorthand | Description |
|--------|-----------|-------------|
| `--storage` | `-s` | Storage pool (default: local) |
| `--node` | `-n` | Node name |
| `--force` | `-f` | Skip confirmation |

### Examples

```bash
px template list
px template list --output json
px template download ubuntu-22.10-standard_22.10-1_amd64.tar.zst
px template download debian-12-standard --wait
px template remove ubuntu-22.10-standard_22.10-1_amd64.tar.zst --force
```

---

## `px node`

Manage Proxmox nodes.

### Commands

| Command | Description |
|---------|-------------|
| `px node list` | List nodes in the cluster |
| `px node status <node>` | Show detailed node status |
| `px node info <node>` | Show version and system information |
| `px node services <node>` | List services on a node |
| `px node reboot <node>` | Reboot a node |

### Options

| Command | Options |
|---------|---------|
| `px node list` | `--output` / `-o` (table, json), `--color` / `-c` |
| `px node status <node>` | `--color` / `-c` |
| `px node info <node>` | `--color` / `-c` |
| `px node services <node>` | `--output` / `-o` (table, json), `--color` / `-c` |
| `px node reboot <node>` | `--force` / `-f` (skip confirmation) |

### Examples

```bash
px node list --color
px node status pve1
px node info pve2
px node services pve1
px node services pve1 --output json
px node reboot pve1 --force
```

---

## `px pool`

Manage resource pools.

### Commands

| Command | Description |
|---------|-------------|
| `px pool list` | List resource pools |
| `px pool create <name>` | Create a new pool |
| `px pool delete <name>` | Delete a pool |
| `px pool show <name>` | Show pool details and members |
| `px pool add <name> <vmid>...` | Add VMs/containers to a pool |
| `px pool remove <name> <vmid>...` | Remove VMs/containers from a pool |

### Options

| Command | Options |
|---------|---------|
| `px pool list` | `--output` / `-o` (table, json), `--color` / `-c` |
| `px pool create <name>` | `--comment` / `-c` (pool description) |
| `px pool delete <name>` | `--force` / `-f` (skip confirmation) |
| `px pool show <name>` | `--color` / `-c` |

### Examples

```bash
px pool list --output json
px pool create production
px pool create production --comment "Production workloads"
px pool show production
px pool add production 100 101 102
px pool remove production 102
px pool delete production --force
```

---

## `px cluster`

Cluster information.

### Commands

| Command | Description |
|---------|-------------|
| `px cluster status` | Show cluster status |
| `px cluster resources` | List all cluster resources |
| `px cluster log` | Show cluster log |
| `px cluster next-id` | Get the next available VMID |

### Options

| Command | Options |
|---------|---------|
| `px cluster status` | `--output` / `-o` (table, json), `--color` / `-c` |
| `px cluster resources` | `--type` / `-t` (vm, node, storage), `--output` / `-o` (table, json), `--color` / `-c` |
| `px cluster log` | `--max` / `-n` (max log entries, default: 50) |

### Examples

```bash
px cluster status --color
px cluster status --output json
px cluster resources --type vm
px cluster resources --output json
px cluster log --max 100
px cluster next-id
```

---

## `px firewall`

Manage firewall rules.

### Commands

| Command | Description |
|---------|-------------|
| `px firewall list [--vmid <id>]` | List firewall rules (VM, node, or cluster level) |

### `px firewall list` options

| Option | Shorthand | Description |
|--------|-----------|-------------|
| `--vmid` | | VM/container ID (omit for node-level rules) |
| `--node` | `-n` | Node name |
| `--output` | `-o` | Output format (table, json) |
| `--color` | `-c` | Enable colored output |

### Examples

```bash
px firewall list
px firewall list --vmid 100 --output json
```

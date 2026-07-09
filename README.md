# px — Proxmox CLI

[![PyPI version](https://img.shields.io/pypi/v/px-cli)](https://pypi.org/project/px-cli/)
[![Python versions](https://img.shields.io/pypi/pyversions/px-cli)](https://pypi.org/project/px-cli/)
[![License](https://img.shields.io/pypi/l/px-cli)](https://github.com/AndrewOcamps/px-cli/blob/main/LICENSE)

`px` is a command-line tool for managing Proxmox VE clusters — VMs, containers,
storage, backups, snapshots, nodes, pools, firewall, and more. Inspired by the
AWS CLI.

## Install

### From PyPI (recommended)

```bash
pip install px-cli
```

### From source

```bash
git clone https://github.com/AndrewOcamps/px-cli.git
cd px-cli
pip install -e .
```

## Quick Start

```bash
px login
```

This will prompt for your Proxmox endpoint, username and password,
then create an API token automatically and save it to `~/.proxmox/config`.

## Manual Configuration

Create `~/.proxmox/config`:

```ini
endpoint=https://192.168.0.100:8006
token=user@pve!tokenid=secret
```

Environment variables override the config file:

```bash
export PX_ENDPOINT=https://192.168.0.100:8006
export PX_TOKEN=user@pve!tokenid=secret
```

## Usage

```
px <group> <command> [options]
```

### VM / Container management

```bash
px vm list                         # list VMs and containers
px vm list --status running        # running only
px vm list --name "*web*"          # wildcard name filter

px vm start 100                    # start a VM
px vm start 100 --force --wait     # skip confirm + wait for completion
px vm stop 100                     # force power-off
px vm shutdown 100                 # graceful shutdown (ACPI)
px vm reboot 100                   # reboot
px vm suspend 100                  # pause
px vm resume 100                   # resume
px vm status 100                   # detailed status panel
px vm status 100 117               # multiple VMs
```

### Snapshots

```bash
px vm snapshot list 100            # list snapshots for a VM
px vm snapshot create 100 snap1    # create a snapshot
px vm snapshot delete 100 snap1    # delete a snapshot
px vm snapshot rollback 100 snap1  # rollback to a snapshot
```

### Storage

```bash
px storage list                    # list storage pools
px storage content local           # list contents (ISOs, templates, backups)
px storage content local --type iso  # filter by content type
px storage info local              # storage pool details
```

### Backups

```bash
px backup create 100 101           # on-demand vzdump backup
px backup create 100 --storage nfs --wait
px backup list                     # list all backups
px backup restore 100 vzdump-qemu-100-2024-01-01.vma.zst
px backup delete 100 --storage nfs # delete backups for a VM
```

### Templates (LXC)

```bash
px template list                   # list available LXC templates
px template download ubuntu-22.10-standard  # download a template
px template remove ubuntu-22.10-standard    # remove a downloaded template
```

### Nodes

```bash
px node list                       # list cluster nodes
px node status pve1                # detailed node status
px node info pve1                  # version and system info
px node services pve1              # list services
px node reboot pve1                # reboot a node (with confirmation)
```

### Resource Pools

```bash
px pool list                       # list pools
px pool create my-pool             # create a pool
px pool show my-pool               # pool details and members
px pool add my-pool 100 101        # add VMs to pool
px pool remove my-pool 100         # remove VMs from pool
px pool delete my-pool             # delete a pool
```

### Cluster

```bash
px cluster status                  # cluster quorum and node status
px cluster resources               # all cluster resources
px cluster log                     # cluster event log
px cluster next-id                 # next available VMID
```

### Firewall

```bash
px firewall list                   # node-level firewall rules
px firewall list --vmid 100        # VM-level firewall rules
```

### Output options

Most commands support `--output json` and `--color` flags.

## Commands overview

| Command | Description |
|---------|-------------|
| `login` | Authenticate with username/password, create API token |
| `logout` | Remove local configuration |
| `vm` | List, start, stop, shutdown, reboot, suspend, resume, status, snapshot |
| `storage` | List pools, browse contents, pool info |
| `backup` | Create, list, restore, delete vzdump backups |
| `template` | List, download, remove LXC templates |
| `node` | List, status, info, services, reboot nodes |
| `pool` | List, create, delete, show, add, remove resource pools |
| `cluster` | Status, resources, log, next-id |
| `firewall` | List rules (node and VM level) |

See [docs/commands.md](docs/commands.md) for the full reference.

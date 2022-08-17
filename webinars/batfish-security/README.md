## Getting Started

In order to make the webinar simple yet helpful it only requires two commands to be run after the repository is cloned down.

1. Make sure you have docker installed on your system.
2. Run Python Script

### Bring up Batfish Container

```bash
docker compose up -d
```

### Create Virtual Environment and Install

```bash
poetry shell
```

```bash
poetry install
```

### Add Configuration
Add configurations into `./data/configs`.

### Run Python Script

```bash
▶ python batfish_analysis.py                                                                   
Your snapshot was successfully initialized but Batfish failed to fully recognized some lines in one or more input files. Some unrecognized configuration lines are not uncommon for new networks, and it is often fine to proceed with further analysis. You can help the Batfish developers improve support for your network by running:

    bf.upload_diagnostics(dry_run=False, contact_info='<optional email address>')

to share private, anonymized information. For more information, see the documentation with:

    help(bf.upload_diagnostics)

====================
Successfully Queries Batfish.
====================
```

### Bring Down Batfish Container

```bash
docker compose down
```

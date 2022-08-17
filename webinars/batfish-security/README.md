## Getting Started

In order to make the webinar simple yet helpful it only requires two commands to be run after the repository is cloned down.

1. Make sure you have docker installed on your system.
2. Make sure you have poetry installed on your system.
3. Follow the steps.


### Bring up Batfish Container

```bash
docker compose up -d
```

### Create Virtual Environment and Install

```bash
cd webinars/batfish-security
```

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
cd security_checks
```

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

### Analyze The Ouptus

Checkout `./batfish_results` which will have the `html` outputs for each command.

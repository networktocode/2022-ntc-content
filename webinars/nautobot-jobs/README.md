# Nautobot Jobs Webinar

The scripts hosted in this folder are the artifacts for the October 6th, 2022 webinar covering Nautobot Jobs.

## Local Scripts Getting Started

In order to make the webinar simple yet helpful it only requires two commands to be run after the repository is cloned down.

1. Make sure you have poetry installed on your system.
2. Follow the steps.

### Create Virtual Environment and Install

```bash
cd webinars/nautobot-jobs
```

```bash
poetry shell
```

```bash
poetry install
```

### Load Environment Variables & Optionally Update Regex Pattern

Make sure to replace each value with applicable value.

```bash
export NETMIKO_USER=foo
export NETMIKO_PASS=bar
export NAUTOBOT_URL=https://demo.nautobot.com
export NAUTOBOT_TOKEN=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

The python script for hostname validation checks the configured hostname based on the regex pattern on line 15 of `00-netmiko-script-verify-hostname.py` only for sites based on the slug value of `nyc` on line 105.

```python
# Expected hostname regex pattern
HOSTNAME_PATTERN = re.compile(r"[a-z0-1]+\-[a-z]+\-\d+\.infra\.ntc\.com")
```

```python
# Query nautobot via pynautobot SDK and limit to just NYC
devices = nautobot.dcim.devices.filter(site="nyc")
```

### Ensure Devices Are In Nautobot

* Device(s) are populated and associated to the site from the python script
* Platform(s) associated are one of the following
  * `cisco_ios`
  * `cisco_nxos`
  * `arista_eos`
  * `juniper_junos`
* Has a primary IP set

### Run Scripts

```bash
# First script does accept inputs
python3 00-netmiko-script-verify-hostname.py
# Second script will prompt for inputs
python3 01-netmiko-assign-vlan-to-interface.py
```

## Translated To Jobs

The first three jobs are translated to Nautobot Jobs.

### Create Git Repo With Just Jobs/ Directory

```bash
mkdir ../../../nautobot-jobs
cp -r jobs/ ../../../nautobot-jobs
cd ../../../nautobot-jobs
git init
git add -A
git commit -m "first commit"
git remote add origin <remote url>
git branch -m main
git push origin main
```

### Run Jobs In Nautobot

1. Add Git Repository & Sync to Nautobot
2. Navigate to Jobs and select appropriate job
3. Fill out form if applicable and submit

### Jobs Exposed

* 02-netmiko-nautobot-job-verify-hostname.py
  * Verifies hostname pattern for all devices at NYC site
* 03-netmiko-nautobot-job-verify-hostname-site-selection.py
  * Verifies hostname pattern for all devices at selected site
* 04-netmiko-nautobot-job-assign-vlan-to-interface.py
  * Adds existing VLAN configured on a devices to allowed VLANs on a trunk port
* 05-create-pop-in-nautobot.py
  * Create a new POP in Nautobot with devices

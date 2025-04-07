# GitHub Actions Storage Manager

This repository contains tools to manage GitHub Actions storage usage, particularly for managing workflow runs and artifacts that can quickly consume your free storage quota.

## Problem

GitHub provides limited free storage for Actions and Packages:
- Free accounts get 500MB of GitHub Packages storage
- Actions artifacts and logs consume the same storage pool
- When you reach 90% of usage, GitHub sends warning emails
- When you reach 100%, your Actions and Packages stop working until you either:
  1. Wait for the monthly reset
  2. Delete old artifacts/runs
  3. Set up a spending limit/payment plan

## Storage Management Script

The `delete_old_runs.py` script automates cleanup of old workflow runs across multiple repositories:

```python
import requests
from datetime import datetime, timedelta, UTC
import os

# === CONFIG ===
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Set this as an environment variable
ORG_NAME = "markwharton"  # Replace with your GitHub org/user
REPOS = ["hm-pdf-generator", "hm-xslfo-service-java"]
DAYS_OLD = 1

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def delete_old_runs(repo):
    print(f"📦 Checking {repo}...")
    base_url = f"https://api.github.com/repos/{ORG_NAME}/{repo}/actions/runs"
    params = {"per_page": 100}
    response = requests.get(base_url, headers=headers, params=params)
    response.raise_for_status()

    now = datetime.now(UTC)
    cutoff = now - timedelta(days=DAYS_OLD)
    deleted = 0

    for run in response.json().get("workflow_runs", []):
        created_at = datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        run_id = run["id"]
        if created_at < cutoff:
            del_url = f"https://api.github.com/repos/{ORG_NAME}/{repo}/actions/runs/{run_id}"
            del_resp = requests.delete(del_url, headers=headers)
            if del_resp.status_code == 204:
                print(f"🗑️ Deleted run {run_id} from {created_at}")
                deleted += 1
            else:
                print(f"⚠️ Failed to delete run {run_id}: {del_resp.status_code}")
    print(f"✅ Done with {repo}. Deleted {deleted} run(s).")

def main():
    for repo in REPOS:
        delete_old_runs(repo)

if __name__ == "__main__":
    main()
```

### Usage

1. Set up a GitHub Personal Access Token with the appropriate permissions (`repo` and `workflow` scopes)
2. Export the token as an environment variable:
   ```bash
   export GITHUB_TOKEN=your_github_token_here
   ```
3. Update the `ORG_NAME` and `REPOS` variables in the script
4. Run the script:
   ```bash
   python delete_old_runs.py
   ```

## Best Practices for GitHub Actions Storage Management

### 1. Set Retention Periods in Workflows

Add the `retention-days` parameter to your job or specific steps that generate artifacts:

```yaml
name: CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build artifacts
        run: make build
      - name: Upload artifacts
        uses: actions/upload-artifact@v2
        with:
          name: build-artifacts
          path: dist/
          retention-days: 1  # Delete after 1 day
```

### 2. Configure Repository-Level Artifact Retention

You can set a default artifact retention policy at the repository level:

1. Go to your repository settings
2. Navigate to Actions → General
3. Scroll down to "Artifact and log retention"
4. Set your desired retention period (minimum 1 day)

### 3. Only Upload Necessary Artifacts

Be selective about what you upload:

```yaml
- name: Upload artifacts
  uses: actions/upload-artifact@v2
  with:
    name: coverage-report
    path: |
      coverage/lcov-report
      !coverage/lcov-report/node_modules/**
    retention-days: 1
```

### 4. Use GitHub's API for Scheduled Cleanup

Create a scheduled workflow that runs the deletion script:

```yaml
name: Cleanup Old Runs
on:
  schedule:
    - cron: '0 0 * * *'  # Run daily at midnight
  workflow_dispatch:  # Allow manual triggering

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install requests
      - name: Run cleanup script
        run: python delete_old_runs.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 5. Monitor Storage Usage

Regularly check your storage usage:

- Personal account: https://github.com/settings/billing
- Organization: https://github.com/organizations/[org-name]/settings/billing

### 6. Use Caching Instead of Artifacts When Possible

For dependencies and build outputs that are used across jobs or workflows:

```yaml
- name: Cache dependencies
  uses: actions/cache@v2
  with:
    path: ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

### 7. Split Large Workflows

Split monolithic workflows into smaller ones that can be run independently, reducing the need to store large artifacts.

## Viewing Usage

To view your current GitHub Packages and Actions usage:

- Personal account: https://github.com/settings/billing
- Organization: https://github.com/organizations/[org-name]/settings/billing

You can also export detailed usage reports from these pages.

## Related GitHub Documentation

- [About billing for GitHub Packages](https://docs.github.com/en/billing/managing-billing-for-github-packages/about-billing-for-github-packages)
- [Managing GitHub Actions artifacts and logs](https://docs.github.com/en/actions/managing-workflow-runs/downloading-workflow-artifacts)
- [Artifact and log retention policy](https://docs.github.com/en/actions/learn-github-actions/usage-limits-billing-and-administration#artifact-and-log-retention-policy)

## License

MIT
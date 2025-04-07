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

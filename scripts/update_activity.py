import json
import os
import urllib.parse
import urllib.request

USERNAME = "bnquon"
TOKEN = os.environ["GH_TOKEN"]
MAX_ACTIVITY = 5

HIDDEN_REPOS = {
    "bnquon/bnquon",
}


def github_get(url):
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": USERNAME,
        },
    )

    with urllib.request.urlopen(request) as response:
        return json.load(response)


activity = []


def add_activity(timestamp, line, key):
    activity.append(
        {
            "timestamp": timestamp,
            "line": line,
            "key": key,
        }
    )


# Public GitHub activity
events = github_get(
    f"https://api.github.com/users/{USERNAME}/events/public?per_page=50"
)

for event in events:
    event_type = event["type"]
    repo = event["repo"]["name"]

    if repo in HIDDEN_REPOS:
        continue

    repo_link = f"https://github.com/{repo}"
    payload = event["payload"]
    timestamp = event["created_at"]

    if event_type == "PullRequestEvent":
        action = payload["action"]
        pr = payload["pull_request"]

        number = pr["number"]
        link = f"https://github.com/{repo}/pull/{number}"

        if action == "opened":
            add_activity(
                timestamp,
                (
                    f"↳ opened [PR #{number}]({link}) in "
                    f"[{repo}]({repo_link})"
                ),
                f"opened-pr:{repo}:{number}",
            )

    elif event_type == "PullRequestReviewEvent":
        pr = payload["pull_request"]

        # Don't show "reviewed" for your own PRs
        author = pr.get("user", {}).get("login", "")

        if author.lower() == USERNAME.lower():
            continue

        number = pr["number"]
        link = f"https://github.com/{repo}/pull/{number}"

        add_activity(
            timestamp,
            (
                f"↳ reviewed [PR #{number}]({link}) in "
                f"[{repo}]({repo_link})"
            ),
            f"reviewed-pr:{repo}:{number}",
        )

    elif event_type == "IssuesEvent":
        if payload["action"] == "opened":
            issue = payload["issue"]

            number = issue["number"]
            link = f"https://github.com/{repo}/issues/{number}"

            add_activity(
                timestamp,
                (
                    f"↳ opened [issue #{number}]({link}) in "
                    f"[{repo}]({repo_link})"
                ),
                f"opened-issue:{repo}:{number}",
            )


# Merged PRs authored by you
# This catches PRs merged by maintainers too.
query = urllib.parse.quote(
    f"author:{USERNAME} is:pr is:merged"
)

search_url = (
    "https://api.github.com/search/issues"
    f"?q={query}"
    "&sort=updated"
    "&order=desc"
    "&per_page=15"
)

merged_results = github_get(search_url)

for item in merged_results["items"]:
    pr = github_get(item["pull_request"]["url"])

    merged_at = pr.get("merged_at")

    if not merged_at:
        continue

    number = pr["number"]
    link = pr["html_url"]

    repo = "/".join(
        item["repository_url"].rstrip("/").split("/")[-2:]
    )

    if repo in HIDDEN_REPOS:
        continue

    repo_link = f"https://github.com/{repo}"

    add_activity(
        merged_at,
        (
            f"↳ merged [PR #{number}]({link}) into "
            f"[{repo}]({repo_link})"
        ),
        f"merged-pr:{repo}:{number}",
    )


# Sort newest first
activity.sort(
    key=lambda item: item["timestamp"],
    reverse=True,
)


# Remove exact duplicate activity entries
seen = set()
unique_activity = []

for item in activity:
    if item["key"] in seen:
        continue

    seen.add(item["key"])
    unique_activity.append(item)

    if len(unique_activity) == MAX_ACTIVITY:
        break


if unique_activity:
    lines = [item["line"] for item in unique_activity]
else:
    lines = ["↳ no recent public activity"]


# Update README
section = """<!-- ACTIVITY_START -->
{}
<!-- ACTIVITY_END -->""".format("  \n".join(lines))

with open("README.md", "r", encoding="utf-8") as file:
    readme = file.read()

start = readme.index("<!-- ACTIVITY_START -->")
end = (
    readme.index("<!-- ACTIVITY_END -->")
    + len("<!-- ACTIVITY_END -->")
)

readme = readme[:start] + section + readme[end:]

with open("README.md", "w", encoding="utf-8") as file:
    file.write(readme)

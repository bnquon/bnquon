import json
import os
import urllib.request

USERNAME = "bnquon"
TOKEN = os.environ["GH_TOKEN"]

url = f"https://api.github.com/users/{USERNAME}/events/public?per_page=30"

request = urllib.request.Request(
    url,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": USERNAME,
    },
)

with urllib.request.urlopen(request) as response:
    events = json.load(response)

activity = []

for event in events:
    event_type = event["type"]
    repo = event["repo"]["name"]
    payload = event["payload"]

    line = None

    if event_type == "PullRequestEvent":
        action = payload["action"]
        pr = payload["pull_request"]

        number = pr["number"]
        link = f"https://github.com/{repo}/pull/{number}"

        if action == "opened":
            line = f"↳ opened [PR #{number}]({link}) in `{repo}`"

        elif action == "closed" and pr.get("merged"):
            line = f"↳ merged [PR #{number}]({link}) in `{repo}`"

    elif event_type == "IssuesEvent":
        if payload["action"] == "opened":
            issue = payload["issue"]
            number = issue["number"]
            link = f"https://github.com/{repo}/issues/{number}"

            line = f"↳ opened [issue #{number}]({link}) in `{repo}`"

    elif event_type == "IssueCommentEvent":
        issue = payload["issue"]
        number = issue["number"]

        if "pull_request" in issue:
            link = f"https://github.com/{repo}/pull/{number}"
            line = f"↳ commented on [PR #{number}]({link}) in `{repo}`"

        else:
            link = f"https://github.com/{repo}/issues/{number}"
            line = f"↳ commented on [issue #{number}]({link}) in `{repo}`"

    elif event_type == "PullRequestReviewEvent":
        pr = payload["pull_request"]

        number = pr["number"]
        link = f"https://github.com/{repo}/pull/{number}"

        line = f"↳ reviewed [PR #{number}]({link}) in `{repo}`"

    if line and line not in activity:
        activity.append(line)

    if len(activity) == 5:
        break

if not activity:
    activity = ["↳ no recent public activity"]

section = """<!-- ACTIVITY_START -->
{}
<!-- ACTIVITY_END -->""".format("  \n".join(activity))

with open("README.md", "r", encoding="utf-8") as file:
    readme = file.read()

start = readme.index("<!-- ACTIVITY_START -->")
end = readme.index("<!-- ACTIVITY_END -->") + len("<!-- ACTIVITY_END -->")

readme = readme[:start] + section + readme[end:]

with open("README.md", "w", encoding="utf-8") as file:
    file.write(readme)

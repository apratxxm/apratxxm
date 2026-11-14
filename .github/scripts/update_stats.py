"""Refresh the live numbers in the README's neofetch block."""
import json
import os
import re
import urllib.request

USER = "apratxxm"
QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection { contributionCalendar { totalContributions } }
    repositories(privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false) { totalCount }
  }
}"""


def fetch():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"], "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if body.get("errors"):
        raise SystemExit("GraphQL error: %s" % body["errors"])
    user = body["data"]["user"]
    return user["contributionsCollection"]["contributionCalendar"]["totalContributions"], user["repositories"]["totalCount"]


def main():
    contribs, repos = fetch()
    path = os.environ.get("README_PATH", "README.md")
    text = open(path, encoding="utf-8").read()
    new, n1 = re.subn(r"(?m)^(activity +)[\d,]+( contributions in the last year)$", r"\g<1>{:,}\g<2>".format(contribs), text)
    new, n2 = re.subn(r"(?m)^(packages +)\d+( public repos)$", r"\g<1>{}\g<2>".format(repos), new)
    if n1 != 1 or n2 != 1:
        raise SystemExit("expected one activity line and one packages line, found %d and %d" % (n1, n2))
    if new != text:
        open(path, "w", encoding="utf-8", newline="\n").write(new)
    print("contributions=%d repos=%d changed=%s" % (contribs, repos, new != text))


if __name__ == "__main__":
    main()

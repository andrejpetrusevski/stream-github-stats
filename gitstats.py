import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from itertools import groupby, product
from pathlib import Path

from github import Github


def by_pulls_issues(all_items, key):
    by_pulls = defaultdict(int)
    by_issues = defaultdict(int)

    by_attr = groupby(
        all_items, lambda x, key=key: (getattr(x, key).year, getattr(x, key).month)
    )
    for key, items in by_attr:
        for item in items:
            if "/pull/" in item.html_url:
                by_pulls[f"{key[0]}-{key[1]}"] += 1
            else:
                by_issues[f"{key[0]}-{key[1]}"] += 1

    return {"by_pulls": by_pulls, "by_issues": by_issues}


def load_data(repo, now, cache: Path, only_cache: bool):
    if only_cache:
        if not cache.exists():
            print("only-cache==True but cache does not exist")
            sys.exit(1)
        with cache.open("r") as f:
            return json.load(f)
    print("Getting data from GitHub")
    first_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month = (first_this_month - timedelta(days=10)).replace(day=1)

    if not cache.exists():
        # load in 2 years worth of data if there is no cache
        since = previous_month.replace(year=now.year - 2)
    else:
        # There is a cache, only need to update the previous month + this month
        since = previous_month

    issues = repo.get_issues(state="all", since=since)
    all_issues = list(issues)
    print(all_issues)
    """
    new_data = {
        "created_bys": by_pulls_issues(all_issues, "created_at"),
        "closed_bys": by_pulls_issues(
            (i for i in all_issues if i.closed_at is not None), "closed_at"
        ),
    }

    if not cache.exists():
        print("Saving to cache")
        with cache.open("w") as f:
            json.dump(new_data, f)
        return new_data

    print("Updating cache")
    # cache exist -> need to update data and cache
    now_str = f"{now.year}-{now.month}"
    previous_str = f"{previous_month.year}-{previous_month.month}"

    # Update cache data
    with cache.open("r") as f:
        data = json.load(f)
    keys = product(
        ["created_bys", "closed_bys"],
        ["by_pulls", "by_issues"],
        [previous_str, now_str],
    )
    for key1, key2, time_key in keys:
        data[key1][key2][time_key] = max(
            data[key1][key2].get(time_key, 0), new_data[key1][key2].get(time_key, 0)
        )

    with cache.open("w") as f:
        json.dump(data, f)
    return data
    """


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "cache", help="Cache folder/file", type=str, default="cache.json"
    )
    # parser.add_argument("dist", help="Distribution folder", type=str, default="dist/index.html")
    parser.add_argument(
        "--github_token",
        help="GitHub Token",
        type=str,
        default=os.environ.get("GITHUB_TOKEN"),
    )
    parser.add_argument(
        "--repo",
        help="Repo to query",
        type=str,
        default="andrejpetrusevski/stream-github-stats",
    )
    parser.add_argument("--logo", help="logo", type=str, default="logo.svg")
    parser.add_argument(
        "--only-cache", help="Only use cached data", action="store_true"
    )
    args = parser.parse_args()
    gh = Github(args.github_token)
    now = datetime.now(tz=timezone.utc)

    repo = gh.get_repo(args.repo)
    data = load_data(repo, now, Path(args.cache), args.only_cache)

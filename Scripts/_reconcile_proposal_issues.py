"""Reconcile proposal titles/slugs from merged registry metadata, with no Git writes."""
import json
from _common import BASE
from _rename_study import update_github_issue


def main() -> None:
    registry = json.loads((BASE / 'Studies/proposal-registry.json').read_bytes())
    for row in registry.get('proposals', []):
        number = row.get('issueNumber')
        if number and row.get('slug') and row.get('title'):
            update_github_issue(int(number), row['slug'], row['title'])


if __name__ == '__main__':
    main()

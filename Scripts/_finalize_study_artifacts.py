"""Finalize tracked study artifacts with the same producers used by preparation.

Run after authoring and targeted renders, before committing. This command does
not render PDFs, change source timestamps, access GitHub, or publish anything.
"""
from __future__ import annotations

import argparse


def finalize(studies: list[str] | None = None) -> None:
    from _build_studies_index import write_index_html
    from _build_social_cards import build as build_social_cards
    from _companion_artifacts import write_registry
    from _publish_generated_pdf_worker import sync_keys
    from _study_search import batch_search_updates, flush_search_updates, write_search_catalog
    from _verify_companion_outputs import verify as verify_companions
    from _verify_studies_index import collect_index_errors

    with batch_search_updates():
        if studies:
            # Reuse preparation's metadata synchronization without changing the
            # author's Edited-on value or invoking a lifecycle handler/render.
            from _ci_study_pr import sync_catalog_timestamp_from_md, mark_registry_in_catalog
            from _build_discussion_pages import write_discussion_page
            from _study_catalog import get_study_row, StudyStatus
            for slug in studies:
                sync_catalog_timestamp_from_md(slug)
                row = get_study_row(slug)[0]
                if row.status in {StudyStatus.DRAFT, StudyStatus.RELEASED}:
                    mark_registry_in_catalog(slug)
                write_discussion_page(row)
        write_index_html()
        write_registry()
        sync_keys()
        build_social_cards()
        write_search_catalog()
        # Preparation may own an outer batch; verify only after finalization.
        flush_search_updates()
    errors = collect_index_errors() + verify_companions()
    if errors:
        raise ValueError('Study artifact finalization failed:\n  - ' + '\n  - '.join(errors))
    print('Study index, companion inventory, PDF keys, social cards, search/offline and companion outputs are current.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', action='append', help='Sync this canonical study catalog from its authored metadata; repeatable')
    args = parser.parse_args()
    finalize(args.study)


if __name__ == '__main__':
    main()

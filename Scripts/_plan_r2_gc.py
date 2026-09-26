"""Plan backed-up, old, unreachable staging objects; never delete anything."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from dataclasses import replace
import json
from pathlib import Path
import re

from _backup_r2 import inventory, verify
from _r2_s3 import R2S3Client, load_r2_config
from _site_release import safe_path

OBJECT = re.compile(r'site/objects/([a-f0-9]{64})')


def reachable(records: dict) -> set[str]:
    protected = set(records)
    def protect(record):
        key = record.get('key', '')
        sha = record.get('sha256', '')
        if key != 'site/objects/' + sha or not OBJECT.fullmatch(key) or not isinstance(record.get('bytes'), int) or record['bytes'] <= 0:
            raise ValueError('Invalid retained object record')
        protected.add(key)
    for key, data in records.items():
        if data.get('schema') != 1:
            raise ValueError('Unsupported retained record: ' + key)
        if key.startswith('site/releases/'):
            if key != 'site/releases/' + data.get('revision', '') + '.json' or not isinstance(data.get('files'), dict):
                raise ValueError('Invalid retained release')
            for path, record in data['files'].items():
                if not safe_path(path):
                    raise ValueError('Unsafe retained path')
                if record.get('archive'):
                    protect(record)
        elif key.startswith('site/builds/'):
            from _publication_plan import receipt_key
            if key != receipt_key(data):
                raise ValueError('Invalid protected build receipt')
            for artifact in data['artifacts'].values():
                if artifact['node']['family'] != 'references':
                    protect(artifact['record'])
        elif key.startswith('site/assets/'):
            from _release_assets import asset_record_key
            if not safe_path(data.get('path', '')) or key != asset_record_key(data['path'], data['record']['sha256']):
                raise ValueError('Invalid retained asset binding')
            protect(data['record'])
        else:
            raise ValueError('Unexpected retained index')
    return protected


def plan(rows: list[dict], protected: set[str], backup: dict, now: datetime) -> dict:
    saved = {(row['bucket'], row['key']): row for row in backup['objects']}
    candidates = []
    for row in rows:
        match = OBJECT.fullmatch(row['key'])
        if not match or row['key'] in protected:
            continue
        stamp = datetime.fromisoformat(row['last_modified'].replace('Z', '+00:00'))
        if stamp.tzinfo is None:
            raise ValueError('Inventory timestamp has no time zone')
        if now - stamp < timedelta(days=90):
            continue
        proof = saved.get((row['bucket'], row['key']))
        if not proof or any(proof.get(field) != row[field] for field in ('etag', 'bytes', 'last_modified')) or proof.get('sha256') != match.group(1):
            continue
        candidates.append({**row, 'sha256': proof['sha256'], 'reason': 'unreachable staging object, 90 days old, verified independent backup'})
    return {'schema': 1, 'readOnly': True, 'deletionAuthorized': False, 'generatedAt': now.isoformat(),
            'retentionDays': 90, 'retainedRecords': len(protected), 'candidates': candidates}


def run(backup_root: Path, output: Path, bucket: str):
    # A verified manifest alone is insufficient: verify every downloaded archive.
    backup = verify(backup_root)
    client = R2S3Client(replace(load_r2_config(), bucket=bucket))
    before = inventory(client)
    index_keys = [row['key'] for row in before if row['key'].startswith(('site/releases/', 'site/builds/', 'site/assets/'))]
    def load(key):
        return key, json.loads(client.get_object(key))
    with ThreadPoolExecutor(max_workers=8) as pool:
        records = dict(pool.map(load, index_keys))
    protected = reachable(records)
    if inventory(client) != before:
        raise ValueError('Bucket changed during planning; retry against a stable inventory')
    report = plan(before, protected, backup, datetime.now(timezone.utc))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(f'{len(report["candidates"])} possible staging-object candidates. No deletion is authorized or performed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verified-backup', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--bucket', default='amd-public-pdfs')
    args = parser.parse_args()
    run(args.verified_backup, args.output, args.bucket)

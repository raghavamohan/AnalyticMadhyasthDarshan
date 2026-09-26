# R2 backups in Google Drive

The independent backup destination is the owner's private
[Analytic Madhyasth Darshan - R2 Backups](https://drive.google.com/drive/folders/1PV_XnPewdSzJ-gFS10Z54HyFTNVowhWY)
folder. Each snapshot has its own child folder. Keep existing snapshots when
creating a new one; this is a backup, not a mirror that propagates deletion.
The operational work item remains `R2-BACKUP` in [PENDING.md](../PENDING.md#references).

The first full snapshot, dated 26 September 2026, is in
[this private snapshot folder](https://drive.google.com/drive/folders/1B0IOm--9Qd2O0_fNNOdSCUPuJccVlLs5).
It covers 3,322 source objects (723,911,805 bytes), stored as 3,274 unique blobs
in twelve ZIP parts. Every uploaded part and the manifest were downloaded from
Drive and matched their local SHA-256. The Drive downloads also passed the
credential-free extraction/recovery drill. The recorded file IDs and hashes are
in [the verification receipt](../infra/r2-backup/drive-receipt-2026-09-26.json).

## Scope and format

`Scripts/_backup_r2.py` reads both complete buckets: `amd-public-pdfs` and
`amd-reference-archive`. This includes generated PDFs, site release objects,
release manifests/build receipts, public reference PDFs, and private archived
HTML originals. It reads directly from R2 rather than from the public website,
so historical and private objects are included. It never writes or deletes R2
objects or changes publication pointers.

The snapshot contains `manifest.json` and `objects-NNN.zip` parts, approximately
64 MiB each. A single object larger than that target stays in one part. Identical
bytes are stored once, with SHA-256 filenames; the manifest maps every original
bucket/key to its blob and preserves size, ETag, modification time, content
headers and custom metadata. This avoids Windows filename and path collisions.
No credential files or access tokens are included. The backup is private because
it includes archived originals that are not licensed for public distribution.

Downloads use conditional GETs and check size, ETag, publisher SHA-256 metadata
when present, and simple-object MD5 ETags. The complete source inventory is read
again before packaging; concurrent changes invalidate the run. This verifies an
unchanged inventory during the run, rather than claiming an atomic cross-bucket
snapshot. Interruptions during download can resume only while that inventory
still matches. Interrupted packaging requires a new output directory.

A completed manifest is written only after every ZIP and every contained blob
passes checksum verification. Archives have SHA-256 and MD5 checksums for Drive
upload verification. A Drive receipt is recorded only after checking uploaded
file metadata, download checksums, and the folder's private sharing state. Drive
checksums describe stored binary content; see the
[Google Drive files API](https://developers.google.com/workspace/drive/api/reference/rest/v3/files).

## Create and store another snapshot

From the repository root, with the existing R2 credentials in ignored `.env`
or environment variables:

```powershell
python Scripts/_backup_r2.py snapshot
```

The command prints a unique directory under ignored `tmp/r2-backup/`. For a
controlled output location or resumed download:

```powershell
python Scripts/_backup_r2.py snapshot --output tmp/r2-backup/my-snapshot --workers 8
```

Use the connected Google Drive plugin to create a new child folder in the
destination above and upload `objects-*.zip`, `manifest.json`, and a copy of this
recovery guide. Upload binary ZIPs without converting them to Google documents.
Read back each file's size and checksum and compare with its local counterpart.
If the connector omits checksum fields, download each uploaded file through the
connector and compare its SHA-256 instead. Check that the destination folder
remains private. Record the observed file
IDs, URLs, sizes and matching checksums in `drive-receipt.json`, then upload that
receipt last. A folder with only some parts is an incomplete backup.

The Drive connector is used for uploads; this local script does not borrow its
OAuth token or create another credential. There is no automatic schedule in this
implementation. A scheduled transfer needs an explicitly configured Drive
authentication method and cadence; do not claim unattended backups are running.

## Verify and rehearse recovery

Download `manifest.json` and every ZIP part from one completed Drive snapshot
into a local directory. The following commands need neither R2 nor Drive
credentials and do not contact production:

```powershell
python Scripts/_backup_r2.py verify tmp/r2-backup/my-snapshot
python Scripts/_backup_r2.py extract tmp/r2-backup/my-snapshot --output tmp/r2-recovery-drill
```

The recovery directory must be new. It contains `objects/<sha256>` plus the exact
bucket/key mapping in `manifest.json`. The command verifies the archives first,
extracts the blobs safely and checks every recovered file's SHA-256. Keep the
Drive receipt with the download: the manifest and part checksums should match
the receipt as well as one another.

For an actual production recovery, identify the missing keys in the manifest,
stage their verified blobs in a separate recovery bucket, restore the recorded
content headers/custom metadata, and check byte hashes and release-manifest
dependencies before selecting a release. Restoring storage alone does not
restore Worker configuration, D1 databases, secrets, Git sources or account
settings. Do not restore every historical manifest over the active publication
pointer or run a destructive sync.

## Deletion protection boundary

The Drive snapshot provides independent recovery. Source-bucket locks remain a
separate part of `R2-BACKUP`: choose retention and verify correction/withdrawal
behavior before applying them. Cloudflare locks prevent both deletion and
overwriting and can cover existing objects, so a blanket lock can obstruct
legitimate correction workflows. See
[Cloudflare bucket locks](https://developers.cloudflare.com/r2/buckets/bucket-locks/).

## Local validation

```powershell
python Scripts/_test_backup_r2.py
python Scripts/_test_generated_file_writes.py
```

The focused suite covers source changes, checksum failures, damaged/missing
archive parts, pagination, verified download resumption, safe extraction of
hostile or case-colliding keys, and completion markers.

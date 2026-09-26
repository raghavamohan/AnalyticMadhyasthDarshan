"""Canonicalize presentation PDF metadata and reachable object ordering.

LibreOffice can emit identical font streams in different object orders. Sorting
dictionary keys before cloning makes traversal deterministic; dates and trailer
IDs come from the PPTX source. Tagged structure, bookmarks and links are kept.
"""
from datetime import datetime, timezone
import hashlib
import re
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, ByteStringObject, DecodedStreamObject, DictionaryObject, IndirectObject, NameObject


def source_time(pptx: Path) -> datetime:
    with zipfile.ZipFile(pptx) as archive:
        root = ET.fromstring(archive.read('docProps/core.xml'))
    modified = root.find('{http://purl.org/dc/terms/}modified')
    if modified is None or not modified.text:
        return datetime(2020, 1, 1, tzinfo=timezone.utc)
    stamp = datetime.fromisoformat(modified.text.replace('Z', '+00:00'))
    if stamp.tzinfo is None:
        raise ValueError('PPTX modification time must have a time zone')
    return stamp.astimezone(timezone.utc)


def canonicalize(pptx: Path, pdf: Path) -> None:
    from _verify_presentation_reproducible import rendered_content_fingerprint
    before = rendered_content_fingerprint(pdf)
    reader = PdfReader(pdf)
    stamp = source_time(pptx)
    for generation, offsets in reader.xref.items():
        for number in offsets:
            if number == 0:
                continue
            obj = IndirectObject(number, generation, reader).get_object()
            if isinstance(obj, DictionaryObject):
                entries = sorted(obj.items())
                obj.clear()
                obj.update(entries)
    root = reader.trailer['/Root']
    metadata = root.get('/Metadata')
    if metadata:
        original = metadata.get_object()
        # These timestamps are in XMP metadata, never in page content streams.
        data = re.sub(rb'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:[+-]\d\d:\d\d|Z)',
                      stamp.strftime('%Y-%m-%dT%H:%M:%SZ').encode(), original.get_data())
        replacement = DecodedStreamObject()
        replacement.update({k: v for k, v in original.items() if k not in ('/Length', '/Filter', '/DecodeParms')})
        replacement.set_data(data)
        root[NameObject('/Metadata')] = replacement
    writer = PdfWriter(clone_from=reader)
    date = stamp.strftime('D:%Y%m%d%H%M%SZ')
    writer.add_metadata({'/CreationDate': date, '/ModDate': date})
    identifier = hashlib.sha256(pptx.read_bytes()).digest()[:16]
    writer._ID = ArrayObject([ByteStringObject(identifier), ByteStringObject(identifier)])
    temporary = pdf.with_suffix('.canonical.pdf')
    try:
        writer.write(temporary)
        if rendered_content_fingerprint(temporary) != before:
            raise ValueError('PDF canonicalization changed page geometry, text or rendered pixels')
        after = PdfReader(temporary)
        for key in ('/StructTreeRoot', '/MarkInfo', '/Outlines'):
            if (key in after.trailer['/Root']) != (key in root):
                raise ValueError('PDF canonicalization lost ' + key)
        if [len(p.get('/Annots', [])) for p in after.pages] != [len(p.get('/Annots', [])) for p in reader.pages]:
            raise ValueError('PDF canonicalization lost annotations')
        temporary.replace(pdf)
    finally:
        temporary.unlink(missing_ok=True)

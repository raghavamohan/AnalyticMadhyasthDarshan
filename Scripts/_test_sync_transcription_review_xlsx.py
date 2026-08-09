import unittest

from Scripts._sync_transcription_review_xlsx import (
    ALLOWED_REVIEW,
    SEGMENT_HEADERS,
    column_index,
    table_records,
)


class ReviewWorkbookReaderTests(unittest.TestCase):
    def test_excel_column_references(self) -> None:
        self.assertEqual(column_index("A1"), 0)
        self.assertEqual(column_index("Z9"), 25)
        self.assertEqual(column_index("AA10"), 26)
        self.assertEqual(column_index("AZ2"), 51)

    def test_segment_table_mapping_and_blank_rows(self) -> None:
        headers = list(SEGMENT_HEADERS)
        row = ["" for _ in headers]
        row[headers.index("Segment ID")] = "S0001"
        row[headers.index("Review")] = "UNREVIEWED"
        row[headers.index("Raw ASR")] = "चुम्बकीयता"
        records = table_records([headers, row, ["" for _ in headers]], SEGMENT_HEADERS)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["segment_id"], "S0001")
        self.assertEqual(records[0]["raw_asr"], "चुम्बकीयता")

    def test_review_values_match_excel_dropdown(self) -> None:
        self.assertEqual(ALLOWED_REVIEW, {"UNREVIEWED", "R", "P", "U"})

    def test_missing_required_column_is_rejected(self) -> None:
        headers = [header for header in SEGMENT_HEADERS if header != "Evidence"]
        with self.assertRaisesRegex(ValueError, "evidence"):
            table_records([headers], SEGMENT_HEADERS)


if __name__ == "__main__":
    unittest.main()

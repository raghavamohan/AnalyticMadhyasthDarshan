"""Exercise the author/reader boundary, including math placeholder survival."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from _common import BASE
from _convert_to_pdf import convert_to_html, _study_seo_head_html
from _safe_study_html import sanitize_author_html
from _verify_study_svgs import verify_svg_file


class SafeStudyHtmlTests(unittest.TestCase):
    def test_active_html_urls_and_dom_clobbering_are_removed(self):
        result = sanitize_author_html('''<script>alert(1)</script><iframe srcdoc="bad"></iframe>
          <img src="x.png" onerror="alert(1)"><a href="jav&#x61;script:alert(1)" id="study-section-next">link</a>
          <svg onload="alert(1)"></svg><form id="study-toolbar"><input name="action"></form>
          <span style="position:fixed" class="study-toolbar">text</span>''')
        soup = BeautifulSoup(result, "html.parser")
        self.assertFalse(soup.select("script,iframe,svg,form,input,[onerror],[onload],[id],[style],[class]"))
        self.assertFalse(soup.a.has_attr("href"))
        self.assertEqual(soup.img["src"], "x.png")
        self.assertIn("link", soup.get_text())

    def test_full_converter_preserves_math_and_safe_markdown(self):
        with tempfile.TemporaryDirectory(dir=BASE) as directory:
            md = Path(directory) / "study.md"
            md.write_bytes(b'# Study\n\nLet $x_1$ be a value.\n\n| A | B |\n| --- | --- |\n| a | b |\n\n```mermaid\ngraph TD\n A --> B\n```\n')
            with patch("_convert_to_pdf.render_latex_math", side_effect=lambda value: value) as render:
                result = convert_to_html(md, include_web_chrome=True).read_text(encoding="utf-8")
            self.assertIn("$x_1$", render.call_args.args[0])
            self.assertIn('class="mermaid"', result)
            self.assertIn("<table>", result)
            self.assertNotIn("MATH_0", result)

    def test_metadata_cannot_close_its_script_element(self):
        result = _study_seo_head_html(title='</script><script>alert(1)</script>', description='safe', canonical_url='https://example.org', date_modified_iso=None, slug='Test')
        scripts = BeautifulSoup(result, "html.parser").find_all("script")
        self.assertEqual(len(scripts), 1)
        self.assertEqual(scripts[0]["type"], "application/ld+json")

    def test_svg_rejects_active_content_and_external_resources(self):
        with tempfile.TemporaryDirectory(dir=BASE) as directory:
            svg = Path(directory) / "figure.svg"
            for content in ['<script>alert(1)</script>', '<g onload="bad"/>', '<foreignObject/>', '<use href="https://evil.example/x"/>', '<style>@import "https://evil.example";</style>']:
                svg.write_bytes(('<svg xmlns="http://www.w3.org/2000/svg">' + content + '</svg>').encode())
                self.assertTrue(verify_svg_file(svg), content)
            svg.write_bytes(b'<svg xmlns="http://www.w3.org/2000/svg"><defs><marker id="a"/></defs><path marker-end="url(#a)"/></svg>')
            self.assertEqual(verify_svg_file(svg), [])


if __name__ == "__main__":
    unittest.main()

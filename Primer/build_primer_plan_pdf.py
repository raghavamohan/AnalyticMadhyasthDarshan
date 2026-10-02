"""Render the standalone Primer book plan as an A4 PDF.

Preserves the plan's Georgia/Mangal typography, table layouts, portrait and
Hindi sample pages. This renderer is separate from the Studies/Applications
publication pipeline and uses no scratch-directory or machine-specific package
paths.

Dependencies: reportlab>=4.5.1, uharfbuzz, markdown, beautifulsoup4 and Pillow.
Fonts default to C:/Windows/Fonts; --font-dir must contain georgia.ttf,
georgiab.ttf, georgiai.ttf, georgiaz.ttf, mangal.ttf and mangalb.ttf.

From the repository root:
    python Primer/build_primer_plan_pdf.py
    python Primer/build_primer_plan_pdf.py --check

Default paths are independent of the working directory. The source is the
adjacent madhyasth-darshan-primer-book-plan.md and
the default output is <source-stem>-revised.pdf beside that source. Images are
resolved relative to the source. --vendor optionally names an explicitly
supplied directory of installed Python packages; it is never inferred.
"""

from pathlib import Path
from html import escape
from io import BytesIO
import argparse
import hashlib
import json
import re
import sys


DEFAULT_SOURCE = Path(__file__).with_name('madhyasth-darshan-primer-book-plan.md')
DEFAULT_FONT_DIR = Path('C:/Windows/Fonts')
FONT_FILES = ('georgia.ttf', 'georgiab.ttf', 'georgiai.ttf', 'georgiaz.ttf',
              'mangal.ttf', 'mangalb.ttf')


def render_plan(source: Path, font_dir: Path) -> tuple[bytes, dict]:
    """Build both pagination passes in memory and return PDF bytes and metadata.

    Nothing is written here. Fixed ReportLab metadata makes the output repeatable
    for unchanged source, images, fonts and dependency versions.
    """
    source = source.resolve()
    font_dir = font_dir.resolve()
    root = Path(__file__).resolve().parents[1]
    if not source.is_file():
        raise FileNotFoundError(f'Plan Markdown not found: {source}')
    missing_fonts = [str(font_dir / name) for name in FONT_FILES
                     if not (font_dir / name).is_file()]
    if missing_fonts:
        raise FileNotFoundError('Required fonts not found: ' + ', '.join(missing_fonts))

    import uharfbuzz  # Required for correctly shaped Devanagari.
    import markdown
    from bs4 import BeautifulSoup, NavigableString, Tag
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    for name, file in [('Georgia','georgia.ttf'),('Georgia-Bold','georgiab.ttf'),('Georgia-Italic','georgiai.ttf'),('Georgia-BoldItalic','georgiaz.ttf'),('Mangal','mangal.ttf'),('Mangal-Bold','mangalb.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(font_dir/file), shapable=name.startswith('Mangal')))
    pdfmetrics.registerFontFamily('Georgia',normal='Georgia',bold='Georgia-Bold',italic='Georgia-Italic',boldItalic='Georgia-BoldItalic')
    pdfmetrics.registerFontFamily('Mangal',normal='Mangal',bold='Mangal-Bold',italic='Mangal',boldItalic='Mangal-Bold')

    page_w,page_h=A4
    left=right=55
    body_w=page_w-left-right
    dark=colors.HexColor('#193d48')
    teal=colors.HexColor('#2a707b')
    ink=colors.HexColor('#22333a')
    muted=colors.HexColor('#617078')
    rule=colors.HexColor('#bed0d2')
    tint=colors.HexColor('#edf4f3')

    def style(name, **kw):
        opts=dict(fontName='Georgia',fontSize=9.8,leading=14.2,textColor=ink)
        opts.update(kw)
        return ParagraphStyle(name,**opts)

    s={
     'body':style('body',spaceAfter=8.5,allowWidows=0,allowOrphans=0),
     'guiding':style('guiding',spaceAfter=8.5,allowWidows=0,allowOrphans=0,keepWithNext=True),
     'intro':style('intro',spaceAfter=5.5,allowWidows=0,allowOrphans=0),
     'h2':style('h2',fontName='Georgia-Bold',fontSize=17.5,leading=22.5,textColor=dark,spaceBefore=15,spaceAfter=9,keepWithNext=True),
     'h3':style('h3',fontName='Georgia-Bold',fontSize=11.8,leading=16.5,textColor=dark,spaceBefore=12,spaceAfter=6,keepWithNext=True),
     'part':style('part',fontName='Georgia-Bold',fontSize=11.6,leading=16,textColor=dark,spaceBefore=10,spaceAfter=4,keepWithNext=True),
     'toc':style('toc',fontSize=10,leading=14,leftIndent=14,firstLineIndent=-13,spaceAfter=3),
     'cell':style('cell',fontSize=7.85,leading=10.7,spaceAfter=0),
     'key':style('key',fontName='Georgia-Bold',fontSize=7.85,leading=10.7,textColor=dark,spaceAfter=0),
     'head':style('head',fontName='Georgia-Bold',fontSize=8,leading=10.7,textColor=colors.white,spaceAfter=0),
     'kicker':style('kicker',fontName='Georgia-Bold',fontSize=9.8,leading=14,textColor=teal,alignment=TA_CENTER),
     'title':style('title',fontName='Georgia-Bold',fontSize=27,leading=35,textColor=dark,alignment=TA_CENTER),
     'subtitle':style('subtitle',fontName='Georgia-Italic',fontSize=12,leading=19,textColor=teal,alignment=TA_CENTER),
     'detail':style('detail',fontSize=9.5,leading=16,textColor=muted,alignment=TA_CENTER),
     'sample_heading':style('sample_heading',fontName='Georgia-Bold',fontSize=12,leading=17,textColor=dark,alignment=TA_CENTER,spaceAfter=24),
     'portrait_name':style('portrait_name',fontName='Georgia-Bold',fontSize=22,leading=27,textColor=dark,alignment=TA_CENTER,spaceBefore=16,spaceAfter=3),
     'portrait_italic':style('portrait_italic',fontName='Georgia-Italic',fontSize=10,leading=15,alignment=TA_CENTER,spaceAfter=14),
     'portrait_label':style('portrait_label',fontName='Georgia-Bold',fontSize=14,leading=19,textColor=teal,alignment=TA_CENTER,spaceAfter=12),
     'wish':style('wish',fontName='Mangal',fontSize=15,leading=26,alignment=TA_CENTER,shaping=True),
     'wish_en':style('wish_en',fontSize=10,leading=15,alignment=TA_CENTER,spaceBefore=18,spaceAfter=7),
     'credit':style('credit',fontSize=7.1,leading=11,textColor=muted,alignment=TA_CENTER,spaceAfter=8),
     'song_title':style('song_title',fontName='Mangal-Bold',fontSize=23,leading=30,textColor=dark,alignment=TA_CENTER,shaping=True,spaceAfter=24),
     'song':style('song',fontName='Mangal',fontSize=12,leading=22,alignment=TA_CENTER,shaping=True),
    }

    class ActualTextParagraph(Paragraph):
        def __init__(self,text,sty):
            self.actual_text=text
            super().__init__(escape(text),sty)
        def draw(self):
            self.canv._code.append('/Span << /ActualText <'+('FEFF'+self.actual_text.encode('utf-16-be').hex().upper())+'> >> BDC')
            super().draw()
            self.canv._code.append('EMC')

    def inline(node):
        if isinstance(node,NavigableString):return escape(str(node))
        body=''.join(inline(c) for c in node.children)
        if node.name in ('strong','b'):return f'<b>{body}</b>'
        if node.name in ('em','i'):return f'<i>{body}</i>'
        if node.name=='a':
            href=node.get('href','')
            if href.startswith('../Studies/') and '.md' in href:
                href='https://'+(root/'CNAME').read_text().strip()+'/'+href[3:].replace('.md','.html',1)
            elif href.startswith('../PENDING.md'):
                href='https://github.com/raghavamohan/AnalyticMadhyasthDarshan/blob/master/'+href[3:]
            elif href.startswith('assets/'):
                href='https://github.com/raghavamohan/AnalyticMadhyasthDarshan/blob/master/Primer/'+href
            if href.startswith(('https://','http://','mailto:','#')):
                return f'<link href="{escape(href,quote=True)}" color="#28707b">{body}</link>'
            return body
        if node.name=='code':return f'<font face="Courier">{body}</font>'
        if node.name=='br':return '<br/>'
        return body

    def markup(tag):return ''.join(inline(c) for c in tag.children)

    def make_table(tag):
        rows=tag.find_all('tr')
        headers=[c.get_text(' ',strip=True) for c in rows[0].find_all(['th','td'],recursive=False)]
        n=len(headers)
        shares={4:[.29,.42,.12,.17],3:[.27,.40,.33],2:[.46,.54]}.get(n,[1/n]*n)
        if headers[0]=='Chapter':shares=[.21,.38,.30,.11]
        elif headers[0].startswith('Essential concept'):shares=[.24,.36,.16,.24]
        elif headers[0].startswith('Group to keep'):shares=[.31,.38,.31]
        elif headers[0].startswith('Scene and'):shares=[.17,.24,.35,.24]
        elif headers[0].startswith('Source and'):shares=[.31,.14,.55]
        elif headers[0]=='Faculty':shares=[.16,.20,.64]
        elif headers[0]=='Motive':shares=[.22,.45,.33]
        elif headers[0]=='Orientation':shares=[.17,.33,.35,.15]
        elif headers[0].startswith('Level and'):shares=[.31,.53,.16]
        elif headers[-1]=='Everyday entrance':shares=[.19,.29,.52]
        data=[]
        for i,row in enumerate(rows):
            cells=row.find_all(['th','td'],recursive=False)
            data.append([Paragraph(markup(cell),s['head' if i==0 else 'key' if j==0 else 'cell']) for j,cell in enumerate(cells)])
        t=Table(data,colWidths=[body_w*x for x in shares],repeatRows=1,splitByRow=1,hAlign='LEFT')
        t.setStyle(TableStyle([
          ('BACKGROUND',(0,0),(-1,0),teal),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,tint]),
          ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
          ('TOPPADDING',(0,0),(-1,-1),4 if n==2 else 6),('BOTTOMPADDING',(0,0),(-1,-1),4 if n==2 else 6),
          ('LINEBELOW',(0,0),(-1,0),.6,teal),('LINEBELOW',(0,1),(-1,-1),.25,rule)]))
        return KeepTogether([t]) if headers[0] in ('Motive','Orientation','Faculty') else t

    class PlanDoc(SimpleDocTemplate):
        def afterFlowable(self,flowable):
            if hasattr(flowable,'bookmark'):
                self.canv.bookmarkPage(flowable.bookmark)
                self.canv.addOutlineEntry(flowable.getPlainText(),flowable.bookmark,flowable.outline_level,False)

    def page_chrome(c,doc):
        if doc.page==1:return
        c.saveState();c.setStrokeColor(rule);c.setLineWidth(.5)
        c.line(left,page_h-38,page_w-right,page_h-38)
        c.setFont('Georgia-Bold',7.3);c.setFillColor(teal)
        c.drawString(left,page_h-31,'THE HUMAN POSSIBILITY')
        c.drawRightString(page_w-right,page_h-31,'BOOK PLAN')
        c.setFont('Georgia',7.3);c.setFillColor(muted)
        c.drawString(left,34,'Madhyasth Darshan - plain-English primer')
        c.drawRightString(page_w-right,34,f'{doc.page} / {doc.total_pages}' if doc.total_pages else str(doc.page))
        c.restoreState()

    raw=source.read_text(encoding='utf-8')
    pdf_raw=(raw.replace('§§','Sections ').replace('§','Section ').replace('—',' - ').replace('–',' - ').replace('\u2011','-').replace('’',"'").replace('“','"').replace('”','"'))
    soup=BeautifulSoup(markdown.markdown(pdf_raw,extensions=['tables']),'html.parser')
    if soup.find('h1') is None:
        raise ValueError('The plan must begin with a Markdown title (one #).')
    title=soup.find('h1').get_text(' ',strip=True)
    subtitles=[x.get_text(' ',strip=True) for x in soup.find('h1').find_next_siblings('p',limit=2)]
    revised=next((p for p in soup.find_all('p') if p.get_text().startswith('Plan revised:')),None)
    if len(subtitles)<2 or revised is None:
        raise ValueError('The plan needs two subtitle paragraphs and a Plan revised: field.')

    def build_story():
        story=[Spacer(1,139),Paragraph('BOOK PLAN',s['kicker']),Spacer(1,22),
           Paragraph(escape(title),s['title']),Spacer(1,24),
           Paragraph(escape(subtitles[0]),s['subtitle']),Spacer(1,20),
           Paragraph(escape(subtitles[1]),s['subtitle']),Spacer(1,38),
           Paragraph('A proposed accessible introduction to Madhyasth Darshan',s['detail']),Spacer(1,12),
           Paragraph('For interested adults and older teenagers,<br/>with no prior background in philosophy',s['detail']),Spacer(1,12),
           Paragraph('Twenty short chapters | working length: 40,000-50,000 words',s['detail']),Spacer(1,20),
           Paragraph(markup(revised),s['detail']),PageBreak()]
        started=False;section='';toc=1;heading_keys=set()
        for node in soup.contents:
            if not isinstance(node,Tag):continue
            if node.name=='h2':
                started=True
                if section.startswith('Opening page - Babaji and his wish'):story.append(PageBreak())
                section=re.sub(r'\s+',' ',node.get_text(' ',strip=True))
            if not started:continue
            is_portrait=section.startswith('Opening page - Babaji and his wish')
            is_song=section.startswith('Final page - Gratitude')
            if node.name in ('h2','h3','h4'):
                if node.name=='h2' and (is_portrait or is_song):story.extend([PageBreak(),Spacer(1,13)])
                kind='sample_heading' if is_portrait or is_song else 'h2' if node.name=='h2' else 'part' if section=='Table of contents' else 'h3'
                h=Paragraph(markup(node),s[kind])
                key=re.sub(r'[^\w\s-]','',node.get_text(' ',strip=True).lower()).strip().replace(' ','-')
                while key in heading_keys:key+='-'
                heading_keys.add(key)
                h.bookmark=key;h.outline_level=int(node.name[1])-2
                story.append(h)
            elif is_portrait:
                if node.name=='p' and node.find('img'):
                    asset=source.parent/node.find('img')['src']
                    from PIL import Image as PILImage
                    im=PILImage.open(asset);buf=BytesIO();im.save(buf,format='PNG');buf.seek(0)
                    story.append(Image(buf,width=90*mm,height=90*mm*im.height/im.width))
                elif node.name=='blockquote':
                    for paragraph in node.find_all('p',recursive=False):
                        text=paragraph.get_text('\n',strip=True)
                        if re.search('[\u0900-\u097f]',text):
                            lines=[x.strip() for x in paragraph.get_text().strip().splitlines() if x.strip()]
                            story.extend(ActualTextParagraph(x,s['wish']) for x in lines)
                        else:story.append(Paragraph(markup(paragraph).strip().replace('\n','<br/>'),s['wish_en']))
                elif node.name=='p':
                    text=node.get_text(' ',strip=True)
                    sty='portrait_name' if text=='Shri A. Nagraj' else 'portrait_italic' if text.startswith('Whom I') else 'portrait_label' if text=='His wish for humanity' else 'credit'
                    story.append(Paragraph(markup(node),s[sty]))
                elif node.name=='ul':
                    for item in node.find_all('li',recursive=False):story.append(Paragraph('- '+markup(item),s['credit']))
                else:raise ValueError(f'Unsupported portrait element {node.name}')
            elif is_song:
                if node.name=='p':story.append(ActualTextParagraph(node.get_text(' ',strip=True),s['song_title']))
                elif node.name=='blockquote':
                    for paragraph in node.find_all('p',recursive=False):
                        lines=[x.strip() for x in paragraph.get_text().strip().splitlines() if x.strip()]
                        story.extend(ActualTextParagraph(x,s['song']) for x in lines)
                        story.append(Spacer(1,16))
                else:raise ValueError(f'Unsupported song element {node.name}')
            elif node.name=='p':story.append(Paragraph(markup(node),s['guiding' if node.get_text().startswith('Guiding question:') else 'intro' if section=='Book proposal' else 'body']))
            elif node.name in ('ol','ul'):
                items=node.find_all('li',recursive=False);start=toc if section=='Table of contents' and node.name=='ol' else int(node.get('start',1))
                for i,item in enumerate(items,start):story.append(Paragraph(escape(f'{i}. ' if node.name=='ol' else '- ')+markup(item),s['toc']))
                if section=='Table of contents' and node.name=='ol':toc+=len(items)
                story.append(Spacer(1,3))
            elif node.name=='table':story.extend([Spacer(1,3),make_table(node),Spacer(1,11)])
            elif node.name=='blockquote':story.append(Paragraph(markup(node),s['body']))
            else:raise ValueError(f'Unsupported Markdown element: {node.name}')
        return story

    def build(target,total=None):
        doc=PlanDoc(target,pagesize=A4,leftMargin=left,rightMargin=right,topMargin=57,bottomMargin=56,
            title=title,author='Analytic Madhyasth Darshan',subject='Madhyasth Darshan primer book plan',
            pageCompression=1,invariant=1)
        doc.total_pages=total
        doc.build(build_story(),onFirstPage=page_chrome,onLaterPages=page_chrome)
        return doc.page

    total = build(BytesIO())
    buffer = BytesIO()
    actual = build(buffer, total)
    if actual != total:
        raise RuntimeError(f'Pagination changed between passes: {total} to {actual}')
    pdf_bytes = buffer.getvalue()
    record = {
        'source': str(source),
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'pdf_sha256': hashlib.sha256(pdf_bytes).hexdigest(),
        'pages': actual,
        'format': 'A4',
        'reportlab_version': __import__('reportlab').Version,
    }
    return pdf_bytes, record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE,
                        help='Plan Markdown (default: adjacent plan source).')
    parser.add_argument('--output', type=Path,
                        help='PDF destination (default: <source-stem>-revised.pdf).')
    parser.add_argument('--font-dir', type=Path, default=DEFAULT_FONT_DIR,
                        help='Directory containing Georgia and Mangal font files.')
    parser.add_argument('--vendor', type=Path,
                        help='Explicit directory containing installed Python packages.')
    parser.add_argument('--report', type=Path,
                        help='Optional JSON build report; also printed to stdout.')
    parser.add_argument('--check', action='store_true',
                        help='Render and validate in memory without writing the PDF or report.')
    args = parser.parse_args(argv)
    source = args.source.resolve()
    output = args.output.resolve() if args.output else source.with_name(source.stem + '-revised.pdf')
    report = args.report.resolve() if args.report else None
    if output == source or report in (source, output):
        parser.error('The source, output PDF and optional report must have distinct paths.')
    if args.vendor:
        vendor = args.vendor.resolve()
        if not vendor.is_dir():
            parser.error(f'Package directory not found: {vendor}')
        sys.path.insert(0, str(vendor))
    try:
        pdf_bytes, record = render_plan(source, args.font_dir)
    except ImportError as exc:
        parser.exit(1, f'Missing renderer dependency: {exc}. Install reportlab>=4.5.1, '
                    'uharfbuzz, markdown, beautifulsoup4 and Pillow.\n')
    except (FileNotFoundError, ValueError) as exc:
        parser.exit(1, f'Cannot render Primer plan: {exc}\n')
    record['pdf'] = str(output)
    if not args.check:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(pdf_bytes)
        if report:
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(record, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""Render the standalone Primer manuscript as a 6 x 9 inch book.

Dependencies: reportlab>=4.5.1, uharfbuzz, markdown, beautifulsoup4, pillow,
svglib. Fonts default to Windows Georgia and Mangal; --font-dir can point
to another directory containing those six font files. --vendor optionally
adds a directory of already installed Python packages (for HarfBuzz).

Run from the repository root: python Primer/build_primer_pdf.py
This is separate from the Studies/Applications publication pipeline.
"""

from pathlib import Path
from io import BytesIO
from html import escape
import argparse
import hashlib
import json
import re
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).with_name('madhyasth-darshan-primer.md'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--font-dir', type=Path, default=Path('C:/Windows/Fonts'))
    parser.add_argument('--vendor', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.vendor:
        sys.path.insert(0, str(args.vendor.resolve()))

    import uharfbuzz  # Required for correctly shaped Devanagari.
    import markdown
    from bs4 import BeautifulSoup, NavigableString, Tag
    from PIL import Image as PILImage
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, PageBreak, Flowable,
        Image, Table, TableStyle, NextPageTemplate, KeepTogether,
    )
    from reportlab.platypus.tableofcontents import TableOfContents
    from svglib.svglib import svg2rlg

    source = args.source.resolve()
    output = args.output.resolve() if args.output else source.with_suffix('.pdf')
    output.parent.mkdir(parents=True, exist_ok=True)
    for name, file in [('Georgia','georgia.ttf'), ('Georgia-Bold','georgiab.ttf'),
                       ('Georgia-Italic','georgiai.ttf'), ('Georgia-BoldItalic','georgiaz.ttf'),
                       ('Mangal','mangal.ttf'), ('Mangal-Bold','mangalb.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(args.font_dir/file), shapable=name.startswith('Mangal')))
    pdfmetrics.registerFontFamily('Georgia', normal='Georgia', bold='Georgia-Bold', italic='Georgia-Italic', boldItalic='Georgia-BoldItalic')
    pdfmetrics.registerFontFamily('Mangal', normal='Mangal', bold='Mangal-Bold', italic='Mangal', boldItalic='Mangal-Bold')
    width, height = 6*inch, 9*inch
    margin = 18*mm
    body_width = width-2*margin
    ink, teal, muted = [colors.HexColor(x) for x in ('#20343b','#276774','#617078')]
    pale, rule = [colors.HexColor(x) for x in ('#edf4f2','#c7d6d7')]

    def sty(name, **kw):
        base = dict(fontName='Georgia', fontSize=10.5, leading=15.2,
                    textColor=ink, spaceAfter=8, allowWidows=0, allowOrphans=0)
        base.update(kw)
        return ParagraphStyle(name, **base)

    styles = {
        'body': sty('body', alignment=TA_JUSTIFY),
        'h2': sty('h2', fontName='Georgia-Bold', fontSize=22, leading=28, spaceBefore=10, spaceAfter=22, keepWithNext=True),
        'h3': sty('h3', fontName='Georgia-Bold', fontSize=12.3, leading=17, textColor=teal, spaceBefore=14, spaceAfter=7, keepWithNext=True),
        'h4': sty('h4', fontName='Georgia-Bold', fontSize=10.5, leading=15, spaceBefore=10, spaceAfter=5, keepWithNext=True),
        'part': sty('part', fontName='Georgia-Bold', fontSize=11.5, leading=17, textColor=teal, spaceBefore=15, spaceAfter=15, keepWithNext=True),
        'title': sty('title', fontName='Georgia-Bold', fontSize=31, leading=39, alignment=TA_CENTER, spaceAfter=27),
        'subtitle': sty('subtitle', fontName='Georgia-Italic', fontSize=13, leading=20, alignment=TA_CENTER, spaceAfter=19),
        'detail': sty('detail', fontSize=9, leading=14, alignment=TA_CENTER, textColor=muted),
        'list': sty('list', leftIndent=13, firstLineIndent=-10, spaceAfter=6),
        'caption': sty('caption', fontName='Georgia-Italic', fontSize=8.7, leading=12, textColor=muted, spaceAfter=13),
        'cell': sty('cell', fontSize=8.1, leading=11.3, spaceAfter=0),
        'thead': sty('thead', fontName='Georgia-Bold', fontSize=8.1, leading=11.3, spaceAfter=0, textColor=colors.white),
        'note': sty('note', fontSize=9.2, leading=13.3, spaceAfter=8),
        'name': sty('name', fontName='Georgia-Bold', fontSize=20, leading=25, alignment=TA_CENTER, spaceBefore=14, spaceAfter=5),
        'portrait_detail': sty('portrait_detail', fontSize=9, leading=14, alignment=TA_CENTER, textColor=muted, spaceAfter=3),
        'wishlabel': sty('wishlabel', fontName='Georgia-Bold', fontSize=12, leading=17, alignment=TA_CENTER, spaceBefore=8, spaceAfter=8),
        'wish': sty('wish', fontName='Mangal', fontSize=12.8, leading=23, alignment=TA_CENTER, shaping=True, spaceAfter=0),
        'wish_en': sty('wish_en', fontSize=9.5, leading=15, alignment=TA_CENTER, spaceBefore=10, spaceAfter=9),
        'credit': sty('credit', fontSize=7.2, leading=11, alignment=TA_CENTER, textColor=muted, spaceAfter=7),
        'song_title': sty('song_title', fontName='Mangal-Bold', fontSize=23, leading=32, alignment=TA_CENTER, shaping=True, spaceAfter=26),
        'song': sty('song', fontName='Mangal', fontSize=10.4, leading=23, alignment=TA_CENTER, shaping=True, spaceAfter=0),
    }

    def slug(text):
        return re.sub(r'[^\w\s-]', '', text.lower()).strip().replace(' ', '-')

    def normal(text):
        return text.replace('\u2011','-').replace('—',' - ').replace('–','-')

    raw = source.read_text(encoding='utf-8')
    soup = BeautifulSoup(markdown.markdown(raw, extensions=['tables', 'toc']), 'html.parser')

    def inline(node):
        if isinstance(node, NavigableString):
            return escape(normal(str(node)))
        body = ''.join(inline(c) for c in node.children)
        if node.name in ('strong','b'): return f'<b>{body}</b>'
        if node.name in ('em','i'): return f'<i>{body}</i>'
        if node.name == 'br': return '<br/>'
        if node.name == 'code': return body
        if node.name == 'a':
            href = node.get('href','')
            if href.startswith(('https://','http://','mailto:','#')):
                return f'<link href="{escape(href, quote=True)}" color="#276774">{body}</link>'
            return body
        return body

    def markup(node):
        value = ''.join(inline(c) for c in node.children)
        return re.sub(r'\bChapter (\d+)', r'Chapter&#160;\1', value)

    class ActualTextParagraph(Paragraph):
        def __init__(self, text, style):
            self.actual_text = text
            super().__init__(escape(text), style)

        def draw(self):
            encoded = 'FEFF'+self.actual_text.encode('utf-16-be').hex().upper()
            self.canv._code.append('/Span << /ActualText <'+encoded+'> >> BDC')
            super().draw()
            self.canv._code.append('EMC')

    class HiddenBookmark(Flowable):
        def __init__(self, title, key, toc_level=None):
            super().__init__()
            self.title, self.bookmark, self.outline_level = title, key, 0
            if toc_level is not None: self.toc_level = toc_level
        def getPlainText(self): return self.title
        def draw(self): pass

    def chrome(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(muted)
        canvas.setFont('Georgia',7)
        canvas.drawString(margin,height-31,'THE HUMAN POSSIBILITY')
        canvas.drawRightString(width-margin,height-31,'FIRST DRAFT')
        canvas.drawCentredString(width/2,27,str(doc.page))
        canvas.restoreState()

    class BookDoc(BaseDocTemplate):
        def afterFlowable(self, flowable):
            if not hasattr(flowable, 'bookmark'): return
            title = flowable.getPlainText()
            self.canv.bookmarkPage(flowable.bookmark)
            self.canv.addOutlineEntry(title, flowable.bookmark, flowable.outline_level, False)
            if hasattr(flowable, 'toc_level'):
                self.notify('TOCEntry', (flowable.toc_level,title,self.page,flowable.bookmark))

    doc = BookDoc(str(output),pagesize=(width,height),leftMargin=margin,rightMargin=margin,
                  topMargin=47,bottomMargin=45,title='The Human Possibility',
                  author='Analytic Madhyasth Darshan',subject='A first-draft introduction to Madhyasth Darshan',
                  pageCompression=1, invariant=1)
    frame = lambda: Frame(margin,45,body_width,height-92,id='body',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id='quiet',frames=[frame()]), PageTemplate(id='body',frames=[frame()],onPage=chrome)])

    story = []
    current = 'title'
    section = ''
    is_notes = False
    is_credits = False
    part_pending = False
    title_seen = False
    question_list = False
    used_keys = set()
    toc = TableOfContents()
    toc.levelStyles = [sty('toc0',fontName='Georgia-Bold',fontSize=10.2,leading=15,spaceBefore=11,spaceAfter=3,leftIndent=0),
                       sty('toc1',fontSize=9.7,leading=14,spaceBefore=2,spaceAfter=3,leftIndent=9)]

    def heading(node, kind, level=0, toc_level=None):
        key = node.get('id') or slug(node.get_text(' ',strip=True))
        while key in used_keys: key += '-'
        used_keys.add(key)
        p = Paragraph(markup(node),styles[kind])
        p.bookmark, p.outline_level = key, level
        if toc_level is not None: p.toc_level = toc_level
        return p

    def table(node):
        rows = node.find_all('tr')
        count = len(rows[0].find_all(['td','th'],recursive=False))
        fractions = {2:[.33,.67],3:[.18,.49,.33],4:[.20,.23,.27,.30],5:[.15,.20,.20,.25,.20]}.get(count,[1/count]*count)
        header = rows[0].get_text(' ',strip=True)
        if 'Faculty' in header: fractions=[.18,.23,.59]
        if 'Established' in header and count==3: fractions=[.28,.28,.44]
        if header.startswith('Established') and count==2: fractions=[.48,.52]
        if header.startswith('Value family') and count==3: fractions=[.24,.12,.64]
        if header.startswith('Category') and count==3: fractions=[.25,.375,.375]
        if header.startswith('Level') and count==3: fractions=[.12,.43,.45]
        def cell_markup(cell):
            return (markup(cell).replace('Plant/biological','Plant/ biological')
                    .replace('Human/knowledge','Human/ knowledge')
                    .replace('putreshana-vitteshana-lokeshana','putreshana - vitteshana - lokeshana'))
        data = [[Paragraph(cell_markup(c),styles['thead' if i==0 else 'cell'])
                 for c in row.find_all(['td','th'],recursive=False)] for i,row in enumerate(rows)]
        result = Table(data,colWidths=[body_width*f for f in fractions],repeatRows=1,hAlign='LEFT',
                       rowSplitRange=(2,-2) if len(data)>5 else None)
        result.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),teal),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,pale]),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('LINEBELOW',(0,1),(-1,-1),.25,rule),
        ]))
        if header.startswith(('Level','Council level','Order')):
            _, table_height = result.wrap(body_width, height-92)
            if table_height < height-112:
                return KeepTogether([result])
        return result

    for node in soup.contents:
        if not isinstance(node,Tag): continue
        txt = node.get_text(' ',strip=True)
        if node.name == 'h1' and not title_seen:
            title_seen = True
            story.extend([Spacer(1,95),Paragraph(markup(node),styles['title'])])
            continue
        if node.name == 'h1':
            current='body';part_pending=True
            story.extend([NextPageTemplate('body'),PageBreak(),heading(node,'part',0,0)])
            continue
        if node.name == 'h2':
            section=txt
            if txt.startswith('Babaji and His Wish'):
                current='portrait';story.extend([PageBreak(),HiddenBookmark('Babaji and His Wish for Humanity','babaji'),Spacer(1,5)])
                continue
            if txt == 'वंदना':
                current='song'
                story.extend([NextPageTemplate('quiet'),PageBreak(),HiddenBookmark('Vandana','vandana',0),Spacer(1,46),ActualTextParagraph(txt,styles['song_title'])])
                continue
            if txt=='Contents':
                current='contents';story.extend([PageBreak(),Paragraph('Contents',styles['h2']),toc]);continue
            current='body'
            if txt.startswith('Sources and Further'): is_notes=True
            if txt.startswith('Acknowledgements'):
                is_notes=False
                is_credits=True
            if not part_pending:
                story.extend([NextPageTemplate('body'),PageBreak()])
            chapter = bool(re.match(r'^\d+\.',txt))
            story.append(heading(node,'h2',1 if chapter else 0,1 if chapter else None if txt.startswith('Preface') else 0))
            part_pending=False
            continue
        if current == 'contents': continue
        if current == 'title':
            if node.name=='p':story.append(Paragraph(markup(node),styles['detail' if node.find('strong') else 'subtitle']))
            continue
        if current == 'portrait':
            if node.name=='p' and node.find('img'):
                im = PILImage.open(source.parent/node.find('img')['src'])
                stream = BytesIO();im.save(stream,format='PNG');stream.seek(0)
                story.append(Image(stream,width=90*mm,height=90*mm*im.height/im.width))
            elif node.name=='blockquote':
                for p in node.find_all('p',recursive=False):
                    if re.search('[\u0900-\u097f]',p.get_text()):
                        story.extend(ActualTextParagraph(line.strip(),styles['wish']) for line in p.get_text().splitlines() if line.strip())
                    else:story.append(Paragraph(markup(p).replace('\n','<br/>'),styles['wish_en']))
            elif node.name=='p':
                name='name' if txt=='Shri A. Nagraj' else 'wishlabel' if txt=='His wish for humanity' else 'portrait_detail' if txt.startswith('Whom I') else 'credit'
                story.append(Paragraph(markup(node),styles[name]))
            continue
        if current == 'song':
            if node.name=='blockquote':
                for p in node.find_all('p',recursive=False):
                    story.extend(ActualTextParagraph(line.strip(),styles['song']) for line in p.get_text().splitlines() if line.strip())
                    story.append(Spacer(1,17))
            continue
        if node.name in ('h3','h4','h5'):
            kind='h3' if node.name=='h3' else 'h4'
            p=Paragraph(markup(node),styles[kind])
            if is_notes and re.match(r'^Chapter \d+',txt):
                p=heading(node,kind,1)
            story.append(p)
        elif node.name=='p' and node.find('img'):
            asset=source.parent/node.find('img')['src']
            if asset.suffix.lower()=='.svg':
                drawing=svg2rlg(str(asset))
                scale=min(body_width/drawing.width,420/drawing.height)
                drawing.scale(scale,scale);drawing.width*=scale;drawing.height*=scale
                drawing.hAlign='CENTER'
                story.extend([Spacer(1,9),drawing,Spacer(1,9)])
            else:
                im=PILImage.open(asset)
                story.append(Image(str(asset),width=body_width,height=body_width*im.height/im.width))
        elif node.name=='p':
            kind='caption' if txt.startswith('Figure ') else 'note' if is_notes or is_credits else 'body'
            p=Paragraph(markup(node),styles[kind])
            if txt=='Questions to sit with':
                p.keepWithNext=True
                question_list=True
            story.append(p)
        elif node.name in ('ul','ol'):
            items=node.find_all('li',recursive=False)
            start=int(node.get('start',1))
            for i,item in enumerate(items,start):
                prefix=f'{i}. ' if node.name=='ol' else '• '
                p=Paragraph(prefix+markup(item),styles['note' if is_notes else 'list'])
                if question_list and i<start+len(items)-1:p.keepWithNext=True
                story.append(p)
            question_list=False
        elif node.name=='table':story.extend([Spacer(1,4),table(node),Spacer(1,12)])
        elif node.name=='blockquote':story.append(Paragraph(markup(node),styles['note' if is_notes else 'body']))
        elif node.name in ('hr','a'):continue
        else:raise ValueError(f'Unsupported manuscript element {node.name}')

    doc.multiBuild(story,maxPasses=8)
    record = dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  pdf=str(output),pdf_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),pages=doc.page,
                  format='6 x 9 inches',reportlab_version=__import__('reportlab').Version)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(record,indent=2))


if __name__=='__main__':
    main()

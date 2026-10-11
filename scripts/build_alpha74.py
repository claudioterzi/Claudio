"""Canonical Alpha 74: vector print layout and small, derived web assets.

The paintings are generated separately. This script lays out the print document,
then renders the explicitly requested web editions from that same document.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path

import fitz
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[1]
AXES = ('nord', 'est', 'sud', 'ovest')
ANGLES = (0, -90, -180, -270)  # PDF coordinates are y-up.
GOLD = HexColor('#d8b976')
INK = HexColor('#0c1116')
CREAM = HexColor('#fff1cf')
PRINT_IMAGES = {}

pdfmetrics.registerFont(TTFont('AlphaSerif', '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'))
pdfmetrics.registerFont(TTFont('AlphaSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))


def wrap(text, font, size, widths):
    words = text.split()
    lines = []
    while words:
        width = widths[min(len(lines), len(widths)-1)]
        line = words.pop(0)
        while words and pdfmetrics.stringWidth(line+' '+words[0], font, size) <= width:
            line += ' '+words.pop(0)
        lines.append(line)
    return lines


def symbol(c, glyph, x, y, size):
    c.saveState()
    c.translate(x, y)
    c.setFillColor(GOLD)
    c.setStrokeColor(GOLD)
    c.setLineWidth(size/19)
    if glyph == '⟁':
        for scale in (1, .52):
            p = c.beginPath()
            p.moveTo(0, size*.48*scale)
            p.lineTo(-size*.45*scale, -size*.32*scale)
            p.lineTo(size*.45*scale, -size*.32*scale)
            p.close()
            c.drawPath(p, stroke=1, fill=0)
    elif glyph == '⤴':
        p = c.beginPath()
        p.moveTo(-size*.45, -size*.3)
        p.curveTo(size*.3, -size*.3, size*.3, -size*.3, size*.3, size*.4)
        c.drawPath(p, stroke=1)
        c.lines([(size*.3, size*.4, size*.08, size*.18), (size*.3, size*.4, size*.5, size*.18)])
    else:
        c.setFont('AlphaSans', size)
        c.drawCentredString(0, -size*.32, '?' if glyph == '？' else glyph)
    c.restoreState()


def face(c, card, polarity, image_path, x, y, side, audit):
    c.saveState()
    c.translate(x, y)
    c.setFillColor(INK)
    c.rect(0, 0, side, side, stroke=0, fill=1)
    # PDF clipping places each original panel without rewriting the source art.
    c.saveState()
    p = c.beginPath()
    p.rect(0, 0, side, side)
    c.clipPath(p, stroke=0)
    if image_path not in PRINT_IMAGES:
        buffer=io.BytesIO()
        with Image.open(image_path) as original:
            original.convert('RGB').save(buffer,'JPEG',quality=90,subsampling=2)
        buffer.seek(0)
        PRINT_IMAGES[image_path]=ImageReader(buffer)
    c.drawImage(PRINT_IMAGES[image_path], 0 if polarity == 'luce' else -side, 0,
                width=side*2, height=side, mask='auto')
    c.restoreState()
    # Equal bands on all four edges remove a privileged reading orientation.
    for axis, angle in zip(AXES, ANGLES):
        c.saveState()
        c.translate(side/2, side/2)
        c.rotate(angle)
        c.translate(-side/2, -side/2)
        c.setFillColor(INK)
        c.setFillAlpha(.85)
        p = c.beginPath()
        p.moveTo(0, side)
        p.lineTo(side, side)
        p.lineTo(side-23*mm, side-23*mm)
        p.lineTo(23*mm, side-23*mm)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
        c.setFillAlpha(1)
        c.setFillColor(GOLD)
        c.setFont('AlphaSans', 6.4)
        c.drawCentredString(side/2, side-5.2*mm, axis.upper()+'  ·  '+polarity.upper())
        name_size = min(10.4, (side-35*mm)/max(1,pdfmetrics.stringWidth(card['nome'], 'AlphaSerif', 1)))
        c.setFont('AlphaSerif', name_size)
        c.drawCentredString(side/2, side-10.6*mm, card['nome'])
        meaning = card[polarity][axis]
        text = meaning[0].upper()+meaning[1:]
        font_size = 9.1
        widths = (side-38*mm, side-46*mm)
        lines = wrap(text, 'AlphaSerif', font_size, widths)
        assert len(lines) <= 2, (card['id'], polarity, axis, lines)
        c.setFillColor(CREAM)
        c.setFont('AlphaSerif', font_size)
        for line_index, line in enumerate(lines):
            c.drawCentredString(side/2, side-(16.1+4.3*line_index)*mm, line)
        audit.append({'id':card['id'], 'polarita':polarity, 'asse':axis,
                      'meaning':meaning, 'pdf_rotation':angle,
                      'font_pt':font_size, 'lines':lines})
        c.restoreState()
    c.setStrokeColor(GOLD)
    c.setLineWidth(.32*mm)
    c.rect(1.7*mm, 1.7*mm, side-3.4*mm, side-3.4*mm, stroke=1, fill=0)
    c.setLineWidth(.19*mm)
    c.line(0,0,side,side)
    c.line(0,side,side,0)
    c.setFillColor(INK)
    radius=10*mm
    c.circle(side/2,side/2,radius,fill=1,stroke=1)
    symbol(c,card['simbolo'],side/2,side/2+1.4*mm,16)
    c.setFont('Times-Italic',6.3)
    c.setFillColor(GOLD)
    c.drawCentredString(side/2,side/2-5.5*mm,'C.Terzi')
    c.restoreState()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--partial',action='store_true')
    parser.add_argument('--art-manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    canonical_path=REPO/'tarocchi_quantici_alpha.json'
    canonical=json.loads(canonical_path.read_text())
    cards=canonical['carte']
    paths=json.loads(args.art_manifest.read_text())
    selected=[c for c in cards if str(c['id']) in paths]
    if not args.partial:
        assert len(selected)==74, f'Only {len(selected)} of 74 artworks'
    out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    web=REPO/'public/images/alpha74'
    web.mkdir(parents=True,exist_ok=True)
    side=120*mm
    audit=[]
    file=out/('Alpha74_Campione.pdf' if args.partial else 'Alpha74_Mazzo_120mm.pdf')
    c=canvas.Canvas(str(file),pagesize=(side,side),pageCompression=1)
    c.setTitle('Canone Alpha 74 - Carte quadrate 120 mm')
    c.setAuthor('Claudio Terzi - C.Terzi')
    resolutions=[]
    for card in selected:
        with Image.open(paths[str(card['id'])]) as im:
            w,h=im.size
            assert abs(w/h-2)<.025, (card['id'],w,h)
            resolutions.append({'id':card['id'],'source_px':[w,h],'face_ppi_at_120mm':round(min(w/2,h)/120*25.4,1)})
        for polarity in ('luce','ombra'):
            face(c,card,polarity,paths[str(card['id'])],0,0,side,audit)
            c.showPage()
    c.save()
    doc=fitz.open(file)
    if not args.partial:
        sheets=fitz.open()
        for pair in range(0,len(selected),2):
            for polarity_index in (0,1):
                sheet=sheets.new_page(width=210*mm,height=297*mm)
                sheet.insert_text((20*mm,12*mm),'ALPHA 74  |  120 x 120 mm  |  Claudio Terzi',fontsize=8)
                for row in (0,1):
                    index=pair+row
                    if index>=len(selected): continue
                    target=fitz.Rect(45*mm,(20+132*row)*mm,165*mm,(140+132*row)*mm)
                    sheet.show_pdf_page(target,doc,2*index+polarity_index)
                    for px in (target.x0,target.x1):
                        for py in (target.y0,target.y1):
                            sx=-1 if px==target.x0 else 1
                            sy=-1 if py==target.y0 else 1
                            sheet.draw_line((px+sx*mm,py),(px+sx*4*mm,py),width=.3)
                            sheet.draw_line((px,py+sy*mm),(px,py+sy*4*mm),width=.3)
                sheet.insert_text((20*mm,288*mm),'Scala 100% - fronte/retro sul lato lungo - 2 carte per foglio',fontsize=7)
        sheets.save(out/'Alpha74_A4_fronte_retro.pdf',garbage=4,deflate=True)
    asset_report=[]
    for i,card in enumerate(selected):
        folder=web/f"{card['id']:02d}"
        folder.mkdir(exist_ok=True)
        for j,polarity in enumerate(('luce','ombra')):
            page=doc[2*i+j]
            for size,quality in ((160,64),(640,79)):
                pix=page.get_pixmap(matrix=fitz.Matrix(size/side,size/side),alpha=False)
                image=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
                path=folder/f'{polarity}-{size}.webp'
                encoded=io.BytesIO()
                image.save(encoded,'WEBP',quality=quality,method=4)
                data=encoded.getvalue()
                assert len(data)>100 and data[:4]==b'RIFF', ('WebP export failed',card['id'],polarity,size)
                with Image.open(io.BytesIO(data)) as check:
                    check.load()
                    assert check.size==(size,size), (card['id'],check.size)
                path.write_bytes(data)
                asset_report.append({'id':card['id'],'polarita':polarity,'px':size,'bytes':path.stat().st_size,
                                     'path':str(path.relative_to(REPO/'public'))})
    # Separate small contact catalog, never loaded by the web reader.
    catalog=fitz.open()
    for offset in range(0,len(selected),4):
        page=catalog.new_page(width=297*mm,height=210*mm)
        page.draw_rect(page.rect,color=None,fill=(.035,.043,.055))
        page.insert_text((13*mm,12*mm),'CANONE ALPHA 74  |  Claudio Terzi',fontsize=11,color=(.84,.73,.47))
        for n,card in enumerate(selected[offset:offset+4]):
            row,col=divmod(n,2)
            x=(13+140*col)*mm
            y=(22+89*row)*mm
            page.insert_text((x,y),f"{card['id']:02d}  {card['nome']}",fontsize=10,color=(.95,.92,.85))
            for j,polarity in enumerate(('luce','ombra')):
                target=fitz.Rect(x+j*64*mm,y+3*mm,x+(j*64+62)*mm,y+65*mm)
                preview=io.BytesIO()
                with Image.open(web/f"{card['id']:02d}"/f'{polarity}-640.webp') as im:
                    im.save(preview,'JPEG',quality=82)
                page.insert_image(target,stream=preview.getvalue())
    catalog.save(out/('Alpha74_Catalogo_campione.pdf' if args.partial else 'Alpha74_Catalogo.pdf'),garbage=4,deflate=True)
    report={'version':'alpha74-art-v1','cards':len(selected),'faces':len(selected)*2,'states':len(audit),
            'canonical_sha256':hashlib.sha256(canonical_path.read_bytes()).hexdigest(),
            'card_mm':[120,120],'master_pdf':file.name,'source_resolution':resolutions,
            'assets':asset_report,'vector_text':audit,
            'print_status':'Prova in scala reale, RGB, senza abbondanza. Non ancora esecutivo tipografico.',
            'art_direction_status':'Testi ruotati esattamente. Le scene pittoriche sono da revisione artistica.'}
    (out/'Alpha74_Verifica.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({'cards':len(selected),'faces':len(doc),'web_bytes':sum(a['bytes'] for a in asset_report),
                      'pdf_bytes':file.stat().st_size,'native_ppi':sorted(set(r['face_ppi_at_120mm'] for r in resolutions))}))
    doc[0].get_pixmap(matrix=fitz.Matrix(2,2)).save(str(out/'layout-proof.png'))


if __name__=='__main__': main()

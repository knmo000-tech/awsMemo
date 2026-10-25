"""Regenerate Web Functions sequence SVGs from the Mermaid source in Markdown.

Uses only the Python standard library. Supports the sequence notation used here;
raises on unsupported syntax instead of silently omitting a step.
"""
from pathlib import Path
from html import escape
import re
import unicodedata
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'AWSシーケンス図_WebFunctions.md'
BASE='AWSシーケンス図_WebFunctions'
WIDTH=2100
FONT='Noto Sans CJK JP, Hiragino Kaku Gothic ProN, Meiryo, sans-serif'

def units(t):
    return sum(1 if unicodedata.east_asian_width(c) in 'WFA' else .58 for c in t)

def wrap(t,width,size=22):
    rows=['']
    for c in t:
        if units(rows[-1]+c)*size>width and rows[-1]: rows.append('')
        rows[-1]+=c
    return rows

def text(x,y,t,size=22,anchor='start',color='#244b6e',bold=False):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}">{escape(t)}</text>'

def render(title,body):
    actors={}; events=[]
    for raw in body.splitlines():
        line=raw.strip()
        if not line or line in ('sequenceDiagram','autonumber'): continue
        p=re.fullmatch(r'participant (\w+) as (.+)',line)
        if p: actors[p[1]]=p[2];continue
        events.append(line)
    assert 1<len(actors)<=5
    ids=list(actors)
    xs={a:220+i*(WIDTH-440)/(len(ids)-1) for i,a in enumerate(ids)}
    y=210; elements=[]; frames=[]; stack=[]; count=0
    for line in events:
        m=re.fullmatch(r'(\w+)(->>|-->>)(\w+): (.+)',line)
        n=re.fullmatch(r'Note over (\w+)(?:,(\w+))?: (.+)',line)
        if m:
            a,kind,b,msg=m.groups(); assert a in xs and b in xs
            x1,x2=xs[a],xs[b]; count+=1
            selfcall=a==b
            available=abs(x2-x1)-80 if not selfcall else 300
            rows=wrap(f'{count}. {msg}',available)
            start=y+25
            tx=(x1+x2)/2 if not selfcall else x1+35
            for i,row in enumerate(rows): elements.append(text(tx,start+30*i,row,anchor='middle' if not selfcall else 'start'))
            ay=start+30*len(rows)-10
            dash=' stroke-dasharray="9 6"' if kind=='-->>' else ''
            color='#9274ae' if kind=='-->>' else '#427a9e'
            marker='reply' if kind=='-->>' else 'request'
            path=f'M{x1},{ay} H{x1+280} V{ay+35} H{x1}' if selfcall else f'M{x1},{ay} H{x2}'
            elements.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.5"{dash} marker-end="url(#{marker})"/>')
            y=ay+(75 if selfcall else 55)
        elif n:
            a,b,msg=n.groups(); b=b or a
            left=max(35,min(xs[a],xs[b])-160);right=min(WIDTH-35,max(xs[a],xs[b])+160)
            rows=wrap(msg,right-left-36,21); height=34+29*len(rows)
            elements.append(f'<rect x="{left}" y="{y}" width="{right-left}" height="{height}" rx="8" fill="#fff8df" stroke="#d7bc71"/>')
            for i,row in enumerate(rows): elements.append(text((left+right)/2,y+30+29*i,row,21,'middle','#68542b'))
            y+=height+28
        elif line.startswith(('alt ','opt ','loop ')):
            kind,label=line.split(' ',1);depth=len(stack)
            left=35+depth*18; y+=10
            stack.append((left,y,kind));rows=wrap(kind+'：'+label,WIDTH-2*left-40,21)
            elements.append(f'<rect x="{left}" y="{y}" width="{WIDTH-2*left}" height="{30*len(rows)+20}" fill="#e9f1f9"/>')
            for i,row in enumerate(rows):elements.append(text(left+16,y+29+30*i,row,21,bold=True))
            y+=30*len(rows)+42
        elif line.startswith('else '):
            assert stack
            left=stack[-1][0]
            elements.append(f'<path d="M{left},{y} H{WIDTH-left}" stroke="#a0b3c3" stroke-dasharray="7 5"/>')
            rows=wrap('else：'+line[5:],WIDTH-2*left-40,21)
            for i,row in enumerate(rows):elements.append(text(left+16,y+31+30*i,row,21,bold=True))
            y+=30*len(rows)+44
        elif line=='end':
            assert stack
            left,top,kind=stack.pop(); y+=5
            frames.append(f'<rect x="{left}" y="{top}" width="{WIDTH-2*left}" height="{y-top}" rx="4" fill="none" stroke="#9cb0c2" stroke-width="2"/>')
            y+=30
        else: raise ValueError('Unsupported sequence syntax: '+line)
    assert not stack
    bottom=y+10;height=bottom+100
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="title desc">',f'<title id="title">{escape(title)}</title>', '<desc id="desc">Web Functions案の処理順。青い実線は要求、紫の破線は応答。黄色枠は補足。採用未確定の設計提案を含む。</desc>', '<defs><marker id="request" viewBox="0 0 10 10" markerWidth="7" markerHeight="7" refX="9" refY="5" orient="auto"><path d="M0 0 L10 5 L0 10Z" fill="#427a9e"/></marker><marker id="reply" viewBox="0 0 10 10" markerWidth="7" markerHeight="7" refX="9" refY="5" orient="auto"><path d="M0 0 L10 5 L0 10Z" fill="#9274ae"/></marker></defs>',f'<rect width="{WIDTH}" height="{height}" fill="#fff"/>',f'<g font-family="{FONT}">',text(40,55,title,30,bold=True),text(40,94,'Web Functions構成・比較検証用  |  不透明トークン前提  |  SQS・Outbox等は提案  |  2026-10-26',20,color='#6b8195')]
    for a,name in actors.items():
        x=xs[a]
        out.append(f'<path d="M{x},180 V{bottom}" stroke="#9fb4c7" stroke-width="2" stroke-dasharray="7 6"/>')
        for by in (130,bottom):
            out.append(f'<rect x="{x-145}" y="{by}" width="290" height="52" rx="9" fill="#edf5fc" stroke="#83aac9" stroke-width="2"/>')
            out.append(text(x,by+34,name,23,'middle',bold=True))
    out+=elements+frames+[text(40,height-16,'青実線：要求  ／  紫破線：応答・通知  ／  黄枠：補足  |  詳細・未決事項は同名のMarkdownを参照',19,color='#6b8195'),'</g></svg>']
    svg='\n'.join(out)+'\n';ET.fromstring(svg)
    return svg,height

def main():
    source=SOURCE.read_text()
    blocks=list(re.finditer(r'```(?:mermaid|text)\n(sequenceDiagram.*?)```',source,re.S))
    assert len(blocks)==6
    names=['01_認証','02_受付','03_Outbox配送','04_生成','05_照会と取得','06_配送回復']
    panels=[]
    for i,m in enumerate(blocks):
        title=re.findall(r'^## (.+)$',source[:m.start()],re.M)[-1]
        svg,h=render(title,m[1]);filename=f'{BASE}_{names[i]}.svg'
        (ROOT/filename).write_text(svg)
        # Put nested SVGs into one overview with unique ids for accessibility/markers.
        panel=svg.replace('id="','id="p'+str(i)+'_').replace('url(#','url(#p'+str(i)+'_').replace('aria-labelledby="title desc"',f'aria-labelledby="p{i}_title p{i}_desc"')
        panels.append((panel,h))
    total=sum(h for _,h in panels)+40*(len(panels)-1)
    combined=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{total}" viewBox="0 0 {WIDTH} {total}">','<title>Web Functions案・全6シーケンス図</title>','<rect width="100%" height="100%" fill="#e5edf5"/>']
    y=0
    for panel,h in panels:
        combined.append(f'<g transform="translate(0,{y})">{panel}</g>');y+=h+40
    combined.append('</svg>');overview='\n'.join(combined)+'\n';ET.fromstring(overview)
    (ROOT/f'{BASE}.svg').write_text(overview)
    if '```mermaid' not in source:
        return
    for i in reversed(range(6)):
        m=blocks[i]; image=f'[{names[i][3:]}のSVGを開く]({BASE}_{names[i]}.svg)\n\n![{names[i][3:]}のシーケンス図]({BASE}_{names[i]}.svg)\n\n'
        # Keep Mermaid source editable without rendering the same diagram twice.
        source=source[:m.start()]+image+'<details>\n<summary>編集用Mermaidソース</summary>\n\n```text\n'+m[1]+'```\n\n</details>'+source[m.end():]
    source=source.replace('[構成図の読み方]',f'[全6図をまとめたSVG]({BASE}.svg) / [構成図の読み方]',1)
    (ROOT/'sequence-page.updated.md').write_text(source)
    print('Generated 6 individual SVGs and 1 overview; preserved all sequence messages and editable source.')

if __name__=='__main__': main()

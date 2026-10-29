"""Шаблон тузатишлари: 1-жадвал (корхона тури, ойлик диапазонлари) ва 1/5-жадвал свод формулалари."""
import os, re, tempfile
from .kcommon import Book, E, cval, colN


def fix_table1(f):
    B = Book(f, os.path.join(tempfile.mkdtemp(), 'w'))
    def setcell(s,ref,v=None,formula=None,sty=None):
        m=re.search(r'<c r="%s"([^>]*?)(/>|>.*?</c>)'%ref,s,re.S)
        if m and sty is None:
            sm=re.search(r' s="(\d+)"',m.group(1)); sty=sm.group(1) if sm else None
        new=(f'<c r="{ref}"'+(f' s="{sty}"' if sty else '')+f'><f>{E(formula)}</f></c>') if formula else cval(ref,v,sty)
        if m: return s[:m.start()]+new+s[m.end():]
        rn=int(re.search(r'\d+',ref).group(0)); col=re.match(r'[A-Z]+',ref).group(0)
        rm=re.search(r'<row r="%d"[^>]*>(.*?)</row>'%rn,s,re.S)
        body=rm.group(1); pos=None
        for mm in re.finditer(r'<c r="([A-Z]+)\d+"',body):
            if colN(mm.group(1))>colN(col): pos=mm.start(); break
        body=body[:pos]+new+body[pos:] if pos is not None else body+new
        return s[:rm.start(1)]+body+s[rm.end(1):]
    def sty(s,ref):
        m=re.search(r'<c r="%s"[^>]*? s="(\d+)"'%ref,s); return m.group(1) if m else None
    # list header
    p=B.path('Фуқаролар рўйхати'); s=B.rd(p)
    s=setcell(s,'V4','Корхона тури (автоматик)',sty=sty(s,'U4'))
    s=setcell(s,'V5',22,sty=sty(s,'U5'))
    B.wr(p,s)
    # svod (2)
    p=B.path('Туманлар кесимида (2)'); s=B.rd(p)
    L="'Фуқаролар рўйхати'!$%s$6:$%s$10005"
    def rg(c): return L%(c,c)
    for col,typ in (('N','МЧЖ/корхона'),('O','Фермер хўжалиги'),('P','ЯТТ')):
        st=sty(s,f'I7')
        for r in range(7,18):
            s=setcell(s,f'{col}{r}',formula=f'SUMIFS({rg("U")},{rg("B")},$Z{r},{rg("C")},$B{r},{rg("V")},"{typ}")',sty=sty(s,f'{col}{r}') or st)
        s=setcell(s,f'{col}6',formula=f'SUM({col}7:{col}17)',sty=sty(s,f'{col}6') or sty(s,'I6'))
    for r in range(7,18):
        base=f'{rg("B")},$Z{r},{rg("C")},$B{r}'
        s=setcell(s,f'J{r}',formula=f'COUNTIFS({base},{rg("P")},">0",{rg("P")},"<=3000000")')
        s=setcell(s,f'K{r}',formula=f'COUNTIFS({base},{rg("P")},">3000000",{rg("P")},"<=5000000")')
        s=setcell(s,f'L{r}',formula=f'COUNTIFS({base},{rg("P")},">5000000")')
        s=setcell(s,f'M{r}',formula=f'IFERROR(AVERAGEIFS({rg("P")},{base},{rg("P")},">0")/1000,0)')
    s=setcell(s,'M6',formula='IFERROR(AVERAGEIFS(M7:M17,M7:M17,">0"),0)')
    B.wr(p,s)
    # Республика
    p=B.path('Республика'); s=B.rd(p)
    ss=B.rd('xl/sharedStrings.xml'); SST=[''.join(re.findall(r'<t[^>]*>(.*?)</t>',x,flags=re.S)) for x in re.findall(r'<si>(.*?)</si>',ss,flags=re.S)]
    for rn in range(7,30):
        mm=re.search(r'<c r="B%d"[^>]*t="s"[^>]*><v>(\d+)</v>'%rn,s)
        lab=SST[int(mm.group(1))] if mm else ''
        if 'Сирдарё' in lab or lab.strip()=='Жами':
            for col in 'NOP':
                s=setcell(s,f'{col}{rn}',formula=f"'Туманлар кесимида (2)'!{col}6",sty=sty(s,f'{col}{rn}') or sty(s,f'M{rn}'))
    B.wr(p,s)
    B.save(f+'.tmp'); os.replace(f+'.tmp',f)


def fix15(f1, f5):
    """5-жадвал: тоифалар сводини Номма-ном дан COUNTIFS қилиш; 1-жадвал: #REF! ларни тузатиш."""
    B = Book(f5, os.path.join(tempfile.mkdtemp(), 'w'))
    p = B.path('Тоифалар кесимида')
    s = B.rd(p)
    for r in range(6, 17):
        for col, typ in (('D', 'ЯТТ'), ('E', 'МЧЖ'), ('F', 'Деҳқон хўжалиги')):
            frm = f"COUNTIFS('Номма-ном'!C:C,B{r},'Номма-ном'!J:J,\"{typ}\")"
            s = re.sub(r'<c r="' + col + str(r) + r'"([^>/]*?)(?:/>|>.*?</c>)',
                       lambda m: f'<c r="{col}{r}"' + re.sub(r' t="\w+"', '', m.group(1)) + f'><f>{E(frm)}</f></c>', s, count=1, flags=re.S)
    B.wr(p, s)
    B.save(f5 + '.tmp')
    os.replace(f5 + '.tmp', f5)
    B = Book(f1, os.path.join(tempfile.mkdtemp(), 'w'))
    p = B.path('Республика')
    s = B.rd(p)
    ss = B.rd('xl/sharedStrings.xml')
    SST = [''.join(re.findall(r'<t[^>]*>(.*?)</t>', x, flags=re.S)) for x in re.findall(r'<si>(.*?)</si>', ss, flags=re.S)]

    def fixrow(m):
        rn, attrs, cells = m.group(1), m.group(2), m.group(3)
        mm = re.search(r'<c r="B' + rn + r'"[^>]*t="s"[^>]*><v>(\d+)</v>', cells)
        lab = SST[int(mm.group(1))] if mm else ''

        def fc(cm):
            col = cm.group(1)
            if 'Сирдарё' in lab or lab.strip() == 'Жами':
                return f'<c r="{col}{rn}"{cm.group(2)}><f>{E(chr(39) + "Туманлар кесимида (2)" + chr(39) + "!" + col + "6")}</f></c>'
            return f'<c r="{col}{rn}"{cm.group(2)}><v>0</v></c>'
        cells = re.sub(r'<c r="([A-Z]+)' + rn + r'"([^>/]*?)(?: t="e")?><f>#REF!</f>(?:<v>[^<]*</v>)?</c>', fc, cells)
        return f'<row r="{rn}"{attrs}>{cells}</row>'
    s = re.sub(r'<row r="(\d+)"([^>]*)>(.*?)</row>', fixrow, s, flags=re.S)
    B.wr(p, s)
    B.save(f1 + '.tmp')
    os.replace(f1 + '.tmp', f1)

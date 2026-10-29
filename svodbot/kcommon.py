import re, os, shutil, zipfile, datetime, pickle
from xml.sax.saxutils import escape as E
import openpyxl

DISTRICTS = [  # template name, code, latin, cyr-long variants
    ('Оқолтин т.', 1, 'Oqoltin tumani', ['Оқолтин тумани']),
    ('Боёвут т.', 2, 'Boyovut tumani', ['Боёвут тумани']),
    ('Гулистон т.', 3, 'Guliston tumani', ['Гулистон тумани']),
    ('Мирзаобод т.', 5, 'Mirzaobod tumani', ['Мирзаобод тумани']),
    ('Сайхунобод т.', 6, 'Sayxunobod tumani', ['Сайхунобод тумани']),
    ('Сирдарё т.', 7, 'Sirdaryo tumani', ['Сирдарё тумани']),
    ('Ховос т.', 8, 'Xovos tumani', ['Ховос тумани']),
    ('Сардоба т.', 9, 'Sardoba tumani', ['Сардоба тумани']),
    ('Гулистон ш.', 10, 'Guliston shahar', ['Гулистон шаҳар', 'Гулистон шаҳри']),
    ('Ширин ш.', 12, 'Shirin shahar', ['Ширин шаҳар', 'Ширин шаҳри']),
    ('Янгиер ш.', 13, 'Yangier shahar', ['Янгиер шаҳар', 'Янгиер шаҳри']),
]
def alias_rows():
    out = []
    for d, c, lat, cyr in DISTRICTS:
        names = [d] + cyr + [lat, lat.replace(' tumani', ' t.').replace(' shahar', ' sh.'), c, str(c), 2400 + c, str(2400 + c)]
        for n in names: out.append((n, d))
    return out

def colL(i):
    s = ''; i += 1
    while i: i, r = divmod(i - 1, 26); s = chr(65 + r) + s
    return s
def colN(L):
    n = 0
    for ch in L: n = n * 26 + ord(ch) - 64
    return n
def cval(ref, v, sty=None):
    st = f' s="{sty}"' if sty is not None else ''
    if v is None or v == '': return ''
    if isinstance(v, bool): v = int(v)
    if isinstance(v, (int, float)):
        if isinstance(v, float) and v.is_integer() and abs(v) < 1e15: v = int(v)
        return f'<c r="{ref}"{st}><v>{v}</v></c>'
    if isinstance(v, (datetime.datetime, datetime.date)):
        return cval(ref, v.strftime('%d.%m.%Y'), sty)
    return f'<c r="{ref}"{st} t="inlineStr"><is><t xml:space="preserve">{E(str(v))}</t></is></c>'
def sheet_xml(rows_xml, widths=None, freeze=None):
    cols = ''.join(f'<col min="{i+1}" max="{i+1}" width="{w}" customWidth="1"/>' for i, w in enumerate(widths or []))
    pane = f'<pane ySplit="{freeze-1}" topLeftCell="A{freeze}" activePane="bottomLeft" state="frozen"/>' if freeze else ''
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<sheetViews><sheetView workbookViewId="0">{pane}</sheetView></sheetViews><sheetFormatPr defaultRowHeight="15"/>'
            + (f'<cols>{cols}</cols>' if cols else '') + '<sheetData>' + rows_xml + '</sheetData></worksheet>')
def table_rows(rows):
    out = []
    for i, r in enumerate(rows):
        cells = ''.join(cval(f'{colL(j)}{i+1}', v) for j, v in enumerate(r))
        if cells: out.append(f'<row r="{i+1}">{cells}</row>')
    return ''.join(out)
def read_rows(path, sheet=None):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet] if sheet else wb.worksheets[0]
    return [list(r) for r in ws.iter_rows(values_only=True)]

class Book:
    def __init__(self, src, work):
        shutil.rmtree(work, ignore_errors=True)
        with zipfile.ZipFile(src) as z:
            z.extractall(work); self.order = [i.filename for i in z.infolist()]
        self.W = work
        wb = self.rd('xl/workbook.xml'); rels = self.rd('xl/_rels/workbook.xml.rels')
        rid2t = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels)) | {a: b for b, a in re.findall(r'Target="([^"]+)"[^>]*Id="(rId\d+)"', rels)}
        self.sheets = {E(n) if False else n: 'xl/' + rid2t[r] for n, r in re.findall(r'<sheet name="([^"]+)" sheetId="\d+" r:id="(rId\d+)"/>', wb)}
        self.new = []
    def rd(self, p): return open(os.path.join(self.W, p), encoding='utf-8').read()
    def wr(self, p, s): open(os.path.join(self.W, p), 'w', encoding='utf-8').write(s)
    def path(self, name): return self.sheets[name]
    def add_sheet(self, name, xml):
        n = len(self.new)
        fn = f'xl/worksheets/zsrc{n+1}.xml'
        self.wr(fn, xml); self.new.append((name, fn))
    def save(self, out, names=None):
        wbx = self.rd('xl/workbook.xml'); rels = self.rd('xl/_rels/workbook.xml.rels'); ct = self.rd('[Content_Types].xml')
        ids = [int(x) for x in re.findall(r'sheetId="(\d+)"', wbx)]
        addS = addR = addC = ''
        for k, (name, fn) in enumerate(self.new):
            rid = f'rId{100+k}'
            addS += f'<sheet name="{E(name)}" sheetId="{max(ids)+1+k}" r:id="{rid}"/>'
            addR += f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="{fn[3:]}"/>'
            addC += f'<Override PartName="/{fn}" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        wbx = wbx.replace('</sheets>', addS + '</sheets>')
        wbx = re.sub(r'<calcPr([^>]*?)/>', lambda m: '<calcPr' + re.sub(r' fullCalcOnLoad="\d"', '', m.group(1)) + ' fullCalcOnLoad="1"/>', wbx)
        if names:
            dn = ''.join(f'<definedName name="{k}">{E(v)}</definedName>' for k, v in names)
            wbx = wbx.replace('</definedNames>', dn + '</definedNames>') if '</definedNames>' in wbx else wbx.replace('</sheets>', '</sheets><definedNames>' + dn + '</definedNames>', 1)
        rels = re.sub(r'<Relationship Id="rId\d+" Type="[^"]*/calcChain" Target="calcChain.xml"/>', '', rels).replace('</Relationships>', addR + '</Relationships>')
        ct = ct.replace('<Override PartName="/xl/calcChain.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.calcChain+xml"/>', '').replace('</Types>', addC + '</Types>')
        self.wr('xl/workbook.xml', wbx); self.wr('xl/_rels/workbook.xml.rels', rels); self.wr('[Content_Types].xml', ct)
        cc = os.path.join(self.W, 'xl/calcChain.xml')
        if os.path.exists(cc): os.remove(cc)
        order = [p for p in self.order if p != 'xl/calcChain.xml'] + [fn for _, fn in self.new]
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
            for p in order: z.write(os.path.join(self.W, p), p)

def add_list_cols(s7, tables, hdr_style, body_style):
    """tables: list of (startcol letter, header list, rows list) -> append cells to rows of Рўйхатлар xml"""
    add = {}
    for start, hdr, rows in tables:
        c0 = colN(start)
        add.setdefault(1, []).extend((c0 + j, cval(f'{colL(c0+j-1)}1', h, hdr_style)) for j, h in enumerate(hdr))
        for i, row in enumerate(rows):
            add.setdefault(i + 2, []).extend((c0 + j, cval(f'{colL(c0+j-1)}{i+2}', v, body_style)) for j, v in enumerate(row))
    def addrow(m):
        r = int(m.group(1)); attrs = re.sub(r' spans="[^"]*"', '', m.group(2))
        extra = ''.join(x for _, x in sorted(add.pop(r, [])))
        return f'<row r="{r}"{attrs}>{m.group(3)}{extra}</row>'
    s7 = re.sub(r'<row r="(\d+)"([^>]*)>(.*?)</row>', addrow, s7, flags=re.S)
    extra = ''.join(f'<row r="{r}">{"".join(x for _, x in sorted(v))}</row>' for r, v in sorted(add.items()))
    s7 = s7.replace('</sheetData>', extra + '</sheetData>')
    s7 = re.sub(r'<dimension ref="[^"]*"/>', '', s7)
    return s7

def rebuild_rows(sx, first, last, formula_for, helpers):
    """Rewrite rows first..last of a sheet xml: keep each existing cell's style; formula_for(col, r) -> formula or None (keep original cell)."""
    head, rest = sx.split('<sheetData>'); body, tail = rest.split('</sheetData>')
    rows = re.findall(r'<row r="(\d+)"([^>]*)>(.*?)</row>', body, flags=re.S)
    out = []
    for rn, attrs, cells in rows:
        r = int(rn)
        if r < first or r > last:
            out.append(f'<row r="{rn}"{attrs}>{cells}</row>'); continue
        attrs = re.sub(r' spans="[^"]*"', '', attrs)
        newc = []
        for m in re.finditer(r'<c r="([A-Z]+)(\d+)"([^>]*?)(/>|>(.*?)</c>)', cells, flags=re.S):
            col, a = m.group(1), m.group(3)
            f = formula_for(col, r)
            if f is None: newc.append(m.group(0)); continue
            a = re.sub(r' t="\w+"', '', a)
            newc.append(f'<c r="{col}{r}"{a}><f>{E(f)}</f></c>')
        for col in helpers:
            newc.append(f'<c r="{col}{r}"><f>{E(formula_for(col, r))}</f></c>')
        out.append(f'<row r="{rn}"{attrs}>{"".join(newc)}</row>')
    return head + '<sheetData>' + ''.join(out) + '</sheetData>' + tail

CATLIST = '{"Ишсизлар","Тадбиркорлик ташаббуси борлар","Даромади паст фуқаролар","Норасмийлар","Ишлаш истаги йўқлар"}'
def xatlov_helpers(r):
    V = f'IF($H{r}="","",IFERROR(MATCH(--$H{r},Хатлов!$G:$G,0),""))'
    W = (f'IF($V{r}="","",IF(INDEX(Хатлов!$H:$H,$V{r})<>"",INDEX(Хатлов!$H:$H,$V{r}),'
         f'IFERROR(INDEX(Хатлов!$H:$H,$V{r}+MATCH(--$H{r},INDEX(Хатлов!$G:$G,$V{r}+1):Хатлов!$G$1048576,0)),"")))')
    J = (f'IF($H{r}="","",IFERROR(CHOOSE(MATCH($W{r},{CATLIST},0),Рўйхатлар!$C$2,Рўйхатлар!$C$3,Рўйхатлар!$C$4,Рўйхатлар!$C$5,Рўйхатлар!$C$6),"Хатловда тоифаси йўқ"))')
    return V, W, J
def todate(x):
    return f'IFERROR(IF(ISNUMBER({x}),{x},DATE(RIGHT({x},4),MID({x},4,2),LEFT({x},2))),"")'

def xatlov_sheet(allrows):
    out = ['<row r="1">' + cval('A1', 'Хонадон хатлови: хатлов файлидаги «Лист1» варағининг A:H устунларини шу варақнинг A1 катагига қўйинг (фильтрни олдин ўчиринг).') + '</row>',
           '<row r="3">' + ''.join(cval(f'{colL(j)}3', allrows[0][j]) for j in range(8)) + '</row>']
    data = [r for r in allrows[1:] if any(v not in (None, '') for v in r[1:8])]
    for i, r in enumerate(data):
        rr = i + 4
        vals = [i + 1] + list(r[1:8])
        out.append(f'<row r="{rr}">' + ''.join(cval(f'{colL(j)}{rr}', vals[j]) for j in range(8)) + '</row>')
    return sheet_xml(''.join(out), [9, 16, 24, 26, 28, 40, 17, 30], freeze=4)

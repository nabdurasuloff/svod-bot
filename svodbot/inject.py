"""LibreOffice hisoblagan qiymatlarni asl fayldagi formulalarga kesh sifatida yozadi
(asl fayl ko'rinishi/ma'lumot tekshiruvlari saqlanadi)."""
import zipfile, re, openpyxl
from xml.sax.saxutils import escape as E

SKIP = {'Тўлдириш намунаси', 'Рўйхатлар', 'Йўриқнома'}


def inject(src, calc, out):
    wbv = openpyxl.load_workbook(calc, data_only=True, read_only=True)
    zin = zipfile.ZipFile(src)
    wbx = zin.read('xl/workbook.xml').decode()
    rels = zin.read('xl/_rels/workbook.xml.rels').decode()
    rid = {a: b for a, b in re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels)}
    rid.update({b: a for a, b in re.findall(r'Target="([^"]+)"[^>]*Id="(rId\d+)"', rels)})
    targets = {}
    for name, r in re.findall(r'<sheet\b[^>]*?name="([^"]+)"[^>]*?r:id="(rId\d+)"', wbx):
        name = name.replace('&amp;', '&')
        if name in SKIP:
            continue
        targets['xl/' + rid[r].lstrip('/').replace('xl/', '')] = name
    zout = zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED)
    n = 0
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename in targets:
            ws = wbv[targets[item.filename]]
            vals = {}
            for row in ws.iter_rows():
                for c in row:
                    if c.value is not None:
                        vals[c.coordinate] = c.value
            s = data.decode()

            def rep(m):
                nonlocal n
                ref, attrs, f = m.group(1), m.group(2), m.group(3)
                v = vals.get(ref)
                if '[' in f:
                    return m.group(0)
                attrs = re.sub(r' t="\w+"', '', attrs)
                if v is None:
                    return f'<c r="{ref}"{attrs}>{f}</c>'
                n += 1
                if isinstance(v, bool):
                    return f'<c r="{ref}"{attrs} t="b">{f}<v>{int(v)}</v></c>'
                if isinstance(v, (int, float)):
                    return f'<c r="{ref}"{attrs}>{f}<v>{v}</v></c>'
                return f'<c r="{ref}"{attrs} t="str">{f}<v>{E(str(v))}</v></c>'
            s = re.sub(r'<c r="([A-Z]+\d+)"([^>/]*)>(<f\b[^>]*?/>|<f\b(?:[^>]*[^/])?>.*?</f>)(?:<v>.*?</v>|<v\s*/>)?</c>',
                       rep, s, flags=re.S)
            data = s.encode()
        zout.writestr(item, data)
    zout.close()
    return n

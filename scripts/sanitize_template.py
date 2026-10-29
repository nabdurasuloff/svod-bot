"""Шаблон ичидаги ишлатилмаётган (қолиб кетган) матнларни тозалайди — шахсий маълумот қолмаслиги учун."""
import zipfile, re, sys, shutil

def _sheet_files(zin):
    wb = zin.read('xl/workbook.xml').decode()
    rels = zin.read('xl/_rels/workbook.xml.rels').decode()
    rid = {a: b for a, b in re.findall(r'Id="(rId\d+)"[^>]*Target="([^"]+)"', rels)}
    rid.update({b: a for a, b in re.findall(r'Target="([^"]+)"[^>]*Id="(rId\d+)"', rels)})
    return {n: 'xl/' + rid[r].lstrip('/').replace('xl/', '') for n, r in re.findall(r'<sheet name="([^"]+)" sheetId="\d+" r:id="(rId\d+)"', wb)}


def _clean_list(xml):
    # 6-қатордан бошлаб формуласиз катакларни бўшатади (стиль қолади)
    def row(m):
        if int(m.group(1)) < 6:
            return m.group(0)
        body = re.sub(r'<c r="([A-Z]+\d+)"([^>/]*?)(?: t="\w+")?(?:/>|>(?!<f).*?</c>)',
                      lambda c: f'<c r="{c.group(1)}"' + re.sub(r' t="\w+"', '', c.group(2)) + '/>', m.group(3), flags=re.S)
        return f'<row r="{m.group(1)}"{m.group(2)}>{body}</row>'
    return re.sub(r'<row r="(\d+)"([^>]*)>(.*?)</row>', row, xml, flags=re.S)


def _clean_nn(xml):
    xml = re.sub(r'<row r="(\d+)"[^>]*/>', lambda m: m.group(0) if int(m.group(1)) < 4 else '', xml)
    return re.sub(r'<row r="(\d+)"[^>]*>.*?</row>', lambda m: m.group(0) if int(m.group(1)) < 4 else '', xml, flags=re.S)


def sanitize(path):
    zin = zipfile.ZipFile(path)
    sf = _sheet_files(zin)
    patch = {}
    if 'Фуқаролар рўйхати' in sf:
        patch[sf['Фуқаролар рўйхати']] = _clean_list
    if 'Номма-ном' in sf:
        patch[sf['Номма-ном']] = _clean_nn
    cleaned = {k: f(zin.read(k).decode('utf8')) for k, f in patch.items()}
    used = set()
    for n in zin.namelist():
        if n.startswith('xl/worksheets/') and n.endswith('.xml'):
            t = cleaned.get(n) or zin.read(n).decode('utf8', 'ignore')
            for m in re.finditer(r'<c\b[^>]*\bt="s"[^>]*>(?:<f>.*?</f>)?<v>(\d+)</v>', t, flags=re.S):
                used.add(int(m.group(1)))
    out = path + '.tmp'
    zout = zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED)
    removed = 0
    for it in zin.infolist():
        data = zin.read(it.filename)
        if it.filename == 'xl/sharedStrings.xml':
            s = data.decode('utf8')
            sis = list(re.finditer(r'<si>.*?</si>', s, flags=re.S))
            parts, last = [], 0
            for i, m in enumerate(sis):
                parts.append(s[last:m.start()])
                if i in used:
                    parts.append(m.group(0))
                else:
                    parts.append('<si><t></t></si>'); removed += 1
                last = m.end()
            parts.append(s[last:])
            data = ''.join(parts).encode('utf8')
        if it.filename in cleaned:
            data = cleaned[it.filename].encode('utf8')
        zout.writestr(it, data)
    zout.close(); shutil.move(out, path)
    return removed

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(p, sanitize(p))

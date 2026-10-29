"""6 та жадвални шаблонларга (assets/t1..t6.xlsx) тўлдириш."""
import os, re, sys, datetime, collections, tempfile, pickle
from xml.sax.saxutils import escape as E
from .kcommon import Book, cval, colN, DISTRICTS
from .sect1 import sect1, etype
from . import sector6

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), 'assets')

K2NAME = {'Боёвут т.': 'Боёвут', 'Гулистон т.': 'Гулистон тумани', 'Мирзаобод т.': 'Мирзаобод', 'Оқолтин т.': 'Оқолтин',
          'Сайхунобод т.': 'Сайхунобод', 'Сардоба т.': 'Сардоба', 'Сирдарё т.': 'Сирдарё тумани', 'Ховос т.': 'Ховос',
          'Гулистон ш.': 'Гулистон шаҳри', 'Ширин ш.': 'Ширин шаҳри', 'Янгиер ш.': 'Янгиер шаҳри'}
PMAP = {'оилавий тадбиркорлик': 'ОТРД', 'Оилавий тадбиркорлик': 'ОТРД', 'Маҳалла лойихаси': 'Маҳалла лойихаси',
        'оилавий': 'ОТРД', 'Оилавий': 'ОТРД', 'маҳалла лойихаси': 'Маҳалла лойихаси', 'махалла лойихаси': 'Маҳалла лойихаси',
        'Бизнесга биринчи қадам': 'Бизнесга биринчи қадам', 'ПҚ-312': 'ПҚ-312', 'МЛ': 'Маҳалла лойихаси',
        'ббқ': 'Бизнесга биринчи қадам', 'ББҚ': 'Бизнесга биринчи қадам'}
BANK = {'Агро банк': 'Агробанк', 'Асакабанк': 'Асака банк', 'Бизнесни ривожлантириш банки': 'Бизнесни ривожлантириш банк'}
SEASON_START = 46023   # 01.01.2026


def P(x):
    return str(int(x)).zfill(14) if isinstance(x, float) else str(x).strip()


def num(x):
    if x in (None, ''):
        return None
    try:
        return int(float(x)) if float(x).is_integer() else float(x)
    except Exception:
        return x


def cat(s):
    s = str(s)
    if s.startswith('Ишсиз'):
        return 'Ишсиз'
    return {'Тадбиркорлик ташаббуси борлар': 'Тадбиркорлик ташаббуси бор', 'Даромади паст фуқаролар': 'Ишлайди, лекин даромади паст',
            'Норасмийлар': 'Норасмий бандлар', 'Ишлаш истаги йўқлар': 'Ишлаш истаги йўқ'}.get(s, s)


def flagged(d, k):
    return str(d.get(k)).split('.')[0] == '1'


class Filler:
    def __init__(self, rows, ref, date, outdir):
        self.R, self.ref, self.date, self.out = rows, ref, date, outdir
        self.stat = collections.Counter()
        self.DMAP = {}
        for d, c, lat, cyr in DISTRICTS:
            for n in [d] + cyr:
                self.DMAP[n] = (d, c)
        res, _miss, _gm = pickle.load(open(os.path.join(ASSETS, 'mfy.pkl'), 'rb'))
        self.MFY = {(d, str(m).strip().lower()): int(code) for d, m, lat, code, _ in res}
        norm = lambda s: re.sub(r'\s+(мфй|маҳалла|махалла)$', '', str(s).strip().lower())
        self.norm = norm
        self.MFY2 = {(d, norm(m)): c for (d, m), c in self.MFY.items()}
        self.SRC = f'Омбор китоби {date}.2026, тоифа 21.10 хатловдан (Фуқаролар кесимида)'
        self.WCAT = {'Тадбиркорлик ташаббуси бор': 'Тадбир-корлик ташаббуси бор'}
        self.tmp = tempfile.mkdtemp(prefix='fill_')

    # ---------- umumiy
    def base(self, d):
        dn, dc = self.DMAP.get(str(d.get(2)).strip(), (str(d.get(2)).strip(), None))
        mf = str(d.get(4, '')).strip()
        code = self.MFY.get((dn, mf.lower())) or self.MFY2.get((dn, self.norm(mf)))
        return dn, dc, mf, code

    def xcat(self, d):
        return cat(self.ref['cat21'].get(P(d[7]), d.get(9)))

    def common(self, d):
        dn, dc, mf, code = self.base(d)
        if code is None:
            self.stat['mfy_miss'] += 1
        return {'B': 'Сирдарё', 'C': dn, 'D': dc, 'E': mf, 'F': code, 'G': d.get(6), 'H': P(d[7]), 'J': self.xcat(d), 'I': None}

    @staticmethod
    def cellpatch(rowxml, r, vals):
        for col, v in vals.items():
            pat = re.compile(r'<c r="' + col + str(r) + r'"([^>/]*?)(/>|>.*?</c>)', re.S)
            m = pat.search(rowxml)
            if v in (None, ''):
                if m:
                    sm = re.search(r' s="(\d+)"', m.group(1))
                    st = f' s="{sm.group(1)}"' if sm else ''
                    rowxml = rowxml[:m.start()] + f'<c r="{col}{r}"{st}/>' + rowxml[m.end():]
                continue
            sty = None
            if m:
                sm = re.search(r' s="(\d+)"', m.group(1))
                sty = sm.group(1) if sm else None
                rowxml = rowxml[:m.start()] + cval(f'{col}{r}', v, sty) + rowxml[m.end():]
            else:
                new = cval(f'{col}{r}', v, None)
                pos = None
                for mm in re.finditer(r'<c r="([A-Z]+)\d+"', rowxml):
                    if colN(mm.group(1)) > colN(col):
                        pos = mm.start()
                        break
                rowxml = rowxml[:pos] + new + rowxml[pos:] if pos is not None else rowxml + new
        return rowxml

    def fill_list(self, tpl, out, sel, mapper, first=6):
        B = Book(os.path.join(ASSETS, tpl), os.path.join(self.tmp, 'w_' + tpl))
        p = B.path('Фуқаролар рўйхати')
        sx = B.rd(p)
        data = [mapper(d) for d in self.R if sel(d)]

        def rep(m):
            r = int(m.group(1))
            i = r - first
            if 0 <= i < len(data):
                return f'<row r="{r}"{m.group(2)}>' + self.cellpatch(m.group(3), r, data[i]) + '</row>'
            if i >= len(data) and data:
                return f'<row r="{r}"{m.group(2)}>' + self.cellpatch(m.group(3), r, {k: None for k in data[0]}) + '</row>'
            return m.group(0)
        sx = re.sub(r'<row r="(\d+)"([^>]*)>(.*?)</row>', rep, sx, flags=re.S)
        B.wr(p, sx)
        B.save(out)
        return len(data)

    def fill_nn(self, tpl, out, items, DATECOLS=()):
        B = Book(os.path.join(ASSETS, tpl), os.path.join(self.tmp, 'n_' + tpl))
        p = B.path('Номма-ном')
        sx = B.rd(p)
        rows = []
        for i, v in enumerate(items):
            r = 4 + i
            cells = cval(f'A{r}', i + 1) + ''.join(cval(f'{c}{r}', v.get(c), 9 if c in DATECOLS else None) for c in 'BCDEFGHIJKLMNOPQRSTUVW')
            rows.append(f'<row r="{r}">{cells}</row>')
        sx = re.sub(r'<row r="([4-9]|\d{2,})"[^>]*/>', '', sx)
        sx = re.sub(r'<row r="([4-9]|\d{2,})"[^>]*>.*?</row>', '', sx, flags=re.S)
        sx = sx.replace('</sheetData>', ''.join(rows) + '</sheetData>') if '</sheetData>' in sx else sx.replace('<sheetData/>', '<sheetData>' + ''.join(rows) + '</sheetData>')
        sx = re.sub(r'<dimension ref="[^"]*"/>', '', sx)
        B.wr(p, sx)
        B.save(out)
        return len(items)

    def nn_base(self, d):
        dn, dc, mf, code = self.base(d)
        return {'B': 'Сирдарё', 'C': K2NAME.get(dn, dn), 'D': mf, 'E': d.get(6), 'F': P(d[7]),
                'T': f'Омбор китоби {self.date}', 'W': self.WCAT.get(self.xcat(d), self.xcat(d))}

    def regf(self, v, col, bcol):
        x = self.ref['reg'].get(v['F'])
        v[col] = 'Ҳа' if x else 'Йўқ'
        if x and x[0] is not None and hasattr(x[0], 'year'):
            v[bcol] = (x[0] - datetime.datetime(1899, 12, 30)).days
        self.stat['reg_' + v[col]] += 1

    # ---------- 6 jadval
    def run(self):
        date, OUT = self.date, self.out
        f = lambda n: os.path.join(OUT, n.replace('{d}', date) + '.xlsx')
        counts = {}
        SRC = self.SRC

        def m1(d):
            v = self.common(d)
            v.update({'L': d.get(12), 'M': num(d.get(13)), 'N': sect1(d.get(12), d.get(14)), 'V': etype(d.get(12)), 'O': d.get(14), 'R': SRC})
            return v

        def m3(d):
            v = self.common(d)
            v.update({'L': BANK.get(str(d.get(19)).strip(), d.get(19)), 'N': PMAP.get(str(d.get(20)).strip(), 'Бошқалар'),
                      'P': num(d.get(21)) or None, 'T': SRC})
            return v

        def m4(d):
            v = self.common(d)
            v.update({'Q': SRC})
            return v

        act = self.ref['act']

        def m6(d):
            v = self.common(d)
            a = d.get(28) or act.get(P(d[7]))
            s = sector6.sec(a) if a else 'Бошқа'
            v.update({'L': s, 'M': a, 'O': SRC + ('; фаолият тури аввалги Омбордан' if (a and not d.get(28)) else '')})
            return v
        counts[1] = self.fill_list('t1.xlsx', f('1_Доимий_ишга_жойлаштирилди_{d}'), lambda d: flagged(d, 30), m1)
        counts[3] = self.fill_list('t3.xlsx', f('3_Кредит_ажратилди_{d}'), lambda d: flagged(d, 32), m3)
        counts[4] = self.fill_list('t4.xlsx', f('4_Касб_хунарга_ўқитиш_{d}'), lambda d: flagged(d, 33), m4)
        counts[6] = self.fill_list('t6.xlsx', f('6_Ўзини_ўзи_банд_{d}'), lambda d: flagged(d, 37), m6)
        # 2 va 5 — nomma-nom
        it2 = []
        for d in self.R:
            if flagged(d, 31):
                v = self.nn_base(d)
                t = str(d.get(15))
                v.update({'J': 'Ссуда' if 'ссуда' in t.lower() else 'Субсидия', 'K': t, 'M': (num(d.get(18)) or 0) / 1e6 if d.get(18) else None,
                          'O': d.get(16), 'V': d.get(17)})
                self.regf(v, 'P', 'G')
                it2.append(v)
        for v in it2:
            v.update({'L': SEASON_START, 'V': (str(v.get('V') or '') + '; сана манбада йўқ — мавсум боши қўйилди').strip('; ')})
        counts[2] = self.fill_nn('t2.xlsx', f('2_Субсидия_ссуда_{d}'), it2, ('L', 'G'))
        it5 = []
        for d in self.R:
            if flagged(d, 34):
                v = self.nn_base(d)
                v.update({'J': 'ЯТТ'})
                self.regf(v, 'O', 'G')
                it5.append(v)
            if flagged(d, 36):
                v = self.nn_base(d)
                v.update({'J': 'Деҳқон хўжалиги', 'L': d.get(26), 'S': num(d.get(27))})
                self.regf(v, 'O', 'G')
                it5.append(v)
        self.WCAT.clear()
        for v in it5:
            v['W'] = 'Тадбиркорлик ташаббуси бор' if v['W'] == 'Тадбир-корлик ташаббуси бор' else v['W']
            v.update({'M': SEASON_START, 'V': 'сана манбада йўқ — мавсум боши қўйилди'})
        counts[5] = self.fill_nn('t5.xlsx', f('5_ЯТТ_МЧЖ_Деҳқон_{d}'), it5, ('M', 'G'))
        files = {1: f('1_Доимий_ишга_жойлаштирилди_{d}'), 2: f('2_Субсидия_ссуда_{d}'), 3: f('3_Кредит_ажратилди_{d}'),
                 4: f('4_Касб_хунарга_ўқитиш_{d}'), 5: f('5_ЯТТ_МЧЖ_Деҳқон_{d}'), 6: f('6_Ўзини_ўзи_банд_{d}')}
        return files, counts, self.stat

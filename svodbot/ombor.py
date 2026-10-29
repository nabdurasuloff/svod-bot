"""«Омбор китоби» файлини ўқиш. Устунлар сарлавҳа матни бўйича аниқланади,
шунинг учун устун жойлашуви ўзгарса ҳам ишлайди."""
import re, openpyxl

# ички калит -> (сарлавҳа матни, неччинчи учраши)   (калитлар аввалги скриптлар билан бир хил)
FIELDS = {
    0: ('№', 1),
    2: ('Туман (шаҳар) номи', 1),
    4: ('МФЙ номи', 1),
    6: ('Фуқаронинг Ф.И.Ш.', 1),
    7: ('ЖШШИР (ПИНФЛ)', 1),
    9: ('Хатловдаги тоифаси', 1),
    12: ('Иш берувчи ташкилот номи', 1),
    13: ('Ташкилот СТИРи', 1),
    14: ('Лавозими', 1),
    15: ('Тури (субсидия / ссуда)', 1),
    16: ('Ажратган орган / жамғарма', 1),
    17: ('Мақсади', 1),
    18: ('суммаси', 1),
    19: ('Банк номи', 1),
    20: ('Кредит дастури номи', 1),
    21: ('Кредит суммаси (сўм)', 1),
    22: ('Касб (мутахассислик)', 1),
    23: ('Фаолият тури', 1),        # ЯТТ (сана)
    24: ('МЧЖ номи', 1),
    25: ('МЧЖ СТИРи', 1),
    26: ('Хўжалик СТИРи', 1),
    27: ('Ер майдони (га)', 1),
    28: ('Фаолият тури', 2),        # ўзини ўзи банд
    29: ('Сони', 1),
    30: ('Доимий ишга жойлаштирилди', 1),
    31: ('Субсидия, ссуда ажратилди', 1),
    32: ('Кредит ажратилди', 1),
    33: ('Касб-ҳунарга ўқитишга жалб қилинди', 1),
    34: ('ЯТТ ташкил этди', 1),
    35: ('МЧЖ ташкил этди', 1),
    36: ('Деҳқон хўжалиги ташкил этди', 1),
    37: ('Ўзини ўзи банд қилинди', 1),
}
REQUIRED = (2, 4, 6, 7, 9)


def _norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip().lower()


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def find_layout(ws):
    """Сарлавҳа қаторини топиб, {калит: устун индекси} қайтаради."""
    for ri, row in enumerate(ws.iter_rows(min_row=1, max_row=12, values_only=True), start=1):
        labels = [_norm(v) for v in row]
        if _norm('ЖШШИР (ПИНФЛ)') in labels and _norm('Фуқаронинг Ф.И.Ш.') in labels:
            lay = {}
            for key, (lab, nth) in FIELDS.items():
                idx = [i for i, l in enumerate(labels) if l == _norm(lab)]
                if len(idx) >= nth:
                    lay[key] = idx[nth - 1]
            miss = [FIELDS[k][0] for k in REQUIRED if k not in lay]
            if miss:
                raise ValueError('Керакли устунлар топилмади: ' + ', '.join(miss))
            return ri, lay
    raise ValueError('Сарлавҳа қатори топилмади — бу «Омбор китоби» (Фуқаролар кесимида) файлими?')


def sheet_of(wb):
    for n in wb.sheetnames:
        if 'Фуқаролар кесимида' in n:
            return wb[n]
    raise ValueError('«Фуқаролар кесимида» варағи топилмади')


def read_rows(path):
    """Қайтаради: (rows, info). rows — {калит: қиймат} лотинлар рўйхати (ЖШШИР бор қаторлар)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = sheet_of(wb)
    hdr, lay = find_layout(ws)
    inv = {i: k for k, i in lay.items()}
    rows = []
    derived = 0
    first_data = hdr + 2   # сарлавҳадан кейин рақамлар қатори
    for ri, r in enumerate(ws.iter_rows(min_row=first_data, values_only=True), start=first_data):
        d = {}
        for i, v in enumerate(r):
            k = inv.get(i)
            if k is None or v in (None, ''):
                continue
            if isinstance(v, str) and v.startswith('='):
                continue
            if v == 0 and k < 29:
                continue
            d[k] = v
        if not d.get(7):
            continue
        # белги устунларида кэш қиймат бўлмаса — асосий майдонлардан ҳисоблаймиз
        def flag(k, cond):
            nonlocal derived
            if d.get(k) is None and k in lay:
                if cond:
                    d[k] = 1
                    derived += 1
        flag(30, d.get(12) or d.get(13))
        flag(31, _num(d.get(18)) and d.get(18) > 0)
        flag(32, _num(d.get(21)) and d.get(21) > 0)
        flag(35, d.get(25))
        flag(36, d.get(26))
        flag(33, d.get(22))
        flag(34, d.get(23))
        flag(37, d.get(28) or d.get(29))
        rows.append(d)
    return rows, {'layout': lay, 'header_row': hdr, 'derived_flags': derived}

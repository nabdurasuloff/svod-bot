import os, re, shutil, tempfile, datetime, concurrent.futures as cf
from . import ombor, lo
from .tables import Filler, P, PMAP
from .fixes import fix15, fix_table1
from .inject import inject
from . import refs


def guess_date(filename='', caption=''):
    for s in (caption or '', filename or ''):
        m = re.search(r'(\d{1,2})[._\- ](\d{1,2})[._\- ](20\d\d)', s) or re.search(r'(\d{1,2})[._](\d{1,2})\b', s)
        if m:
            return f'{int(m.group(1)):02d}.{int(m.group(2)):02d}'
    t = datetime.datetime.utcnow() + datetime.timedelta(hours=5)
    return t.strftime('%d.%m')


def _finish(src, dst):
    """src: тўлдирилган шаблон. Қайта ҳисоблаб, кэш қийматларини dst га ёзади."""
    tmp = src + '.calc.xlsx'
    shutil.copy(src, tmp)
    lo.recalc(tmp)
    inject(src, tmp, dst)
    os.remove(tmp)


def run(ombor_path, outdir, date, ref=None, log=print):
    ref = ref or refs.load()
    os.makedirs(outdir, exist_ok=True)
    log('Омбор файли ўқилмоқда…')
    rows, info = ombor.read_rows(ombor_path)
    log(f'{len(rows)} та қатор ўқилди')
    work = tempfile.mkdtemp(prefix='svod_')
    flr = Filler(rows, ref, date, work)
    files, counts, stat = flr.run()
    fix15(files[1], files[5])
    fix_table1(files[1])
    log('Формулалар ҳисобланмоқда…')
    final = {}
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        futs = {}
        for k, f in files.items():
            dst = os.path.join(outdir, os.path.basename(f))
            futs[ex.submit(_finish, f, dst)] = (k, dst)
        for fu in cf.as_completed(futs):
            fu.result()
            k, dst = futs[fu]
            final[k] = dst
    shutil.rmtree(work, ignore_errors=True)
    # ҳисобот
    other_prog = sum(1 for d in rows if str(d.get(32)).split('.')[0] == '1' and str(d.get(20)).strip() not in PMAP)
    new_act = 0
    for d in rows:
        if d.get(28) and str(d.get(37)).split('.')[0] == '1':
            ref['act'][P(d[7])] = str(d[28]).strip()
            new_act += 1
    if new_act:
        try:
            refs.save(ref)
        except Exception as e:  # noqa
            log(f'Маълумотнома сақланмади: {e}')
    notes = []
    if stat.get('mfy_miss'):
        notes.append(f"МФЙ коди топилмаган қаторлар: {stat['mfy_miss']}")
    if info['derived_flags']:
        notes.append(f"Омбордаги белгиси ҳисобланмаган, майдонлардан аниқланган: {info['derived_flags']}")
    if other_prog:
        notes.append(f'Кредит дастури номаълум («Бошқалар»га тушди): {other_prog}')
    sixth = [d for d in rows if str(d.get(37)).split('.')[0] == '1']
    noact = sum(1 for d in sixth if not (d.get(28) or ref['act'].get(P(d[7]))))
    if noact:
        notes.append(f'6-жадвал: фаолият тури топилмаган (соҳа «Бошқа»): {noact}')
    return final, counts, notes

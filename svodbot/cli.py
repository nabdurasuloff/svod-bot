import argparse, os
from .pipeline import run, guess_date

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Омбор китобидан 6 та жадвални тўлдириш')
    ap.add_argument('ombor'); ap.add_argument('--out', default='out'); ap.add_argument('--date')
    a = ap.parse_args()
    date = a.date or guess_date(os.path.basename(a.ombor))
    final, counts, notes = run(a.ombor, a.out, date)
    print(counts); [print('•', n) for n in notes]

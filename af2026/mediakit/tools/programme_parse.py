"""Legge assets/source/programme.md e restituisce una struttura: giorni -> sale -> blocchi.

Blocco = {'kind': 'session'|'item'|'break'|'note', ...}
- session: titolo di sezione (Panel, Keynote lecture, Workshop…) + eventuali chair
- item:    orario, nomi, titolo
- break:   orario + testo (Coffee break, Lunch break, Discussion…)
- note:    testo libero (es. iscrizione ai workshop)
Nessuna abbreviazione: i nomi incompleti del sorgente vengono completati (FULL_NAMES).
"""
import re
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / 'assets' / 'source' / 'programme.md'

# Nel sorgente alcuni chair hanno solo il cognome: nomi completi dalla lista partecipanti
FULL_NAMES = {
    'Chair and introduction by **Simeoni**': 'Andrea Simeoni',
    'Chair and introduction by **Cavalazzi**, **Johnson**, **Putzolu**': 'Marco Cavalazzi, Tyler Duane Johnson, Cristiano Putzolu',
}
BREAKS = ('Coffee break', 'Lunch break', 'Discussion', 'Panel presentation', 'Day-one closing remarks', 'Closing remarks')


def clean(s):
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)   # link -> testo
    s = s.replace('**', '').replace('*', '')
    return re.sub(r'\s+', ' ', s).strip()


def parse(path=SRC):
    lines = path.read_text(encoding='utf-8').splitlines()
    days, day, room, item = [], None, None, None

    def flush():
        nonlocal item
        if item and room is not None:
            if item.get('title') or item.get('names'):
                room['blocks'].append(item)
            elif item.get('text'):
                room['blocks'].append({'kind': 'break', 'time': item['time'], 'text': item['text']})
        item = None

    for raw in lines:
        s = raw.strip()
        m = re.match(r'^## (\d+ \w+ 2026)$', s)
        if m:
            flush(); day = {'date': m.group(1), 'rooms': []}; days.append(day); room = None; continue
        if day is None:
            continue
        m = re.match(r'^### (.+)$', s)
        if m:
            flush(); room = {'name': m.group(1), 'blocks': []}; day['rooms'].append(room); continue
        if room is None or not s or s == '---':
            if not s or s == '---':
                flush()
            continue
        m = re.match(r'^- \*\*(\d\d:\d\d)\*\* - (\d\d:\d\d)\s*(.*)$', s)
        if m:
            flush()
            item = {'kind': 'item', 'time': f'{m.group(1)}–{m.group(2)}', 'names': '', 'title': '', 'text': clean(m.group(3))}
            continue
        if s.startswith('Chair and introduction by'):
            flush()
            names = FULL_NAMES.get(s) or clean(s[len('Chair and introduction by'):])
            room['blocks'][-1]['chairs'] = names
            continue
        if s.startswith('**') and s.endswith('**') and item is None:
            flush()
            title = clean(s)
            room['blocks'].append({'kind': 'session', 'title': title})
            continue
        if item is not None:
            if s.startswith('Discussants:'):
                item['discussants'] = clean(s[len('Discussants:'):]); continue
            c = clean(s)
            if c in BREAKS:                       # pause, discussioni, chiusure: prima del controllo dei titoli
                item['text'] = c; continue
            if s.startswith('*') or s.startswith('[*'):
                item['title'] = c; continue
            item['names'] = (item['names'] + ', ' + c).strip(', ') if item['names'] else c
            continue
        if s.startswith('To register'):
            room['blocks'].append({'kind': 'note', 'text': clean(s)})
    flush()
    return days


if __name__ == '__main__':
    for d in parse():
        print('==', d['date'])
        for r in d['rooms']:
            print('  --', r['name'], len(r['blocks']), 'blocchi')
            for b in r['blocks'][:4]:
                print('     ', b)

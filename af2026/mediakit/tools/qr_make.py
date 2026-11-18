"""Generatore di QR code senza dipendenze (modalità byte, standard ISO/IEC 18004; struttura come la libreria di Project Nayuki).

Uso:  ../.venv/bin/python tools/qr_make.py "https://..." assets/source/master-qr-teams.svg
Scrive un SVG con un modulo = 1 unità e 4 moduli di bordo bianco, nello stesso stile di assets/source/master-qr.svg,
largo 35 mm come il QR del programma (più moduli = moduli più piccoli, stessa misura).
"""
import sys
from pathlib import Path

ECC_M = 1                                   # livelli: 0 L, 1 M, 2 Q, 3 H
_FORMAT_BITS = {0: 1, 1: 0, 2: 3, 3: 2}
# blocchi di correzione per versione (indice 1..40) e livello L, M, Q, H
_ECC_PER_BLOCK = [
    [-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18, 20, 24, 26, 30, 22, 24, 28, 30, 28, 28, 28, 28, 30, 30, 26, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
    [-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26, 30, 22, 22, 24, 24, 28, 28, 26, 26, 26, 26, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28, 28],
    [-1, 13, 22, 18, 26, 18, 24, 18, 22, 20, 24, 28, 26, 24, 20, 30, 24, 28, 28, 26, 30, 28, 30, 30, 30, 30, 28, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30],
    [-1, 17, 28, 22, 16, 22, 28, 26, 26, 24, 28, 24, 28, 22, 24, 24, 30, 28, 28, 26, 28, 30, 24, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30, 30]]
_NUM_BLOCKS = [
    [-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4, 4, 4, 4, 4, 6, 6, 6, 6, 7, 8, 8, 9, 9, 10, 12, 12, 12, 13, 14, 15, 16, 17, 18, 19, 19, 20, 21, 22, 24, 25],
    [-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5, 5, 8, 9, 9, 10, 10, 11, 13, 14, 16, 17, 17, 18, 20, 21, 23, 25, 26, 28, 29, 31, 33, 35, 37, 38, 40, 43, 45, 47, 49],
    [-1, 1, 1, 2, 2, 4, 4, 6, 6, 8, 8, 8, 10, 12, 16, 12, 17, 16, 18, 21, 20, 23, 23, 25, 27, 29, 34, 34, 35, 38, 40, 43, 45, 48, 51, 53, 56, 59, 62, 65, 68],
    [-1, 1, 1, 2, 4, 4, 4, 5, 6, 8, 8, 11, 11, 16, 16, 18, 16, 19, 21, 25, 25, 25, 34, 30, 32, 35, 37, 40, 42, 45, 48, 51, 54, 57, 60, 63, 66, 70, 74, 77, 81]]


def _raw_modules(ver):
    r = (16 * ver + 128) * ver + 64
    if ver >= 2:
        na = ver // 7 + 2
        r -= (25 * na - 10) * na - 55
        if ver >= 7:
            r -= 36
    return r


def _data_codewords(ver, ecl):
    return _raw_modules(ver) // 8 - _ECC_PER_BLOCK[ecl][ver] * _NUM_BLOCKS[ecl][ver]


def _gf_mul(x, y):
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _rs_divisor(degree):
    res = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(len(res)):
            res[j] = _gf_mul(res[j], root)
            if j + 1 < len(res):
                res[j] ^= res[j + 1]
        root = _gf_mul(root, 0x02)
    return res


def _rs_remainder(data, div):
    res = [0] * len(div)
    for b in data:
        f = b ^ res.pop(0)
        res.append(0)
        for i, c in enumerate(div):
            res[i] ^= _gf_mul(c, f)
    return res


def _align_positions(ver):
    if ver == 1:
        return []
    n = ver // 7 + 2
    step = (ver * 8 + n * 3 + 5) // (n * 4 - 4) * 2
    return [6] + [ver * 4 + 10 - i * step for i in reversed(range(n - 1))]


class QR:
    def __init__(self, data: bytes, ecl=ECC_M):
        for ver in range(1, 41):
            cap = _data_codewords(ver, ecl) * 8
            cc = 8 if ver < 10 else 16
            if 4 + cc + len(data) * 8 <= cap:
                break
        else:
            raise ValueError('testo troppo lungo')
        self.ver, self.ecl, self.size = ver, ecl, ver * 4 + 17
        bits = []
        put = lambda val, n: bits.extend((val >> i) & 1 for i in reversed(range(n)))
        put(0b0100, 4); put(len(data), cc)
        for b in data:
            put(b, 8)
        put(0, min(4, cap - len(bits)))
        put(0, (-len(bits)) % 8)
        pad = 0xEC
        while len(bits) < cap:
            put(pad, 8); pad ^= 0xEC ^ 0x11
        cw = [int(''.join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
        allcw = self._add_ecc(cw)
        self.m = [[False] * self.size for _ in range(self.size)]
        self.fn = [[False] * self.size for _ in range(self.size)]
        self._draw_function()
        self._draw_codewords(allcw)
        best, bestp = None, None
        for mask in range(8):
            self._apply_mask(mask); self._draw_format(mask)
            p = self._penalty()
            if bestp is None or p < bestp:
                best, bestp = mask, p
            self._apply_mask(mask)
        self._apply_mask(best); self._draw_format(best)
        self.mask = best

    def _add_ecc(self, data):
        ver, ecl = self.ver, self.ecl
        nb, eb = _NUM_BLOCKS[ecl][ver], _ECC_PER_BLOCK[ecl][ver]
        raw = _raw_modules(ver) // 8
        nshort = nb - raw % nb
        slen = raw // nb
        div = _rs_divisor(eb)
        blocks, k = [], 0
        for i in range(nb):
            dat = data[k:k + slen - eb + (0 if i < nshort else 1)]
            k += len(dat)
            ecc = _rs_remainder(dat, div)
            if i < nshort:
                dat = dat + [0]
            blocks.append(dat + ecc)
        out = []
        for i in range(len(blocks[0])):
            for j, blk in enumerate(blocks):
                if i != slen - eb or j >= nshort:
                    out.append(blk[i])
        return out

    def _set(self, x, y, dark):
        self.m[y][x] = dark; self.fn[y][x] = True

    def _draw_function(self):
        n = self.size
        for i in range(n):
            self._set(6, i, i % 2 == 0); self._set(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (n - 4, 3), (3, n - 4)):
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < n and 0 <= y < n:
                        d = max(abs(dx), abs(dy))
                        self._set(x, y, d not in (2, 4))
        ap = _align_positions(self.ver)
        for i in ap:
            for j in ap:
                if (i, j) in ((6, 6), (6, ap[-1]), (ap[-1], 6)):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        self._set(i + dx, j + dy, max(abs(dx), abs(dy)) != 1)
        self._draw_format(0)
        if self.ver >= 7:
            rem = self.ver
            for _ in range(12):
                rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
            bits = self.ver << 12 | rem
            for i in range(18):
                bit = (bits >> i) & 1 == 1
                a, b = n - 11 + i % 3, i // 3
                self._set(a, b, bit); self._set(b, a, bit)

    def _draw_format(self, mask):
        data = _FORMAT_BITS[self.ecl] << 3 | mask
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = (data << 10 | rem) ^ 0x5412
        g = lambda i: (bits >> i) & 1 == 1
        n = self.size
        for i in range(6):
            self._set(8, i, g(i))
        self._set(8, 7, g(6)); self._set(8, 8, g(7)); self._set(7, 8, g(8))
        for i in range(9, 15):
            self._set(14 - i, 8, g(i))
        for i in range(8):
            self._set(n - 1 - i, 8, g(i))
        for i in range(8, 15):
            self._set(8, n - 15 + i, g(i))
        self._set(8, n - 8, True)

    def _draw_codewords(self, data):
        n, i = self.size, 0
        right = n - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vert in range(n):
                for j in range(2):
                    x = right - j
                    upward = (right + 1) & 2 == 0
                    y = n - 1 - vert if upward else vert
                    if not self.fn[y][x] and i < len(data) * 8:
                        self.m[y][x] = (data[i >> 3] >> (7 - (i & 7))) & 1 == 1
                        i += 1
            right -= 2

    def _apply_mask(self, mask):
        f = [lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0, lambda x, y: (x + y) % 3 == 0,
             lambda x, y: (x // 3 + y // 2) % 2 == 0, lambda x, y: x * y % 2 + x * y % 3 == 0,
             lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0, lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0][mask]
        for y in range(self.size):
            for x in range(self.size):
                if not self.fn[y][x] and f(x, y):
                    self.m[y][x] = not self.m[y][x]

    def _penalty(self):
        n, m, p = self.size, self.m, 0
        for line in [m[y] for y in range(n)] + [[m[y][x] for y in range(n)] for x in range(n)]:
            run, col = 1, line[0]
            for v in line[1:]:
                if v == col:
                    run += 1
                else:
                    if run >= 5:
                        p += run - 2
                    run, col = 1, v
            if run >= 5:
                p += run - 2
            s = ''.join('1' if v else '0' for v in line)
            for pat in ('10111010000', '00001011101'):
                p += 40 * sum(1 for k in range(len(s) - 10) if s[k:k + 11] == pat)
        for y in range(n - 1):
            for x in range(n - 1):
                if m[y][x] == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1]:
                    p += 3
        dark = sum(sum(r) for r in m)
        p += (abs(dark * 20 - n * n * 10) + n * n - 1) // (n * n) * 10
        return p


def qr_svg(text, quiet=4, ink='#252B29', mm=35):
    q = QR(text.encode('utf-8'))
    n = q.size + 2 * quiet
    d = ' '.join(f'M{x + quiet} {y + quiet}h1v1h-1z' for y in range(q.size) for x in range(q.size) if q.m[y][x])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{mm}mm" height="{mm}mm" viewBox="0 0 {n} {n}">'
            f'<rect width="{n}" height="{n}" fill="#fff"/><path d="{d}" fill="{ink}" shape-rendering="crispEdges"/></svg>'), q


if __name__ == '__main__':
    svg, q = qr_svg(sys.argv[1])
    Path(sys.argv[2]).write_text(svg, encoding='utf-8')
    print('versione', q.ver, '| moduli', q.size, '| maschera', q.mask)

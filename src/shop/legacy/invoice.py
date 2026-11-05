"""EP6 · 레거시 코드. 5년 전 누군가 쓴 영수증 함수. 테스트가 없고, 아무도 규칙을 정확히 모른다.

이 파일은 일부러 고치지 않는다. 리팩터링한 버전은 shop/invoice.py 에 있다.
"""


def make_invoice(c, items, t, m):
    s = 0
    for i in items:
        if i[2] > 0:
            s = s + i[1] * i[2]
    if t == 1:
        if s >= 30000:
            d = s * 0.1
        else:
            d = 0
    elif t == 2:
        d = 5000
        if s < 30000:
            d = 0
    else:
        d = 0
    if m:
        if s * 0.05 > d:
            d = s * 0.05
    s2 = s - d
    if s2 < 0:
        s2 = 0
    if s2 >= 50000:
        sh = 0
    else:
        if s2 == 0:
            sh = 0
        else:
            sh = 3000
    tot = int(s2 + sh + 0.5)
    p = 0
    if m:
        p = int(s2 / 100)
        if p > 5000:
            p = 5000
    lines = []
    lines.append("INVOICE for " + c)
    for i in items:
        if i[2] > 0:
            lines.append("  " + i[0] + " x" + str(i[2]) + " = " + str(i[1] * i[2]))
    lines.append("  discount: -" + str(int(d + 0.5)))
    lines.append("  shipping: " + str(sh))
    lines.append("TOTAL: " + str(tot))
    if p > 0:
        lines.append("points earned: " + str(p))
    return "\n".join(lines)

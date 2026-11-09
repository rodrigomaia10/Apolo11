import fitz, re, sys, io
from PIL import Image, ImageFilter

SRC = sys.argv[1]
DST = sys.argv[2]
ZOOM = 2.0
RAIO = 9

num = re.compile(r"^[-+(]?\d[\d.,]*[%)…]*$")
UNID = {"Mi", "mil", "Bi", "k", "M"}


def eh_valor(t):
    t = t.strip()
    if not num.match(t):
        return False
    d = re.sub(r"\D", "", t)
    if "%" in t or "," in t or "…" in t:
        return True
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", t):      # milhar 1.234 / 12.345.678
        return True
    if re.fullmatch(r"(19|20)\d\d", d) and t == d:  # ano
        return False
    if re.fullmatch(r"\d{3,}", t):                  # inteiros grandes (contagens)
        return True
    return False


doc = fitz.open(SRC)
out = fitz.open()
total = 0
for pg in doc:
    words = pg.get_text("words")  # x0,y0,x1,y1,texto,bloco,linha,palavra
    rects = []
    for i, w in enumerate(words):
        t = w[4]
        ligado = (i + 1 < len(words) and words[i + 1][4] in UNID and abs(words[i + 1][1] - w[1]) < 3) or                  (i > 0 and words[i - 1][4] in ("R$", "-R$") and abs(words[i - 1][1] - w[1]) < 3)
        if eh_valor(t) or (ligado and num.match(t)):
            r = fitz.Rect(w[:4])
            # junta unidade apos o numero (Mi, mil...) e R$ antes
            if i + 1 < len(words) and words[i + 1][4] in UNID and abs(words[i + 1][1] - w[1]) < 3:
                r |= fitz.Rect(words[i + 1][:4])
            if i > 0 and words[i - 1][4] in ("R$", "-R$") and abs(words[i - 1][1] - w[1]) < 3:
                r |= fitz.Rect(words[i - 1][:4])
            rects.append(r)
    mat = fitz.Matrix(ZOOM, ZOOM)
    pix = pg.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    for r in rects:
        box = (int(r.x0 * ZOOM) - 3, int(r.y0 * ZOOM) - 2, int(r.x1 * ZOOM) + 3, int(r.y1 * ZOOM) + 2)
        box = (max(box[0], 0), max(box[1], 0), min(box[2], img.width), min(box[3], img.height))
        if box[2] <= box[0] or box[3] <= box[1]:
            continue
        reg = img.crop(box)
        # pixeliza forte e borra: ilegivel e irreversivel
        small = reg.resize((max(1, reg.width // 6), max(1, reg.height // 6)), Image.BILINEAR)
        reg = small.resize(reg.size, Image.NEAREST).filter(ImageFilter.GaussianBlur(RAIO))
        img.paste(reg, box)
    total += len(rects)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    npg = out.new_page(width=pg.rect.width, height=pg.rect.height)
    npg.insert_image(npg.rect, stream=buf.getvalue())
    print("pagina", pg.number + 1, "valores borrados:", len(rects))
out.save(DST, deflate=True)
print("total", total, "->", DST)

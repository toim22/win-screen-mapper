"""folhas_regua.py: junta prints em folhas com regua para marcar alvos de clique olhando a imagem.

Cada print ganha regua de 28 px a esquerda (y) e 14 px no topo (x), com numero a cada 50 px e linhas
guia magenta a cada 50 px. As coordenadas lidas na folha ja sao relativas ao print (descontar a regua
e feito pela propria numeracao). Cuidado com a conversao: varios alvos do Corel sairam errados por
somar a regua de novo.

Uso:
  python folhas_regua.py --saida <pasta> --por-folha 4 --y0 0 --y1 560 "<pasta>/*/000 inicial.png"
  python folhas_regua.py --saida <pasta> --grade print.png    # uma copia com grade de 10/50 px e x,y escritos
"""
import argparse
import glob
import os

from PIL import Image, ImageDraw


def ruled(im, y0=0, y1=None):
    y1 = y1 or im.height
    im = im.crop((0, y0, im.width, min(y1, im.height))).convert("RGB")
    R = Image.new("RGB", (im.width + 28, im.height + 14), (255, 255, 255))
    R.paste(im, (28, 14))
    d = ImageDraw.Draw(R)
    for x in range(0, im.width, 10):
        d.line([(28 + x, 0), (28 + x, 14 if x % 50 == 0 else 6)], fill=(0, 0, 0))
        if x % 50 == 0:
            d.text((30 + x, 0), str(x), fill=(200, 0, 0))
    for y in range(0, im.height, 10):
        yy = y + y0
        d.line([(0 if yy % 50 == 0 else 20, 14 + y), (28, 14 + y)], fill=(0, 0, 0))
        if yy % 50 == 0:
            d.text((0, 15 + y), str(yy), fill=(200, 0, 0))
    for x in range(50, im.width, 50):
        d.line([(28 + x, 14), (28 + x, R.height)], fill=(255, 0, 255))
    for y in range(0, im.height, 10):
        if (y + y0) % 50 == 0:
            d.line([(28, 14 + y), (R.width, 14 + y)], fill=(255, 0, 255))
    return R


def sheet(files, path, y0=0, y1=None):
    ims = [ruled(Image.open(f), y0, y1) for f in files]
    W = sum(i.width for i in ims) + 8 * len(ims)
    H = max(i.height for i in ims)
    s = Image.new("RGB", (W, H), (255, 255, 255))
    x = 0
    for i in ims:
        s.paste(i, (x, 0))
        x += i.width + 8
    s.save(path)
    return path


def gridded(img, path):
    """Copia com grade de 10/50 px e as coordenadas escritas a cada 50x100 (bom para paineis)."""
    im = img.convert("RGB")
    d = ImageDraw.Draw(im)
    for x in range(0, im.width, 10):
        d.line([(x, 0), (x, im.height)], fill=(90, 90, 0) if x % 50 else (200, 200, 0))
    for y in range(0, im.height, 10):
        d.line([(0, y), (im.width, y)], fill=(90, 90, 0) if y % 50 else (200, 200, 0))
    for x in range(0, im.width, 50):
        for y in range(0, im.height, 100):
            d.text((x + 1, y + 1), f"{x},{y}", fill=(255, 80, 80))
    im.save(path)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("padroes", nargs="+", help="arquivos ou globs")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--por-folha", type=int, default=4)
    ap.add_argument("--y0", type=int, default=0)
    ap.add_argument("--y1", type=int, default=0, help="0 = altura toda")
    ap.add_argument("--grade", action="store_true", help="uma copia com grade por arquivo")
    a = ap.parse_args()
    os.makedirs(a.saida, exist_ok=True)
    fs = sorted({f for p in a.padroes for f in glob.glob(p)})
    if a.grade:
        for f in fs:
            print(gridded(Image.open(f), os.path.join(a.saida, "grade_" + os.path.basename(f))))
        return
    for k in range(0, len(fs), a.por_folha):
        out = sheet(fs[k:k + a.por_folha], os.path.join(a.saida, f"folha{k // a.por_folha + 1:02d}.png"),
                    a.y0, a.y1 or None)
        print(out, [os.path.basename(os.path.dirname(f)) + "/" + os.path.basename(f) for f in fs[k:k + a.por_folha]])


if __name__ == "__main__":
    main()

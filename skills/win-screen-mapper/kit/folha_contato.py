"""folha_contato.py: miniaturas lado a lado, com o nome embaixo, para revisar muitos prints de uma vez.

Revise toda rodada: print vazio/trocado, tooltip salvo como janela, outro monitor, pastas pessoais,
"nada abriu". Abra as folhas com a ferramenta Read (ela mostra imagens).

Uso:
  python folha_contato.py --saida <pasta> [--colunas 5] [--lado 300] [--por-folha 30] "<pasta>/**/*.png"
"""
import argparse
import glob
import os

from PIL import Image, ImageDraw


def folha(files, path, colunas=5, lado=300, raiz=""):
    cel_h = lado + 30
    linhas = (len(files) + colunas - 1) // colunas
    s = Image.new("RGB", (colunas * (lado + 10) + 10, linhas * (cel_h + 10) + 10), (235, 235, 232))
    d = ImageDraw.Draw(s)
    for i, f in enumerate(files):
        im = Image.open(f).convert("RGB")
        im.thumbnail((lado, lado))
        x = 10 + (i % colunas) * (lado + 10)
        y = 10 + (i // colunas) * (cel_h + 10)
        d.rectangle([x - 1, y - 1, x + lado, y + lado], outline=(180, 180, 175))
        s.paste(im, (x + (lado - im.width) // 2, y + (lado - im.height) // 2))
        nome = (os.path.relpath(f, raiz) if raiz else os.path.basename(f)).replace("▸", ">")  # fonte padrao sem ▸
        d.text((x, y + lado + 4), f"{i + 1}. {nome[-48:]}", fill=(20, 20, 20))
    s.save(path)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("padroes", nargs="+")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--colunas", type=int, default=5)
    ap.add_argument("--lado", type=int, default=300)
    ap.add_argument("--por-folha", type=int, default=30)
    ap.add_argument("--com-tela-inteira", action="store_true", help="inclui as copias de tela-inteira/")
    a = ap.parse_args()
    os.makedirs(a.saida, exist_ok=True)
    fs = sorted({f for p in a.padroes for f in glob.glob(p, recursive=True)})
    if not a.com_tela_inteira:
        fs = [f for f in fs if "tela-inteira" not in f.replace("\\", "/").split("/")]
    raiz = os.path.commonpath(fs) if len(fs) > 1 else ""
    for k in range(0, len(fs), a.por_folha):
        print(folha(fs[k:k + a.por_folha], os.path.join(a.saida, f"contato{k // a.por_folha + 1:02d}.png"),
                    a.colunas, a.lado, raiz))
    print(len(fs), "prints")


if __name__ == "__main__":
    main()

"""Gera as imagens dos cartões de apresentação dos modelos (app/img/modelos/render-<familia>.jpg).

São renders próprias do Clave, feitas por conta (sem foto nem imagem de terceiros), no espírito das páginas de
lançamento de cada família: Opus, o horizonte da Terra ao amanhecer; Sonnet, a Terra vista da janela de uma nave;
Haiku, papel claro com um horizonte a traço fino; Fable, céu de tarde com nuvens e a lua.

Uso: python ferramentas/gerar_renders.py   (precisa de numpy e Pillow; não roda dentro do app)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

SAIDA = Path(__file__).resolve().parent.parent / "app" / "img" / "modelos"
L, A = 1000, 600
rng = np.random.default_rng(55)


def ruido(escalas=(4, 8, 16, 32, 64), pesos=None, semente=0):
    """Ruído fractal 0..1 (grades aleatórias ampliadas e somadas)."""
    g = np.random.default_rng(semente)
    pesos = pesos or [1 / (i + 1) for i in range(len(escalas))]
    total = np.zeros((A, L))
    for e, p in zip(escalas, pesos):
        base = g.random((max(2, A * e // L), e))
        img = Image.fromarray((base * 255).astype(np.uint8)).resize((L, A), Image.BICUBIC)
        total += np.asarray(img, dtype=float) / 255 * p
    total -= total.min()
    return total / total.max()


def suave(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def misturar(cores, pos, t):
    """Gradiente: cores (lista de RGB 0..255) nas posições pos, avaliado em t (array)."""
    cores = np.asarray(cores, dtype=float)
    saida = np.zeros(t.shape + (3,))
    for c in range(3):
        saida[..., c] = np.interp(t, pos, cores[:, c])
    return saida


def granular(img, forca=7.0, semente=1):
    g = np.random.default_rng(semente)
    return img + g.normal(0, forca, img.shape[:2])[..., None]


def vinheta(img, forca=0.35):
    yy, xx = np.mgrid[0:A, 0:L]
    d = np.sqrt(((xx - L / 2) / (L / 2)) ** 2 + ((yy - A / 2) / (A / 2)) ** 2)
    return img * (1 - forca * suave(0.6, 1.5, d))[..., None]


def salvar(img, nome):
    arr = np.clip(img, 0, 255).astype(np.uint8)
    Image.fromarray(arr).save(SAIDA / f"render-{nome}.jpg", quality=84, optimize=True, progressive=True)
    print("ok", nome, (SAIDA / f"render-{nome}.jpg").stat().st_size // 1024, "KB")


def opus():
    yy, xx = np.mgrid[0:A, 0:L].astype(float)
    horizonte = A * 0.66 + ((xx - L / 2) / L) ** 2 * A * 0.55     # a curva da Terra
    acima = (horizonte - yy) / A                                    # >0 no céu
    centro = np.exp(-((xx - L * 0.5) / (L * 0.42)) ** 2)            # o sol vai nascer no meio
    ceu = misturar([(255, 120, 40), (255, 196, 120), (150, 170, 205), (84, 128, 196), (34, 56, 102), (10, 16, 34)],
                   [0, 0.018, 0.07, 0.2, 0.45, 0.8], acima)
    brilho = np.exp(-np.clip(acima, 0, None) / 0.035) * (0.55 + 0.45 * centro)
    ceu = ceu * (0.75 + 0.25 * centro[..., None]) + np.array([255, 90, 20]) * brilho[..., None] * 0.55
    abaixo = np.clip(-acima, 0, None)
    terra = misturar([(70, 30, 18), (30, 16, 12), (16, 11, 10)], [0, 0.04, 0.3], abaixo)
    terra += np.array([255, 80, 20]) * (np.exp(-abaixo / 0.012) * centro * 0.35)[..., None]
    nuvens = ruido((6, 14, 40), semente=3)
    terra *= (0.8 + 0.35 * nuvens)[..., None]
    img = np.where((acima > 0)[..., None], ceu, terra)
    img = np.asarray(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)), float)
    salvar(vinheta(granular(img, 9, 2), 0.3), "opus")


def sonnet():
    yy, xx = np.mgrid[0:A, 0:L].astype(float)
    img = np.zeros((A, L, 3)) + np.array([4, 6, 12])
    g = np.random.default_rng(8)
    for _ in range(260):                                             # estrelas
        x, y = g.integers(0, L), g.integers(0, int(A * 0.62))
        b = g.random() ** 3 * 220 + 30
        img[y, x] = (b, b, b * 1.05)
    cx, cy, r = L * 0.5, A * 2.15, A * 1.62                          # o planeta, centro bem abaixo
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    dentro = d < r
    borda = np.clip((r - d) / (A * 0.45), 0, 1)                      # 0 no limbo, 1 para dentro
    oceano = misturar([(40, 78, 140), (24, 60, 120), (12, 34, 80)], [0, 0.3, 1], borda)
    nuv = suave(0.5, 0.74, ruido((8, 18, 40, 90, 180), semente=11))
    planeta = oceano * (1 - nuv[..., None] * 0.85) + np.array([215, 225, 240]) * nuv[..., None] * 0.85
    planeta *= (0.55 + 0.45 * suave(0, 0.35, borda))[..., None]      # escurece no limbo
    img = np.where(dentro[..., None], planeta, img)
    atmos = np.exp(-np.abs(d - r) / (A * 0.012)) + 0.5 * np.exp(-np.clip(d - r, 0, None) / (A * 0.05))
    img += np.array([70, 120, 255]) * atmos[..., None] * 0.55
    img = np.asarray(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), float)
    # a janela: um retângulo de cantos bem redondos, com a moldura escura e um fio de luz na beirada
    m = Image.new("L", (L, A), 0)
    from PIL import ImageDraw
    ImageDraw.Draw(m).rounded_rectangle((L * 0.06, A * 0.1, L * 0.94, A * 0.9), radius=int(A * 0.2), fill=255)
    janela = np.asarray(m.filter(ImageFilter.GaussianBlur(5)), float) / 255
    fio = np.asarray(m.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.GaussianBlur(3)), float) / 255
    moldura = misturar([(28, 30, 38), (12, 13, 18)], [0, 1], yy / A)
    img = img * janela[..., None] + moldura * (1 - janela[..., None]) + np.array([90, 105, 150]) * fio[..., None] * 1.6
    salvar(vinheta(granular(img, 6, 4), 0.25), "sonnet")


def haiku():
    yy, xx = np.mgrid[0:A, 0:L].astype(float)
    papel = np.zeros((A, L, 3)) + np.array([246, 243, 236])
    fibra = ruido((40, 120, 300), semente=21)
    papel -= (fibra * 10)[..., None]
    img = Image.fromarray(np.clip(papel, 0, 255).astype(np.uint8))
    from PIL import ImageDraw
    dr = ImageDraw.Draw(img)
    g = np.random.default_rng(5)
    pontos = []
    for x in np.linspace(-L * 0.02, L * 1.02, 500):                  # o horizonte, um arco feito à mão
        y = A * 0.74 - (1 - ((x - L / 2) / (L * 0.56)) ** 2) * A * 0.2 + g.normal(0, 0.5)
        pontos.append((x, y))
    dr.line(pontos, fill=(32, 30, 28), width=2)
    for _ in range(900):                                             # tinta que respinga do traço
        i = g.integers(0, len(pontos))
        x, y = pontos[i]
        dr.point((x + g.normal(0, 1.4), y + g.normal(0, 1.4)), fill=(60, 56, 52))
    arr = np.asarray(img, float)
    salvar(granular(arr, 4, 6), "haiku")


def fable():
    yy, xx = np.mgrid[0:A, 0:L].astype(float)
    ceu = misturar([(98, 140, 210), (112, 156, 220), (140, 178, 230)], [0, 0.5, 1], yy / A)
    n = ruido((3, 6, 12, 24), semente=31)
    borda = suave(0.0, 1.0, np.abs(xx - L * 0.55) / (L * 0.55))     # as nuvens ficam nos lados
    nuv = suave(0.42, 0.75, n * (0.55 + 0.6 * borda))
    tom = misturar([(250, 226, 190), (246, 214, 214)], [0, 1], ruido((4, 9), semente=33))
    img = ceu * (1 - nuv[..., None]) + tom * nuv[..., None]
    img = np.asarray(Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7)), float)
    # a lua, em foco e meio apagada pelo céu (o desfoque é só das nuvens e do capim)
    mx, my, mr = L * 0.74, A * 0.3, A * 0.11
    dm = np.sqrt((xx - mx) ** 2 + (yy - my) ** 2)
    lua = suave(mr + 1.5, mr - 1.5, dm) * (0.55 + 0.45 * suave(mr, -mr, xx - mx))   # mais clara de um lado
    crat = ruido((10, 24, 60), semente=41)
    cor_lua = np.array([232, 236, 244]) - (crat * 46)[..., None]
    img = img * (1 - lua[..., None] * 0.8) + cor_lua * lua[..., None] * 0.8
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    # capim desfocado na frente, curvado, do canto de baixo
    from PIL import ImageDraw
    capim = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    dr = ImageDraw.Draw(capim)
    g = np.random.default_rng(13)
    for _ in range(26):
        x0 = L * (0.5 + g.random() * 0.55)
        dobra, alt = g.normal(-70, 40), A * (0.18 + g.random() * 0.32)
        pts = [(x0 + dobra * (t ** 2), A + 10 - alt * t) for t in np.linspace(0, 1, 12)]
        dr.line(pts, fill=(70, 84, 128, 105), width=int(3 + g.random() * 5))
    capim = capim.filter(ImageFilter.GaussianBlur(6))
    pil = Image.alpha_composite(pil.convert("RGBA"), capim).convert("RGB")
    salvar(granular(np.asarray(pil, float), 7, 9), "fable")


if __name__ == "__main__":
    SAIDA.mkdir(parents=True, exist_ok=True)
    for f in (opus, sonnet, haiku, fable):
        f()

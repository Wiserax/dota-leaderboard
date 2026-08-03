# -*- coding: utf-8 -*-
"""Генерация favicon.ico + apple-touch-icon.png в стиле Settling Line.

Дизайн: тёмный квадрат, ember-треугольник падает сквозь градиентную линию горизонта.
favicon.svg лежит в репе руками, тут только растровые версии.
"""
import os

from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = (12, 15, 20, 255)          # --bg #0c0f14
EMBER_HI = (224, 90, 65, 255)   # --ember-hi #e05a41
UP = (110, 200, 136)            # --up #6ec888
GOLD = (230, 180, 92)           # --gold #e6b45c


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_icon(size, rounded):
    s = size / 64.0
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if rounded:
        d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(13 * s), fill=BG)
    else:
        d.rectangle([0, 0, size, size], fill=BG)
    # треугольник вниз (базовая линия выше горизонта, вершина глубоко под ним)
    d.polygon([(16 * s, 22 * s), (48 * s, 22 * s), (32 * s, 54 * s)], fill=EMBER_HI)
    # линия горизонта: градиент up -> gold -> ember по колонкам
    x0, x1 = int(7 * s), int(57 * s)
    y0, y1 = int(25 * s), max(int(28 * s), int(25 * s) + 1)
    for x in range(x0, x1):
        t = (x - x0) / max(1, x1 - 1 - x0)
        c = lerp(UP, GOLD, t / 0.55) if t < 0.55 else lerp(GOLD, EMBER_HI[:3], (t - 0.55) / 0.45)
        d.rectangle([x, y0, x, y1 - 1], fill=c + (255,))
    return img


big = draw_icon(256, rounded=True)
big.resize((48, 48), Image.LANCZOS).save(
    os.path.join(REPO, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
draw_icon(360, rounded=False).resize((180, 180), Image.LANCZOS).save(
    os.path.join(REPO, "apple-touch-icon.png"))
print("favicon.ico + apple-touch-icon.png готовы")

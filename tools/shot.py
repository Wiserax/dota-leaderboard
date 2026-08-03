# -*- coding: utf-8 -*-
"""Скриншоты сайта в эмуляции реальных телефонов (Playwright).

  python tools/shot.py before      # снимет в shots/before-*.png
  python tools/shot.py after

Поднимает свой http-сервер на репозитории, так что видит локальные правки.
"""
import http.server
import os
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "shots")
PORT = 8231
TAG = sys.argv[1] if len(sys.argv) > 1 else "shot"

DEVICES = [
    ("pixel", "Pixel 7"),
    ("iphone", "iPhone 13"),
]


def serve():
    os.chdir(REPO)
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *a: None
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
        httpd.serve_forever()


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    threading.Thread(target=serve, daemon=True).start()

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for name, device_name in DEVICES:
            device = dict(pw.devices[device_name])
            ctx = browser.new_context(**device, locale="ru-RU")
            page = ctx.new_page()
            page.goto("http://127.0.0.1:%d/index.html" % PORT, wait_until="networkidle")
            page.wait_for_timeout(1600)  # анимации входа

            # первый экран
            p1 = os.path.join(OUT, "%s-%s-fold.png" % (TAG, name))
            page.screenshot(path=p1)

            # сколько пикселей до таблицы
            y = page.evaluate(
                "() => { const b = document.getElementById('board');"
                " return b ? Math.round(b.getBoundingClientRect().top + window.scrollY) : -1; }")
            vh = device["viewport"]["height"]
            print("%-7s %-10s до таблицы: %spx (%.2f экрана)" % (name, device_name, y, y / vh))

            # проверка липкой полосы фильтров: скроллим вглубь таблицы
            page.evaluate("() => window.scrollTo(0, 1600)")
            page.wait_for_timeout(500)
            page.screenshot(path=os.path.join(OUT, "%s-%s-scrolled.png" % (TAG, name)))
            page.evaluate("() => window.scrollTo(0, 0)")

            # вся страница целиком (сжатая, для обзора композиции)
            p2 = os.path.join(OUT, "%s-%s-full.png" % (TAG, name))
            page.screenshot(path=p2, full_page=True)
            ctx.close()
        browser.close()
    print("сохранено в", OUT)


if __name__ == "__main__":
    main()

# After the Fall: передача проекта

Документ для продолжения работы с нового устройства. Обновлён 4 августа 2026.

## Что это

Лидерборд Европы Dota 2, показывающий, как изменились позиции игроков после вайпа
рейтинга 31 июля 2026 (патч 7.41e сжал MMR Immortal до 9500, сохранив порядок мест).

- Прод: **https://dota2afterfall.com**
- Репозиторий: github.com/Wiserax/dota-leaderboard (GitHub Pages с ветки `main`)
- Дашборд аналитики: **https://141-148-232-49.sslip.io** (логин и пароль в приватном
  репозитории `Wiserax/servers`, файл `analytics.md`)

## Быстрый старт на новой машине

```bash
git clone git@github.com:Wiserax/dota-leaderboard.git
cd dota-leaderboard
python build.py --offline      # пересобрать data.js из сохранённых слепков
python -m http.server 8123     # открыть http://localhost:8123
```

Зависимости для тулзов: `pip install pillow requests PyJWT cryptography`

## Как устроены данные

Источник: `https://www.dota2.com/webapi/ILeaderboard/GetDivisionLeaderboard/v0001?division=europe&leaderboard=0`
(API отдаёт только ники, без ID аккаунтов, поэтому переименованных игроков сопоставить нельзя).

| Файл | Роль |
|---|---|
| `baseline_pre_reset.json` | стартовый слепок 31.07 14:13 МСК, самый ранний сохранившийся после вайпа |
| `current.json` | последний слепок с API |
| `prev_day.json` | два слота `{old, mid}` для суточного окна, база всегда 12-24 часа назад |
| `notable.json` | известные игроки, для карточки «Падение · известные» |
| `data.js` | результат сборки, читается фронтендом как `window.LB` |

`.github/workflows/update-data.yml` раз в час (cron `23 * * * *`) запускает `build.py`
и коммитит `data.js`, `current.json`, `prev_day.json`.

**Важно:** бот регулярно пушит в `main`, поэтому перед своим пушем всегда
`git pull --rebase origin main`. При конфликте в `current.json`:

```bash
git checkout --ours current.json && python build.py --offline
git add current.json data.js prev_day.json && GIT_EDITOR=true git rebase --continue
```

## Инструменты (`tools/`)

| Скрипт | Что делает |
|---|---|
| `build_artifact.py` | самодостаточный HTML (шрифты, флаги, данные внутри) в `artifact-build.html` |
| `og_gen.py` | генерирует `og.png` 1200x630 для превью ссылок |
| `favicon_gen.py` | генерирует `favicon.ico` и `apple-touch-icon.png` |
| `ga_report.py` | читает статистику Google Analytics 4 (нужен `tools/ga-key.json`, см. ниже) |

## Аналитика

**GoatCounter (работает).** Развёрнут на сервере openclaw (Oracle, `141.148.232.49`),
SQLite в `/var/lib/goatcounter/db.sqlite3`, systemd-юнит `goatcounter.service`,
TLS через ACME на 443. Скрипт подключён в `<head>` сайта внутри блока `<!-- ga4 -->`
(этот блок вырезается при сборке артефакта). События: `react/<карточка>/<эмодзи>`
и `feedback/<текст отзыва>` видны в дашборде как отдельные строки.

**Google Analytics 4 (частично).** Тег `G-THYFR0EMHT` стоит на сайте и собирает данные,
но прочитать их через API пока нельзя: нужно, чтобы владелец property
(kirill.krasovitsky@gmail.com) добавил сервис-аккаунт
`claude-ga@dreamcore-analytics.iam.gserviceaccount.com` с ролью Editor в
Admin → Property access management. После этого работает `python tools/ga_report.py`
(ключ сервис-аккаунта: `tools/ga-key.json`, лежит в приватном репозитории `servers`).

## Дизайн

Концепт «Settling Line»: линия горизонта как датум вайпа, карточки сводки висят
на ножках с пинами, таблица-леджер без зебры, CSS-треугольники вместо стрелок,
эпиграф в духе сериала «Чернобыль» под заголовком.

Правила текстов: **никаких длинных тире** (символ `—` допустим только как метка
«нет данных» в колонке изменений).

## Что осталось сделать

- [ ] Сделать дашборд GoatCounter публичным: зайти в Settings → Site → Dashboard visibility → Public.
      Тогда графики открываются без логина, удобно с телефона.
- [ ] Доступ к GA4 через API (шаг Кирилла, описан выше).
- [ ] Винрейт и реалтайм-данные: идея взять OpenDota W-L за сутки для известных игроков,
      требует прописать `account_id` в `notable.json`.
- [ ] Идея дизайн-критика: посадить заголовок hero прямо на линию горизонта.
- [ ] Продвижение: тексты для Telegram-каналов и Reddit готовы, лежат в истории переписки.

## Особенности окружения (старая машина, на новой может не быть)

- `github.com` по HTTPS и API блокировался, работал только SSH на порту 22, причём флаки:
  пуш иногда падает, помогает retry-цикл на 5 попыток.
- Локальный DNS перехватывался VPN и отдавал фейковые адреса `198.18.x.x`, проверять
  записи приходилось через DoH (`https://dns.google/resolve`).
- `analytics.google.com` и `googletagmanager.com` не открывались вообще, поэтому
  собственная аналитика на своём сервере оказалась надёжнее.

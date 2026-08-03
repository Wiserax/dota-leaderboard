# -*- coding: utf-8 -*-
"""Собирает data.js: сравнивает текущий лидерборд Европы с базой до сброса рейтинга.

Запуск:  python build.py           - скачать свежие данные и пересобрать data.js
         python build.py --offline - пересобрать из сохранённого current.json
"""
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
API = "https://www.dota2.com/webapi/ILeaderboard/GetDivisionLeaderboard/v0001?division=europe&leaderboard=0"


def fetch_current():
    req = urllib.request.Request(API, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    (HERE / "current.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def ranks_by_name(board):
    d = {}
    for p in board:
        d.setdefault(p["name"], []).append(p["rank"])
    for v in d.values():
        v.sort()
    return d


def norm(name):
    return name.casefold().strip().strip("`'~.-_ ")


def day_snapshot(board_json):
    return {"time": board_json["time_posted"], "ranks": ranks_by_name(board_json["leaderboard"])}


def main():
    baseline = json.loads((HERE / "baseline_pre_reset.json").read_text(encoding="utf-8"))
    old_current = None
    cur_path = HERE / "current.json"
    if cur_path.exists():
        old_current = json.loads(cur_path.read_text(encoding="utf-8"))
    if "--offline" in sys.argv:
        current = old_current
    else:
        current = fetch_current()

    # скользящее суточное окно, два слота: базе всегда 12-24 часа
    day_path = HERE / "prev_day.json"
    store = json.loads(day_path.read_text(encoding="utf-8")) if day_path.exists() else None
    rotate_src = old_current or current
    if not store or "old" not in store:
        snap = day_snapshot(rotate_src)
        store = {"old": snap, "mid": snap}
    if current["time_posted"] - store["mid"]["time"] >= 43200:
        store["old"] = store["mid"]
        store["mid"] = day_snapshot(rotate_src)
    day = store["old"]
    day_path.write_text(json.dumps(store, ensure_ascii=False), encoding="utf-8")

    notable = set()
    notable_path = HERE / "notable.json"
    if notable_path.exists():
        notable = {norm(n) for n in json.loads(notable_path.read_text(encoding="utf-8"))["nicks"]}

    old_ranks = ranks_by_name(baseline["leaderboard"])
    # Ники не уникальны: одинаковые ники сопоставляем по порядку мест.
    # Указатель, сколько записей этого ника уже израсходовано.
    used = {name: 0 for name in old_ranks}

    players = []
    for p in current["leaderboard"]:
        name = p["name"]
        entry = {
            "r": p["rank"],
            "n": name,
            "t": p.get("team_tag", ""),
            "c": p.get("country", ""),
        }
        if name in old_ranks and used[name] < len(old_ranks[name]):
            old_r = old_ranks[name][used[name]]
            used[name] += 1
            entry["d"] = old_r - p["rank"]  # >0 поднялся, <0 опустился
            if len(old_ranks[name]) > 1:
                entry["a"] = 1  # неоднозначный ник (дубликат)
        else:
            entry["d"] = None  # новичок на лидерборде
        players.append(entry)

    # взлёт за суточное окно (сопоставление дублей ников — по порядку мест)
    day_used = {name: 0 for name in day["ranks"]}
    day_climb = None
    for p in current["leaderboard"]:
        name = p["name"]
        if name in day["ranks"] and day_used[name] < len(day["ranks"][name]):
            old_r = day["ranks"][name][day_used[name]]
            day_used[name] += 1
            dd = old_r - p["rank"]
            if dd > 0 and (day_climb is None or dd > day_climb["d"]):
                day_climb = {"n": name, "d": dd, "r": p["rank"]}

    # самое глубокое падение среди известных игроков
    nf = None
    for p in players:
        if p["d"] is not None and p["d"] < 0 and norm(p["n"]) in notable:
            if nf is None or p["d"] < nf["d"]:
                nf = {"n": p["n"], "d": p["d"], "r": p["r"]}

    out = {
        "division": "europe",
        "baselineTime": baseline["time_posted"],
        "currentTime": current["time_posted"],
        "players": players,
    }
    if day_climb:
        out["day"] = {"t": day["time"], "climb": day_climb}
    if nf:
        out["nf"] = nf
    js = "window.LB = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";"
    (HERE / "data.js").write_text(js, encoding="utf-8")

    ups = [p for p in players if p["d"] is not None and p["d"] > 0]
    downs = [p for p in players if p["d"] is not None and p["d"] < 0]
    new = [p for p in players if p["d"] is None]
    print(f"players: {len(players)}, up: {len(ups)}, down: {len(downs)}, new: {len(new)}")
    top_up = sorted(ups, key=lambda p: -p["d"])[:5]
    top_down = sorted(downs, key=lambda p: p["d"])[:5]
    print("top up:  ", [(p["n"], f"+{p['d']}") for p in top_up])
    print("top down:", [(p["n"], p["d"]) for p in top_down])


if __name__ == "__main__":
    main()

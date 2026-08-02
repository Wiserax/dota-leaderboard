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


def main():
    baseline = json.loads((HERE / "baseline_pre_reset.json").read_text(encoding="utf-8"))
    if "--offline" in sys.argv:
        current = json.loads((HERE / "current.json").read_text(encoding="utf-8"))
    else:
        current = fetch_current()

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

    out = {
        "division": "europe",
        "baselineTime": baseline["time_posted"],
        "currentTime": current["time_posted"],
        "players": players,
    }
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

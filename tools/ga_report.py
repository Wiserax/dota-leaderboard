# -*- coding: utf-8 -*-
"""Читалка статистики GA4 для dota2afterfall.com (Google Analytics Data API).

Использование:
  python tools/ga_report.py        # сводка за 7 дней + реалтайм
  python tools/ga_report.py 28     # за последние 28 дней

Нужен tools/ga-key.json — JSON-ключ сервис-аккаунта (в .gitignore, НЕ коммитить).
Email сервис-аккаунта должен быть добавлен Viewer'ом в Access management GA4 property.
Зависимости: pip install requests PyJWT cryptography
"""
import io
import json
import os
import sys
import time

import jwt
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.environ.get("GA_KEY_FILE", os.path.join(HERE, "ga-key.json"))
SCOPE = "https://www.googleapis.com/auth/analytics.readonly"
DATA = "https://analyticsdata.googleapis.com/v1beta/properties/%s:%s"


TOKEN_FILE = os.path.join(HERE, "ga-token.json")


def get_token():
    # вариант 1: сервис-аккаунт (ga-key.json)
    if os.path.exists(KEY_FILE):
        key = json.load(io.open(KEY_FILE, encoding="utf-8"))
        now = int(time.time())
        assertion = jwt.encode(
            {"iss": key["client_email"], "scope": SCOPE, "aud": key["token_uri"],
             "iat": now, "exp": now + 3600},
            key["private_key"], algorithm="RS256")
        r = requests.post(key["token_uri"], data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion}, timeout=30)
        r.raise_for_status()
        return r.json()["access_token"]
    # вариант 2: user-OAuth refresh token (ga-token.json, создаётся ga_oauth.py)
    if os.path.exists(TOKEN_FILE):
        t = json.load(io.open(TOKEN_FILE, encoding="utf-8"))
        r = requests.post("https://oauth2.googleapis.com/token", data={
            "client_id": t["client_id"], "client_secret": t["client_secret"],
            "refresh_token": t["refresh_token"], "grant_type": "refresh_token"},
            timeout=30)
        r.raise_for_status()
        return r.json()["access_token"]
    raise SystemExit("Нет ни %s, ни %s — сначала запусти tools/ga_oauth.py" % (KEY_FILE, TOKEN_FILE))


def discover_property(hdr):
    r = requests.get(
        "https://analyticsadmin.googleapis.com/v1beta/accountSummaries",
        headers=hdr, timeout=30)
    r.raise_for_status()
    for acc in r.json().get("accountSummaries", []):
        for p in acc.get("propertySummaries", []):
            return p["property"].split("/")[1], p.get("displayName", "?")
    raise SystemExit("Сервис-аккаунт не видит ни одного GA4 property — проверь Access management")


def report(hdr, pid, days, dimensions, metrics, limit=10, order_metric=None):
    body = {
        "dateRanges": [{"startDate": "%ddaysAgo" % days, "endDate": "today"}],
        "dimensions": [{"name": d} for d in dimensions],
        "metrics": [{"name": m} for m in metrics],
        "limit": limit,
    }
    if order_metric:
        body["orderBys"] = [{"metric": {"metricName": order_metric}, "desc": True}]
    elif dimensions == ["date"]:
        body["orderBys"] = [{"dimension": {"dimensionName": "date"}}]
    r = requests.post(DATA % (pid, "runReport"), headers=hdr, json=body, timeout=30)
    r.raise_for_status()
    return r.json().get("rows", [])


def realtime(hdr, pid):
    r = requests.post(DATA % (pid, "runRealtimeReport"), headers=hdr,
                      json={"metrics": [{"name": "activeUsers"}]}, timeout=30)
    r.raise_for_status()
    rows = r.json().get("rows", [])
    return rows[0]["metricValues"][0]["value"] if rows else "0"


def block(title, rows, cols):
    print("\n== %s ==" % title)
    if not rows:
        print("  (пусто)")
        return
    for row in rows:
        dims = [d["value"] for d in row.get("dimensionValues", [])]
        mets = [m["value"] for m in row.get("metricValues", [])]
        print("  " + " | ".join(dims + mets) if dims else "  " + " | ".join(
            "%s=%s" % (c, v) for c, v in zip(cols, mets)))


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    hdr = {"Authorization": "Bearer " + get_token()}
    pid, name = discover_property(hdr)
    print("Property: %s (%s) | период: %d дн." % (name, pid, days))

    totals = report(hdr, pid, days, [], ["activeUsers", "screenPageViews", "sessions",
                                         "averageSessionDuration"])
    block("Итого", totals, ["юзеры", "просмотры", "сессии", "ср.сессия,сек"])
    block("По дням (дата | юзеры | просмотры)",
          report(hdr, pid, days, ["date"], ["activeUsers", "screenPageViews"], limit=40), [])
    block("Страны (топ)", report(hdr, pid, days, ["country"], ["activeUsers"],
                                 order_metric="activeUsers"), [])
    block("Источники (топ)", report(hdr, pid, days, ["sessionSource"], ["sessions"],
                                    order_metric="sessions"), [])
    block("Устройства", report(hdr, pid, days, ["deviceCategory"], ["activeUsers"],
                               order_metric="activeUsers"), [])
    print("\n== Реалтайм ==\n  активных прямо сейчас: %s" % realtime(hdr, pid))


if __name__ == "__main__":
    main()

"""history.json + config.json から実データのダッシュボードHTMLを生成。
口座別DDの加重に使う金額(評価額)は、環境変数 WEIGHTS(JSON: wkey->円) から読む。
リポジトリのファイルには金額を置かない。WEIGHTS未設定なら口座別DDは非表示(—)。"""
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

from dd_lib import load_config, load_history, drawdown_series, BASE

TEMPLATE = BASE / "template.html"
OUT = BASE / "dashboard.html"
WINDOW_DAYS = 365

_wmap = None
_env = os.environ.get("WEIGHTS")
if _env:
    try:
        _wmap = json.loads(_env)
    except Exception:
        _wmap = None


def weight_of(f):
    """金額(加重)を返す。Secret優先、なければconfigのweight、どちらも無ければNone。"""
    if _wmap is not None:
        return _wmap.get(f.get("wkey"))
    return f.get("weight")


def r2(x):
    return None if x is None else round(x, 2)


def main():
    cfg = load_config()
    hist = load_history()
    nav = hist.get("nav", {})

    dd_by_code = {}
    ser_by_code = {}
    for code, navd in nav.items():
        ser = drawdown_series(navd)
        ser_by_code[code] = ser
        dd_by_code[code] = {d: v for d, v in ser}

    all_dates = sorted({d for navd in nav.values() for d in navd})
    if not all_dates:
        raise SystemExit("history.json にデータがありません。fetch_nav.py / backfill.py を先に実行してください。")
    asof = all_dates[-1]
    start = (date.fromisoformat(asof) - timedelta(days=WINDOW_DAYS)).isoformat()
    axis = [d for d in all_dates if d >= start]

    funds_out, table_out = [], []
    for idx, f in enumerate(cfg["funds"]):
        code = f["code"]
        ddmap = dd_by_code.get(code, {})
        funds_out.append({
            "short": f["short"], "type": f["type"], "account": f["account"],
            "idx": idx, "dd": [r2(ddmap.get(d)) for d in axis],
        })
        ser = ser_by_code.get(code, [])
        dd0 = ser[-1][1] if ser else None
        def diff(k):
            if not ser or len(ser) <= k or dd0 is None:
                return None
            return dd0 - ser[-1 - k][1]
        table_out.append({
            "short": f["short"], "account": f["account"], "idx": idx,
            "dd0": r2(dd0), "dDay": r2(diff(1)), "dWk": r2(diff(5)), "dMo": r2(diff(21)),
        })

    accounts = {}
    for acc in ("tn", "dc"):
        members = [f for f in cfg["funds"] if f["account"] == acc]
        ws = [weight_of(f) for f in members]
        now = None
        if all(w is not None for w in ws) and members:
            common = None
            for f in members:
                ds = set(nav.get(f["code"], {}))
                common = ds if common is None else (common & ds)
            if common:
                cds = sorted(common)
                base = cds[0]
                agg = {d: sum(weight_of(f) * nav[f["code"]][d] / nav[f["code"]][base] for f in members) for d in cds}
                now = drawdown_series(agg)[-1][1]
        accounts[acc] = {"now": r2(now)}

    pending = {k: [b["label"] for b in v] for k, v in cfg.get("benchmarks", {}).items() if isinstance(v, list)}

    data = {
        "asof": asof,
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "dates": axis,
        "types": {k: v["name"] for k, v in cfg["types"].items()},
        "type_order": cfg["type_order"],
        "funds": funds_out,
        "table": table_out,
        "accounts": accounts,
        "benchmarks": {},
        "pending_bench": pending,
    }

    html = TEMPLATE.read_text(encoding="utf-8").replace(
        "__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    OUT.write_text(html, encoding="utf-8")
    print(f"生成: {OUT}  (基準日 {asof} / 軸 {len(axis)}日 / 銘柄 {len(funds_out)}本 / {len(html):,} bytes)")
    print(f"  口座計 現在DD  特定+NISA={accounts['tn']['now']}  DC+iDeCo={accounts['dc']['now']}  (WEIGHTS={'あり' if _wmap else 'なし'})")


if __name__ == "__main__":
    main()

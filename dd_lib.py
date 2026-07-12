"""投資信託ドローダウン監視 - 共通ロジック（データ取得・履歴・計算）。"""
import json
import re
import urllib.request
from datetime import date, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
CONFIG = BASE / "config.json"
HISTORY = BASE / "history.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def _get_bytes(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=timeout).read()


def load_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def load_history():
    if HISTORY.exists():
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    return {"updated": None, "nav": {}}


def save_history(hist):
    hist["updated"] = datetime.now().isoformat(timespec="seconds")
    HISTORY.write_text(json.dumps(hist, ensure_ascii=False, indent=1), encoding="utf-8")


# ---- Yahoo!ファイナンスから当日の基準価額 ----
def fetch_current(code):
    """(iso_date, nav:int, name:str) を返す。取得失敗時は None。"""
    html = _get_bytes(f"https://finance.yahoo.co.jp/quote/{code}").decode("utf-8", "replace")
    key = "window.__PRELOADED_STATE__ = "
    i = html.find(key)
    if i < 0:
        return None
    seg = html[i + len(key):]
    depth = 0; instr = False; esc = False; end = None
    for k, ch in enumerate(seg):
        if instr:
            if esc: esc = False
            elif ch == "\\": esc = True
            elif ch == '"': instr = False
        else:
            if ch == '"': instr = True
            elif ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = k + 1
                    break
    data = json.loads(seg[:end])
    hit = []
    def walk(o):
        if isinstance(o, dict):
            if "price" in o and "updateDate" in o:
                hit.append(o)
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(data)
    if not hit:
        return None
    o = hit[0]
    nav = int(str(o["price"]).replace(",", ""))
    iso = _mmdd_to_iso(o["updateDate"])
    name = o.get("nickName") or o.get("name") or code
    return iso, nav, name


def _mmdd_to_iso(mmdd):
    """'07/10' を今年基準でISO日付へ（未来になる場合は前年）。"""
    mm, dd = [int(x) for x in mmdd.split("/")]
    today = date.today()
    y = today.year
    try:
        d = date(y, mm, dd)
    except ValueError:
        d = date(y, mm, min(dd, 28))
    if d > today:
        d = date(y - 1, mm, dd)
    return d.isoformat()


# ---- 投信ライブラリーCSVから設定来の履歴（要ISIN） ----
def fetch_history(isin, code):
    """{iso_date: nav} を返す。取得不可なら None。"""
    if not isin:
        return None
    url = (f"https://toushin-lib.fwg.ne.jp/FdsWeb/FDST030000/csv-file-download"
           f"?isinCd={isin}&associFundCd={code}")
    raw = _get_bytes(url)
    if raw[:1] == b"{":  # {"statusCode":null} = 取得失敗
        return None
    lines = raw.decode("shift_jis", "replace").strip().splitlines()
    out = {}
    for ln in lines[1:]:
        parts = ln.split(",")
        if len(parts) < 2:
            continue
        m = re.match(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})", parts[0])
        if not m:
            continue
        iso = f"{int(m[1]):04d}-{int(m[2]):02d}-{int(m[3]):02d}"
        try:
            out[iso] = int(parts[1].replace(",", ""))
        except ValueError:
            continue
    return out or None


# ---- ドローダウン計算 ----
def drawdown_series(nav_by_date):
    """{date:nav} -> [(date, dd_pct)] 昇順。dd = (nav/その日までのピーク - 1)*100。"""
    out = []
    peak = None
    for d in sorted(nav_by_date):
        v = nav_by_date[d]
        peak = v if peak is None else max(peak, v)
        out.append((d, (v / peak - 1) * 100))
    return out

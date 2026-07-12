"""日次実行：全銘柄の当日基準価額をYahooから取得し history.json に追記。"""
import sys
from dd_lib import load_config, load_history, save_history, fetch_current


def main():
    cfg = load_config()
    hist = load_history()
    nav = hist.setdefault("nav", {})
    codes = {f["code"] for f in cfg["funds"]}  # 同一コードは1回だけ取得
    ok = 0
    for code in sorted(codes):
        try:
            res = fetch_current(code)
        except Exception as e:
            print(f"  ! {code}: {e}", file=sys.stderr)
            continue
        if not res:
            print(f"  ! {code}: 取得できず", file=sys.stderr)
            continue
        iso, v, name = res
        nav.setdefault(code, {})[iso] = v
        ok += 1
        print(f"  {code}  {iso}  {v:>9,}  {name}")
    save_history(hist)
    print(f"更新完了: {ok}/{len(codes)} 銘柄")


if __name__ == "__main__":
    main()

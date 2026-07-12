"""初回のみ実行：ISINのある銘柄の設定来履歴を投信ライブラリーCSVから取り込み。
既存の history.json にマージ（当日Yahoo値は残る）。"""
import sys
from dd_lib import load_config, load_history, save_history, fetch_history


def main():
    cfg = load_config()
    hist = load_history()
    nav = hist.setdefault("nav", {})
    done = 0
    for f in cfg["funds"]:
        isin = f.get("isin")
        code = f["code"]
        if not isin:
            print(f"  - {code} {f['short']}: ISINなし → スキップ（前方蓄積）")
            continue
        if code in nav and len(nav[code]) > 5:
            print(f"  = {code} {f['short']}: 既に履歴あり({len(nav[code])}件) → スキップ")
            continue
        try:
            h = fetch_history(isin, code)
        except Exception as e:
            print(f"  ! {code}: {e}", file=sys.stderr)
            continue
        if not h:
            print(f"  ! {code} {f['short']}: CSV取得失敗", file=sys.stderr)
            continue
        merged = nav.setdefault(code, {})
        merged.update(h)
        done += 1
        ds = sorted(h)
        print(f"  + {code} {f['short']}: {len(h)}件 ({ds[0]}〜{ds[-1]})")
    save_history(hist)
    print(f"バックフィル完了: {done} 銘柄")


if __name__ == "__main__":
    main()

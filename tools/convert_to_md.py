#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""70cityprice filtered CSV -> 结构化 markdown（海口三亚月度指数）"""
import csv
import io

SRC = "/Users/pyemini/projects/70cityprice/projects/70cityprice_filtered.csv"
OUT = "/Users/pyemini/Documents/Hermes Vault/03-文章/现房制专题/数据/海口三亚70城房价指数_202608.md"

rows = list(csv.DictReader(io.open(SRC, encoding="utf-8-sig")))
print(f"读取 {len(rows)} 行")

# 结构: (city, base, idx_col) -> {year: {month: value}}
data = {}
for r in rows:
    y, m, _ = r["DATE"].split("/")
    y = int(y); m = int(m)
    city = r["CITY"]
    base = r["FixedBase"]
    for idx, col in [("新建商品住宅", "CommodityHouseIDX"), ("二手住宅", "SecondHandIDX")]:
        key = (city, base, idx)
        v = r.get(col, "").strip()
        data.setdefault(key, {}).setdefault(y, {})[m] = v

lines = []
lines.append("# 海口、三亚 70 城房价指数（月度，同比/环比）")
lines.append("")
lines.append("> 数据源：国家统计局《70个大中城市商品住宅销售价格变动情况》月度报告（本地 70cityprice 项目全量库，2006 年起维护，每月 15-17 日更新上月数据）")
lines.append("> 提取工具：`projects/70cityprice/tools/extract_70cityprice.py filter --cities 海口 三亚 --start 202001 --end 202608 --fixedbase 同比,环比`")
lines.append("> 提取时间：2026-08-29。指数口径：上月=100（环比）/ 上年同月=100（同比）。2023 年起国家统计局停止公布定基指数，故本表不含定基比。")
lines.append("")
for city in ["海口", "三亚"]:
    for base in ["同比", "环比"]:
        for idx in ["新建商品住宅", "二手住宅"]:
            key = (city, base, idx)
            lines.append(f"## {city} {idx}（{base}%）")
            lines.append("")
            for y in range(2020, 2027):
                months = data.get(key, {}).get(y, {})
                if not months:
                    continue
                cells = []
                for m in range(1, 13):
                    v = months.get(m, "缺失")
                    cells.append(f"{m:02d}:{v}")
                lines.append(f"{y}: " + ", ".join(cells))
            lines.append("")

# 缺口统计
gaps = []
for city in ["海口", "三亚"]:
    for base in ["同比", "环比"]:
        for idx in ["新建商品住宅", "二手住宅"]:
            key = (city, base, idx)
            total = sum(1 for y in range(2020, 2027) for m in range(1, 13)
                        if y < 2026 or m <= 6)
            have = sum(1 for y in range(2020, 2027) for m in range(1, 13)
                       if (y < 2026 or m <= 6) and data.get(key, {}).get(y, {}).get(m, "") not in ("", "缺失"))
            if have < total:
                gaps.append(f"{city}-{idx}-{base}: {have}/{total}")

lines.append("## 缺口与备注")
lines.append("")
lines.append(f"- 覆盖范围：2020-01 至 2026-06（78 个月）× 海口/三亚 × 新建/二手 × 同比/环比")
lines.append(f"- 缺口：{len(gaps)} 个序列存在缺月" if gaps else "- 缺口：无，全部序列完整")
for g in gaps:
    lines.append(f"  - {g}")
lines.append("- 备注：二手住宅指数为官方二手住宅销售价格指数（新建+二手均含分户型，本表只取主指数）")

with io.open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"落盘 {OUT}，{len(lines)} 行")

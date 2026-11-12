#!/usr/bin/env python3
"""生成70城房价综合走势图 — 全国均价 + 北上广深"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti SC', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def main():
    script_dir = Path(__file__).parent
    csv_path = script_dir.parent / '70cityprice.csv'
    df = pd.read_csv(csv_path)
    df['DATE'] = pd.to_datetime(df['DATE'])
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 9), dpi=150)
    
    # ── 图1: 全国70城均价趋势 ──
    ax1 = axes[0]
    for label, col, color, ls in [
        ('新建住宅', 'CommodityHouseIDX', '#E53935', '-'),
        ('二手住宅', 'SecondHandIDX', '#1565C0', '--'),
    ]:
        yoy = df[df['FixedBase'] == '同比']
        national = yoy.groupby('DATE')[col].mean()
        # 只保留 2015+
        national = national[national.index >= '2015-01-01']
        ax1.plot(national.index, national.values, color=color, linewidth=2,
                linestyle=ls, label=label, alpha=0.9)

    ax1.axhline(y=100, color='gray', linestyle=':', alpha=0.4, linewidth=1)
    ax1.set_title('70城住宅价格指数 — 全国均价趋势（同比）', fontsize=15, fontweight='bold', pad=12)
    ax1.set_ylabel('同比指数（上年同月=100）', fontsize=11)
    ax1.legend(loc='lower left', framealpha=0.9, fontsize=10)
    ax1.grid(True, alpha=0.25)
    ax1.set_ylim(90, 112)
    
    # 标注最新值
    latest_new = yoy[yoy['DATE'] == yoy['DATE'].max()]['CommodityHouseIDX'].mean()
    latest_sh = yoy[yoy['DATE'] == yoy['DATE'].max()]['SecondHandIDX'].mean()
    latest_date = yoy['DATE'].max().strftime('%Y年%m月')
    ax1.annotate(f'新建指数{latest_new:.1f}', xy=(yoy['DATE'].max(), latest_new),
                xytext=(15, 15), textcoords='offset points', fontsize=9,
                color='#E53935', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#E53935', alpha=0.6))
    ax1.annotate(f'二手指数{latest_sh:.1f}', xy=(yoy['DATE'].max(), latest_sh),
                xytext=(15, -15), textcoords='offset points', fontsize=9,
                color='#1565C0', fontweight='bold',
                arrowprops=dict(arrowstyle='->', color='#1565C0', alpha=0.6))

    # ── 图2: 北上广深新建住宅分城 ──
    ax2 = axes[1]
    cities = ['北京', '上海', '广州', '深圳']
    colors_city = {'北京': '#E53935', '上海': '#1E88E5', '广州': '#43A047', '深圳': '#FB8C00'}
    
    mask = (df['CITY'].isin(cities)) & (df['FixedBase'] == '同比') & (df['DATE'] >= '2018-01-01')
    data_city = df[mask].copy()
    
    for city in cities:
        cd = data_city[data_city['CITY'] == city].sort_values('DATE')
        ax2.plot(cd['DATE'], cd['CommodityHouseIDX'],
                label=city, color=colors_city[city], linewidth=1.6)

    ax2.axhline(y=100, color='gray', linestyle=':', alpha=0.4, linewidth=1)
    ax2.set_title('北上广深新建商品住宅价格指数（同比，2018至今）', fontsize=15, fontweight='bold', pad=12)
    ax2.set_ylabel('同比指数（上年同月=100）', fontsize=11)
    ax2.legend(loc='upper right', framealpha=0.9, fontsize=10)
    ax2.grid(True, alpha=0.25)
    ax2.set_ylim(85, 130)
    
    # 标注最新
    for city in cities:
        cd = data_city[data_city['CITY'] == city].sort_values('DATE')
        last_val = cd['CommodityHouseIDX'].iloc[-1]
        last_date_idx = cd['DATE'].iloc[-1]
        ax2.annotate(f'{last_val:.1f}', xy=(last_date_idx, last_val),
                    xytext=(5, 0), textcoords='offset points', fontsize=8,
                    color=colors_city[city], fontweight='bold', va='center')

    # 共同信息
    fig.text(0.02, 0.01, f'数据来源：国家统计局 | 更新至{latest_date}',
             fontsize=9, color='gray', alpha=0.7)
    
    plt.tight_layout(rect=[0, 0.03, 1, 1])
    
    output_path = script_dir.parent / 'assets' / '70city_trend_latest.png'
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, bbox_inches='tight', facecolor='white')
    print(f'✅ 图表已保存: {output_path}')
    return str(output_path)

if __name__ == '__main__':
    print(main())

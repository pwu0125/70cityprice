#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
70城房价交互式走势图
基于 Plotly 生成可交互 HTML 图表（支持缩放、悬停提示、图例切换）

使用方法:
    python3 tools/price_trend_interactive.py
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.offline import plot
import webbrowser
from pathlib import Path


def main():
    repo_root = Path(__file__).resolve().parent.parent
    csv_path = repo_root / "70cityprice.csv"
    output_dir = repo_root / "assets"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "price_trend_interactive.html"

    df = pd.read_csv(csv_path, dtype=str)
    df["DATE"] = pd.to_datetime(df["DATE"])
    df["CommodityHouseIDX"] = pd.to_numeric(df["CommodityHouseIDX"], errors="coerce")
    df["SecondHandIDX"] = pd.to_numeric(df["SecondHandIDX"], errors="coerce")

    # 四个一线城市
    cities = ["北京", "上海", "广州", "深圳"]
    colors = {
        "北京": "#E53935",
        "上海": "#1E88E5",
        "广州": "#43A047",
        "深圳": "#FB8C00",
    }

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.55, 0.45],
        subplot_titles=("新建商品住宅价格指数（同比）", "二手住宅价格指数（同比）"),
    )

    for city in cities:
        city_data = df[(df["CITY"] == city) & (df["FixedBase"] == "同比")].sort_values("DATE")

        # 新建商品住宅
        fig.add_trace(
            go.Scatter(
                x=city_data["DATE"],
                y=city_data["CommodityHouseIDX"],
                name=city,
                line=dict(color=colors[city], width=1.5),
                hovertemplate=f"{city}<br>%{{x|%Y-%m}}<br>%{{y:.1f}}<extra></extra>",
            ),
            row=1,
            col=1,
        )

        # 二手住宅
        fig.add_trace(
            go.Scatter(
                x=city_data["DATE"],
                y=city_data["SecondHandIDX"],
                name=city,
                line=dict(color=colors[city], width=1.5),
                showlegend=False,
                hovertemplate=f"{city}<br>%{{x|%Y-%m}}<br>%{{y:.1f}}<extra></extra>",
            ),
            row=2,
            col=1,
        )

    # 基准线
    for row in [1, 2]:
        fig.add_hline(
            y=100,
            line=dict(color="gray", width=1, dash="dash"),
            opacity=0.5,
            row=row,
            col=1,
        )

    fig.update_layout(
        width=1400,
        height=800,
        plot_bgcolor="rgb(255, 255, 255)",
        paper_bgcolor="rgb(255, 255, 255)",
        title={
            "text": "北上广深住宅价格指数走势（同比 · 上年同期=100）",
            "x": 0.5,
            "y": 0.97,
            "xanchor": "center",
            "font": {"size": 18, "color": "#333"},
        },
        legend=dict(
            x=0.01,
            y=0.98,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#ddd",
            borderwidth=1,
            orientation="h",
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="rgba(255,255,255,0.9)"),
    )

    fig.update_xaxes(
        rangeslider=dict(visible=False),
        showgrid=True,
        gridcolor="#eee",
    )
    fig.update_yaxes(
        title_text="新建商品住宅指数",
        showgrid=True,
        gridcolor="#eee",
        zeroline=False,
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text="二手住宅指数",
        showgrid=True,
        gridcolor="#eee",
        zeroline=False,
        row=2,
        col=1,
    )

    # 输出并打开
    html = plot(fig, include_plotlyjs=True, output_type="file", filename=str(output_path), auto_open=False)
    print(f"图表已保存至: {output_path}")

    webbrowser.open(f"file://{output_path}")
    print("已在浏览器中打开。")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
图表工具模块
"""

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import pearsonr
import base64
from io import BytesIO

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


def plot_to_base64(fig):
    """将matplotlib图表转换为base64字符串"""
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format='png', bbox_inches='tight', dpi=100)
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    plt.close(fig)
    return img_base64


def plot_goods_trend_double_axis(goods_id, df):
    """
    绘制商品曝光趋势图和动销条形图（同一张图，双Y轴）
    返回base64编码的图片
    """
    if len(df) == 0:
        return None
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # 计算日期数量
    date_count = df['date_label'].nunique()
    ax.set_title(f"{goods_id}\n（{date_count}个日期）", fontsize=14)
    
    # 左Y轴：曝光趋势图（折线图）
    ax.plot(
        df['date_label'],
        df['impressions'],
        color="tab:blue",
        marker="o",
        linewidth=1,
        label="曝光",
    )
    ax.set_ylabel("曝光", fontsize=12)
    
    # 右Y轴：动销条形图
    ax_sales = ax.twinx()
    ax_sales.bar(
        df['date_label'],
        df['buyers'],
        color="tab:orange",
        alpha=0.4,
        width=0.6,
        label="动销",
    )
    ax_sales.set_ylabel("动销", fontsize=12)
    
    # 设置动销Y轴范围（0-12）和刻度
    sales_ticks = np.arange(0, 13, 1)
    ax_sales.set_ylim(0, 12)
    ax_sales.set_yticks(sales_ticks)
    
    # 设置X轴日期刻度（最多16个刻度点）
    max_ticks = 16
    tick_indices = np.linspace(
        0, len(df) - 1, num=min(max_ticks, len(df))
    ).round().astype(int)
    tick_dates = df.iloc[tick_indices]['date_label']
    ax.set_xticks(tick_dates)
    ax.set_xticklabels(
        tick_dates.dt.strftime("%m-%d"), rotation=45, ha="right", fontsize=10
    )
    
    # 合并图例
    handles1, labels1 = ax.get_legend_handles_labels()
    handles2, labels2 = ax_sales.get_legend_handles_labels()
    ax.legend(
        handles1 + handles2, labels1 + labels2, fontsize=10, loc="upper left"
    )
    
    plt.tight_layout()
    img_base64 = plot_to_base64(fig)
    return img_base64


def plot_impressions_clicks_scatter(goods_id, df):
    """
    绘制曝光和点击的散点图，并计算相关性，绘制3%的线
    返回base64编码的图片和相关系数
    """
    if len(df) == 0 or 'impressions' not in df.columns or 'clicks' not in df.columns:
        return None, None
    
    # 过滤掉0值
    df_filtered = df[(df['impressions'] > 0) & (df['clicks'] > 0)].copy()
    
    if len(df_filtered) == 0:
        return None, None
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # 散点图
    ax.scatter(df_filtered['impressions'], df_filtered['clicks'], 
               alpha=0.6, s=50, color='blue')
    
    # 计算相关性
    correlation, p_value = pearsonr(df_filtered['impressions'], df_filtered['clicks'])
    
    # 绘制3%的线
    max_impressions = df_filtered['impressions'].max()
    x_line = np.linspace(0, max_impressions, 100)
    y_line = x_line * 0.03
    ax.plot(x_line, y_line, 'r--', linewidth=2, label='3% CTR线')
    
    ax.set_xlabel('曝光量', fontsize=12)
    ax.set_ylabel('点击量', fontsize=12)
    ax.set_title(f'{goods_id} - 曝光与点击散点图\n相关系数: {correlation:.4f} (p={p_value:.4f})', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    img_base64 = plot_to_base64(fig)
    return img_base64, correlation


def plot_goods_batch(df, cols=3, marked_dates=None):
    """
    批量展示商品图，每行固定3个小图
    marked_dates: dict {goods_id: [date1, date2, ...]} 标记日期列表，会在折线图上用红点标记
    返回base64编码的图片列表
    """
    if len(df) == 0:
        return []
    
    if marked_dates is None:
        marked_dates = {}
    
    sales_ticks = np.arange(0, 13, 1)
    goods_groups = list(df.groupby("goods_id"))
    chunk_size = cols
    images = []
    
    for start in range(0, len(goods_groups), chunk_size):
        chunk = goods_groups[start : start + chunk_size]
        fig, axes = plt.subplots(
            1, cols, figsize=(cols * 4, 3), constrained_layout=True
        )
        axes = np.atleast_1d(axes)
        
        for ax in axes[len(chunk) :]:
            ax.axis("off")
        
        for idx_ax, (goods_id, sub_df) in enumerate(chunk):
            ax = axes[idx_ax]
            sub = sub_df.sort_values("date")
            ax_sales = ax.twinx()
            
            ax.plot(
                sub["date"],
                sub["Product impressions"],
                color="tab:blue",
                marker="o",
                linewidth=1,
                label="曝光",
            )
            
            # 如果有标记日期，在折线图上用红点标记
            if goods_id in marked_dates and marked_dates[goods_id]:
                marked_dates_list = marked_dates[goods_id]
                # 将标记日期转换为与sub["date"]相同的格式（datetime）
                import pandas as pd
                from datetime import datetime
                
                # 确保标记日期是datetime格式
                marked_dates_dt = []
                for md in marked_dates_list:
                    if isinstance(md, str):
                        try:
                            md_dt = pd.to_datetime(md)
                            marked_dates_dt.append(md_dt)
                        except:
                            continue
                    elif hasattr(md, 'to_pydatetime'):
                        marked_dates_dt.append(md)
                    elif isinstance(md, datetime):
                        marked_dates_dt.append(pd.to_datetime(md))
                
                # 在折线图上标记这些日期
                for md_dt in marked_dates_dt:
                    # 找到sub中对应的日期行
                    matching_rows = sub[sub["date"] == md_dt]
                    if len(matching_rows) > 0:
                        # 在对应的日期位置画红点
                        ax.scatter(
                            md_dt,
                            matching_rows.iloc[0]["Product impressions"],
                            color="red",
                            s=100,
                            marker="o",
                            zorder=5,
                            edgecolors="darkred",
                            linewidths=1.5
                        )
            
            ax_sales.bar(
                sub["date"],
                sub["Buyers"],
                color="tab:orange",
                alpha=0.4,
                width=0.6,
                label="动销",
            )
            
            date_count = sub["date"].nunique()
            ax.set_title(f"{goods_id}\n（{date_count}个日期）", fontsize=9)
            ax.set_ylabel("曝光", fontsize=8)
            ax_sales.set_ylabel("动销", fontsize=8)
            
            ax_sales.set_ylim(0, 12)
            ax_sales.set_yticks(sales_ticks)
            
            max_ticks = 16
            tick_indices = np.linspace(
                0, len(sub) - 1, num=min(max_ticks, len(sub))
            ).round().astype(int)
            tick_dates = sub.iloc[tick_indices]["date"]
            ax.set_xticks(tick_dates)
            ax.set_xticklabels(
                tick_dates.dt.strftime("%m-%d"), rotation=45, ha="right", fontsize=7
            )
            
            if idx_ax == 0:
                handles1, labels1 = ax.get_legend_handles_labels()
                handles2, labels2 = ax_sales.get_legend_handles_labels()
                ax.legend(
                    handles1 + handles2, labels1 + labels2, fontsize=8, loc="upper left"
                )
        
        img_base64 = plot_to_base64(fig)
        images.append(img_base64)
    
    return images


def plot_reason_category_pie(reason_counts):
    """
    绘制Reason类别统计饼图
    参数:
        reason_counts: dict，包含各个类别的数量
            {
                'Out_of_stock': 数量,
                'Secondary_traffic_restricted': 数量,
                'Blocked': 数量,
                'Normal': 数量,
                'None': 数量
            }
    返回base64编码的图片
    """
    # 准备数据
    labels = []
    sizes = []
    # 定义颜色映射（为每个类别指定固定颜色）
    color_map = {
        'Out_of_stock': '#ff9999',
        'Secondary_traffic_restricted': '#66b3ff',
        'Blocked': '#ff6666',
        'Normal': '#99ff99',
        'None': '#cccccc'
    }
    
    # 定义类别顺序
    category_order = ['Out_of_stock', 'Secondary_traffic_restricted', 'Blocked', 'Normal', 'None']
    
    # 只显示数量大于0的类别
    pie_colors = []
    for category in category_order:
        count = reason_counts.get(category, 0)
        if count > 0:
            labels.append(f'{category}\n({count}个)')
            sizes.append(count)
            pie_colors.append(color_map[category])
    
    if len(sizes) == 0:
        return None
    
    # 绘制饼图
    fig, ax = plt.subplots(figsize=(8, 6))
    
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=pie_colors,
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 10}
    )
    
    # 设置标题
    ax.set_title('Reason类别统计', fontsize=14, fontweight='bold', pad=20)
    
    # 确保饼图是圆形
    ax.axis('equal')
    
    plt.tight_layout()
    img_base64 = plot_to_base64(fig)
    return img_base64


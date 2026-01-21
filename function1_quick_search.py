# -*- coding: utf-8 -*-
"""
功能1：快速查找
"""

from db_utils import get_goods_data
from plot_utils import plot_goods_trend_double_axis, plot_impressions_clicks_scatter
from config import get_current_table


def quick_search(goods_id):
    """
    快速查找功能
    返回: {
        'success': bool,
        'data': dict or None,
        'error': str or None
    }
    """
    try:
        table_name = get_current_table()
        sales_table_name = f"{table_name}_Sales"
        
        # 获取数据
        df = get_goods_data(table_name, sales_table_name, goods_id)
        
        if len(df) == 0:
            return {
                'success': False,
                'data': None,
                'error': f'未找到goods_id {goods_id} 的数据'
            }
        
        # 绘制双轴图
        img1 = plot_goods_trend_double_axis(goods_id, df)
        
        # 绘制散点图
        img2, correlation = plot_impressions_clicks_scatter(goods_id, df)
        
        # 数据摘要
        summary = {
            'date_range': f"{df['date_label'].min().strftime('%Y-%m-%d')} 至 {df['date_label'].max().strftime('%Y-%m-%d')}",
            'total_impressions': f"{df['impressions'].sum():,.0f}",
            'avg_impressions': f"{df['impressions'].mean():,.2f}",
            'max_impressions': f"{df['impressions'].max():,.0f}",
            'total_buyers': f"{df['buyers'].sum():,.0f}",
            'days_with_buyers': f"{(df['buyers'] > 0).sum()} 天",
            'correlation': f"{correlation:.4f}" if correlation else "N/A"
        }
        
        return {
            'success': True,
            'data': {
                'goods_id': goods_id,
                'trend_image': img1,
                'scatter_image': img2,
                'summary': summary
            },
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'data': None,
            'error': str(e)
        }


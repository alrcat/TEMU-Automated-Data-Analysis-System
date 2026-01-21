# -*- coding: utf-8 -*-
"""
功能3：优化效果数据
"""

from db_utils import get_optimization_data
from plot_utils import plot_goods_batch
from config import get_current_table


def get_optimization_marked_dates(table_name, field_name):
    """
    获取标记了Video或Price的商品的标记日期
    返回: dict {goods_id: date_label}
    """
    from config import get_db_config
    import pymysql
    
    traffic_config, _, _, _ = get_db_config()
    conn = pymysql.connect(**traffic_config)
    
    try:
        cursor = conn.cursor()
        query = f"""
        SELECT DISTINCT goods_id, date_label
        FROM `{table_name}`
        WHERE `{field_name}` = 1
        ORDER BY goods_id, date_label
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        marked_dates = {}
        for goods_id, date_label in results:
            if goods_id not in marked_dates:
                marked_dates[goods_id] = []
            # 将日期对象转换为字符串（如果是datetime.date对象）
            date_str = str(date_label) if not isinstance(date_label, str) else date_label
            marked_dates[goods_id].append(date_str)
        
        return marked_dates
    finally:
        cursor.close()
        conn.close()


def optimization_effect(field_name):
    """
    优化效果数据功能
    field_name: 'Video' 或 'Price'
    返回: {
        'success': bool,
        'data': dict or None,
        'error': str or None
    }
    """
    try:
        table_name = get_current_table()
        sales_table_name = f"{table_name}_Sales"
        
        # 获取优化数据
        df = get_optimization_data(table_name, sales_table_name, field_name)
        
        if len(df) == 0:
            return {
                'success': True,
                'data': {
                    'field_name': field_name,
                    'images': [],
                    'marked_dates': {},
                    'summary': {}
                },
                'error': None
            }
        
        # 获取标记日期
        marked_dates = get_optimization_marked_dates(table_name, field_name)
        
        # 将标记日期转换为与df["date"]相同的格式（pandas datetime）
        import pandas as pd
        marked_dates_for_plot = {}
        for goods_id, dates_list in marked_dates.items():
            marked_dates_for_plot[goods_id] = []
            for date_str in dates_list:
                try:
                    # 转换为pandas datetime格式，与df["date"]保持一致
                    date_dt = pd.to_datetime(date_str)
                    marked_dates_for_plot[goods_id].append(date_dt)
                except:
                    # 如果转换失败，跳过该日期
                    continue
        
        # 绘制图表，传入标记日期
        images = plot_goods_batch(df, cols=3, marked_dates=marked_dates_for_plot)
        
        # 获取商品信息（包括标记日期）
        goods_info = []
        for goods_id, group in df.groupby('goods_id'):
            dates = marked_dates.get(goods_id, [])
            # 将日期对象转换为字符串
            dates_str = ', '.join(str(d) if not isinstance(d, str) else d for d in dates) if dates else 'N/A'
            goods_info.append({
                'goods_id': goods_id,
                'marked_dates': dates_str
            })
        
        # 基本信息统计
        summary = {
            'total_records': len(df),
            'unique_goods': df['goods_id'].nunique(),
            'date_range': f"{df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}" if 'date' in df.columns else 'N/A'
        }
        
        return {
            'success': True,
            'data': {
                'field_name': field_name,
                'images': images,
                'goods_info': goods_info,
                'marked_dates': marked_dates,
                'summary': summary
            },
            'error': None
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'data': None,
            'error': str(e)
        }


# -*- coding: utf-8 -*-
"""
功能4：手动更新记录
"""

from db_utils import (
    update_reason, update_video, update_price,
    check_date_exists, get_latest_date_label, get_yesterday_date
)
from config import get_current_table


def manual_update_reason(goods_id, date_label, reason):
    """
    手动更新Reason字段
    """
    try:
        table_name = get_current_table()
        
        # 检查日期是否存在
        if not check_date_exists(table_name, goods_id, date_label):
            return {
                'success': False,
                'error': f'日期 {date_label} 下不存在goods_id {goods_id} 的记录'
            }
        
        # 执行更新
        if update_reason(table_name, goods_id, date_label, reason):
            return {
                'success': True,
                'message': f'成功更新：goods_id={goods_id}, date_label={date_label}, Reason={reason}'
            }
        else:
            return {
                'success': False,
                'error': '更新失败：未找到对应的记录'
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def manual_update_video(goods_id, date_label):
    """
    手动更新Video字段
    """
    try:
        table_name = get_current_table()
        
        # 检查日期是否存在
        if not check_date_exists(table_name, goods_id, date_label):
            return {
                'success': False,
                'error': f'日期 {date_label} 下不存在goods_id {goods_id} 的记录'
            }
        
        # 执行更新
        if update_video(table_name, goods_id, date_label):
            return {
                'success': True,
                'message': f'成功更新：goods_id={goods_id}, date_label={date_label}, Video=1'
            }
        else:
            return {
                'success': False,
                'error': '更新失败：未找到对应的记录'
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def manual_update_price(goods_id, date_label):
    """
    手动更新Price字段
    """
    try:
        table_name = get_current_table()
        
        # 检查日期是否存在
        if not check_date_exists(table_name, goods_id, date_label):
            return {
                'success': False,
                'error': f'日期 {date_label} 下不存在goods_id {goods_id} 的记录'
            }
        
        # 执行更新
        if update_price(table_name, goods_id, date_label):
            return {
                'success': True,
                'message': f'成功更新：goods_id={goods_id}, date_label={date_label}, Price=1'
            }
        else:
            return {
                'success': False,
                'error': '更新失败：未找到对应的记录'
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_available_dates(goods_id):
    """
    获取指定goods_id可用的日期列表
    """
    try:
        table_name = get_current_table()
        from config import get_db_config
        import pymysql
        
        traffic_config, _, _, _ = get_db_config()
        conn = pymysql.connect(**traffic_config)
        
        try:
            cursor = conn.cursor()
            query = f"""
            SELECT DISTINCT date_label
            FROM `{table_name}`
            WHERE goods_id = %s
            ORDER BY date_label DESC
            LIMIT 50
            """
            cursor.execute(query, (goods_id,))
            results = cursor.fetchall()
            dates = [row[0] for row in results]
            return {
                'success': True,
                'dates': dates
            }
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'dates': []
        }


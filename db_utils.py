# -*- coding: utf-8 -*-
"""
数据库工具模块
"""

import pymysql
import pandas as pd
from datetime import datetime, timedelta
from config import get_db_config


def get_db_connection(config):
    """获取数据库连接"""
    return pymysql.connect(**config)


def get_available_tables(cursor):
    """获取所有ROA1开头的表"""
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall() if row[0].startswith('ROA1_')]
    return sorted(tables)


def get_yesterday_date():
    """获取昨天的日期字符串（格式：YYYY-MM-DD）"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime('%Y-%m-%d')


def get_goods_data(table_name, sales_table_name, goods_id):
    """
    获取指定goods_id的曝光和动销数据
    返回: DataFrame包含日期、曝光量、动销数据、点击数据
    """
    traffic_config, sales_config, _, _ = get_db_config()
    
    conn = get_db_connection(traffic_config)
    conn_sales = get_db_connection(sales_config)
    
    try:
        cursor = conn.cursor()
        cursor_sales = conn_sales.cursor()
        
        query = f"""
        SELECT 
          t.date_label,
          t.`Product impressions` as impressions,
          t.`Product clicks` as clicks,
          COALESCE(s.Buyers, 0) as buyers
        FROM `Vida_Traffic`.`{table_name}` t
        LEFT JOIN `Vida_Sales`.`{sales_table_name}` s
          ON t.goods_id = s.goods_id
          AND t.date_label = s.date_label
        WHERE t.goods_id = %s
        ORDER BY t.date_label;
        """
        cursor.execute(query, (goods_id,))
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=columns)
        
        # 转换日期格式
        if len(df) > 0:
            df['date_label'] = pd.to_datetime(df['date_label'])
            # 确保数值列为数值类型
            df['impressions'] = pd.to_numeric(df['impressions'], errors='coerce').fillna(0)
            df['clicks'] = pd.to_numeric(df['clicks'], errors='coerce').fillna(0)
            df['buyers'] = pd.to_numeric(df['buyers'], errors='coerce').fillna(0)
        
        return df
    finally:
        cursor.close()
        cursor_sales.close()
        conn.close()
        conn_sales.close()


def build_filter_condition(filter_mode, sales_table_name, target_date):
    """
    构建过滤条件的SQL子句
    filter_mode: 字典，包含'min'和'max'键，None表示不过滤
    返回: (condition_sql, condition_params)
    """
    if filter_mode is None:
        return f"EXISTS (SELECT 1 FROM `Vida_Sales`.`{sales_table_name}` s3 WHERE s3.goods_id = t2.goods_id AND s3.date_label <= %s AND s3.Buyers IS NOT NULL AND s3.Buyers > 0)", [target_date]
    
    min_val = filter_mode.get('min', 0)
    max_val = filter_mode.get('max')
    
    if max_val is not None:
        # 有上限和下限
        condition_sql = f"(SELECT COALESCE(SUM(s3.Buyers), 0) FROM `Vida_Sales`.`{sales_table_name}` s3 WHERE s3.goods_id = t2.goods_id AND s3.date_label <= %s AND s3.Buyers IS NOT NULL) >= %s AND (SELECT COALESCE(SUM(s3.Buyers), 0) FROM `Vida_Sales`.`{sales_table_name}` s3 WHERE s3.goods_id = t2.goods_id AND s3.date_label <= %s AND s3.Buyers IS NOT NULL) <= %s"
        condition_params = [target_date, min_val, target_date, max_val]
    else:
        # 只有下限
        condition_sql = f"(SELECT COALESCE(SUM(s3.Buyers), 0) FROM `Vida_Sales`.`{sales_table_name}` s3 WHERE s3.goods_id = t2.goods_id AND s3.date_label <= %s AND s3.Buyers IS NOT NULL) >= %s"
        condition_params = [target_date, min_val]
    
    return condition_sql, condition_params


def get_dynamic_goods_data(table_name, sales_table_name, status, target_date=None, filter_mode=None):
    """
    获取动销品数据（上升期或非上升期）
    status: 1=上升期, 2=非上升期
    filter_mode: 过滤模式，None=不过滤, 字典格式：{'min': 最小值, 'max': 最大值或None}
    """
    if target_date is None:
        target_date = get_yesterday_date()
    
    traffic_config, sales_config, _, _ = get_db_config()
    
    conn = get_db_connection(traffic_config)
    conn_sales = get_db_connection(sales_config)
    
    try:
        cursor = conn.cursor()
        cursor_sales = conn_sales.cursor()
        
        # 构建过滤条件
        filter_condition, filter_params = build_filter_condition(filter_mode, sales_table_name, target_date)
        
        # 构建查询
        query = f"""
        SELECT 
          t.*,
          s.Buyers
        FROM `Vida_Traffic`.`{table_name}` t
        LEFT JOIN `Vida_Sales`.`{sales_table_name}` s
          ON t.goods_id = s.goods_id
          AND t.date_label = s.date_label
        WHERE t.goods_id IN (
            SELECT DISTINCT t2.goods_id
            FROM `Vida_Traffic`.`{table_name}` t2
            WHERE t2.date_label = %s
              AND t2.Status = %s
              AND EXISTS (
                  SELECT 1
                  FROM `Vida_Sales`.`{sales_table_name}` s2
                  WHERE s2.goods_id = t2.goods_id
              )
              AND {filter_condition}
        )
        ORDER BY t.goods_id, t.date_label;
        """
        cursor.execute(query, [target_date, status] + filter_params)
        
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=columns)
        
        # 数据清洗
        if 'date_label' in df.columns:
            df["date"] = pd.to_datetime(df["date_label"], dayfirst=True, errors="coerce")
            df = df.dropna(subset=["date"])
        
        if "Product impressions" in df.columns:
            df["Product impressions"] = pd.to_numeric(df["Product impressions"], errors="coerce").fillna(0)
        
        if "Product clicks" in df.columns:
            df["Product clicks"] = pd.to_numeric(df["Product clicks"], errors="coerce").fillna(0)
        
        if "Buyers" in df.columns:
            df["Buyers"] = pd.to_numeric(df["Buyers"], errors="coerce").fillna(0)
        
        return df
    finally:
        cursor.close()
        cursor_sales.close()
        conn.close()
        conn_sales.close()


def get_optimization_data(table_name, sales_table_name, field_name, target_date=None):
    """
    获取优化效果数据（Video=1或Price=1）
    field_name: 'Video' 或 'Price'
    """
    if target_date is None:
        target_date = get_yesterday_date()
    
    traffic_config, sales_config, _, _ = get_db_config()
    
    conn = get_db_connection(traffic_config)
    conn_sales = get_db_connection(sales_config)
    
    try:
        cursor = conn.cursor()
        cursor_sales = conn_sales.cursor()
        
        query = f"""
        SELECT 
          t.*,
          s.Buyers
        FROM `Vida_Traffic`.`{table_name}` t
        LEFT JOIN `Vida_Sales`.`{sales_table_name}` s
          ON t.goods_id = s.goods_id
          AND t.date_label = s.date_label
        WHERE t.goods_id IN (
            SELECT DISTINCT t2.goods_id
            FROM `Vida_Traffic`.`{table_name}` t2
            WHERE t2.`{field_name}` = 1
        )
        ORDER BY t.goods_id, t.date_label;
        """
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=columns)
        
        # 数据清洗
        if 'date_label' in df.columns:
            df["date"] = pd.to_datetime(df["date_label"], dayfirst=True, errors="coerce")
            df = df.dropna(subset=["date"])
        
        if "Product impressions" in df.columns:
            df["Product impressions"] = pd.to_numeric(df["Product impressions"], errors="coerce").fillna(0)
        
        if "Buyers" in df.columns:
            df["Buyers"] = pd.to_numeric(df["Buyers"], errors="coerce").fillna(0)
        
        return df
    finally:
        cursor.close()
        cursor_sales.close()
        conn.close()
        conn_sales.close()


def get_filtered_data(table_name, filters, sort_field=None, sort_order='asc', on_shelf_filter_mode=False):
    """
    获取筛选后的数据
    filters: dict，包含筛选条件
    sort_field: 排序字段
    sort_order: 'asc' 或 'desc'
    on_shelf_filter_mode: 是否启用上架时间筛选模式
    """
    traffic_config, _, _, _ = get_db_config()
    
    conn = get_db_connection(traffic_config)
    
    try:
        cursor = conn.cursor()
        
        # 如果启用上架时间筛选模式
        if on_shelf_filter_mode and (filters.get('date_from') or filters.get('date_to')):
            # 先找到所有goods_id的上架日期（第一次出现的date_label）
            query_first_date = f"""
            SELECT goods_id, MIN(date_label) as first_date
            FROM `Vida_Traffic`.`{table_name}`
            GROUP BY goods_id
            """
            cursor.execute(query_first_date)
            first_dates = cursor.fetchall()
            
            # 筛选出上架日期在时间范围内的goods_id
            valid_goods_ids = []
            date_from = filters.get('date_from')
            date_to = filters.get('date_to')
            
            for goods_id, first_date in first_dates:
                # 处理日期类型（可能是字符串或date对象）
                if isinstance(first_date, str):
                    first_date_str = first_date
                elif hasattr(first_date, 'strftime'):
                    first_date_str = first_date.strftime('%Y-%m-%d')
                else:
                    first_date_str = str(first_date)
                
                # 检查是否在时间范围内
                in_range = True
                if date_from and first_date_str < date_from:
                    in_range = False
                if date_to and first_date_str > date_to:
                    in_range = False
                
                if in_range:
                    valid_goods_ids.append(goods_id)
            
            if len(valid_goods_ids) == 0:
                # 没有符合条件的goods_id，返回空DataFrame
                return pd.DataFrame()
            
            # 对于符合条件的goods_id，获取从其上架日期到最新时间的所有数据
            placeholders = ','.join(['%s'] * len(valid_goods_ids))
            
            # 构建其他筛选条件
            where_conditions = []
            params = valid_goods_ids.copy()
            
            # 上架时间筛选模式：只筛选上架日期在范围内的goods_id，然后获取这些goods_id从其上架日期到最新时间的所有数据
            where_conditions.append(f"t.goods_id IN ({placeholders})")
            where_conditions.append(f"t.date_label >= (SELECT MIN(date_label) FROM `Vida_Traffic`.`{table_name}` t2 WHERE t2.goods_id = t.goods_id)")
            
            # 应用其他筛选条件（曝光量、点击量、CTR等）
            if filters.get('impressions_min'):
                where_conditions.append("t.`Product impressions` >= %s")
                params.append(float(filters['impressions_min']))
            
            if filters.get('impressions_max'):
                where_conditions.append("t.`Product impressions` <= %s")
                params.append(float(filters['impressions_max']))
            
            if filters.get('clicks_min'):
                where_conditions.append("t.`Product clicks` >= %s")
                params.append(float(filters['clicks_min']))
            
            if filters.get('clicks_max'):
                where_conditions.append("t.`Product clicks` <= %s")
                params.append(float(filters['clicks_max']))
            
            if filters.get('ctr_min'):
                where_conditions.append("t.CTR >= %s")
                params.append(float(filters['ctr_min']))
            
            if filters.get('ctr_max'):
                where_conditions.append("t.CTR <= %s")
                params.append(float(filters['ctr_max']))
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
            SELECT t.*
            FROM `Vida_Traffic`.`{table_name}` t
            WHERE {where_clause}
            """
            
        else:
            # 普通筛选模式
            # 构建WHERE子句
            where_conditions = []
            params = []
            
            if filters.get('date_from'):
                where_conditions.append("t.date_label >= %s")
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                where_conditions.append("t.date_label <= %s")
                params.append(filters['date_to'])
        
            if filters.get('impressions_min'):
                where_conditions.append("t.`Product impressions` >= %s")
                params.append(float(filters['impressions_min']))
            
            if filters.get('impressions_max'):
                where_conditions.append("t.`Product impressions` <= %s")
                params.append(float(filters['impressions_max']))
            
            if filters.get('clicks_min'):
                where_conditions.append("t.`Product clicks` >= %s")
                params.append(float(filters['clicks_min']))
            
            if filters.get('clicks_max'):
                where_conditions.append("t.`Product clicks` <= %s")
                params.append(float(filters['clicks_max']))
            
            if filters.get('ctr_min'):
                where_conditions.append("t.CTR >= %s")
                params.append(float(filters['ctr_min']))
            
            if filters.get('ctr_max'):
                where_conditions.append("t.CTR <= %s")
                params.append(float(filters['ctr_max']))
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            query = f"""
            SELECT 
              t.*
            FROM `Vida_Traffic`.`{table_name}` t
            WHERE {where_clause}
            """
        
        # 构建ORDER BY子句
        order_clause = ""
        if sort_field:
            order_clause = f"ORDER BY t.`{sort_field}` {sort_order.upper()}"
        
        query = query + f" {order_clause} LIMIT 10000;"
        
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=columns)
        
        return df
    finally:
        cursor.close()
        conn.close()


def check_date_exists(table_name, goods_id, date_label):
    """检查指定goods_id和date_label是否存在"""
    traffic_config, _, _, _ = get_db_config()
    conn = get_db_connection(traffic_config)
    
    try:
        cursor = conn.cursor()
        query = f"""
        SELECT COUNT(*) 
        FROM `{table_name}` 
        WHERE goods_id = %s AND date_label = %s
        """
        cursor.execute(query, (goods_id, date_label))
        result = cursor.fetchone()
        return result[0] > 0 if result else False
    finally:
        cursor.close()
        conn.close()


def update_reason(table_name, goods_id, date_label, reason):
    """更新Reason字段"""
    traffic_config, _, _, _ = get_db_config()
    conn = get_db_connection(traffic_config)
    
    try:
        cursor = conn.cursor()
        query = f"""
        UPDATE `{table_name}` 
        SET Reason = %s 
        WHERE goods_id = %s AND date_label = %s
        """
        cursor.execute(query, (reason, goods_id, date_label))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()


def update_video(table_name, goods_id, date_label):
    """更新Video字段为1"""
    traffic_config, _, _, _ = get_db_config()
    conn = get_db_connection(traffic_config)
    
    try:
        cursor = conn.cursor()
        query = f"""
        UPDATE `{table_name}` 
        SET Video = 1 
        WHERE goods_id = %s AND date_label = %s
        """
        cursor.execute(query, (goods_id, date_label))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()


def update_price(table_name, goods_id, date_label):
    """更新Price字段为1"""
    traffic_config, _, _, _ = get_db_config()
    conn = get_db_connection(traffic_config)
    
    try:
        cursor = conn.cursor()
        query = f"""
        UPDATE `{table_name}` 
        SET Price = 1 
        WHERE goods_id = %s AND date_label = %s
        """
        cursor.execute(query, (goods_id, date_label))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()


def get_latest_date_label(table_name, goods_id):
    """获取指定goods_id最近的date_label"""
    traffic_config, _, _, _ = get_db_config()
    conn = get_db_connection(traffic_config)
    
    try:
        cursor = conn.cursor()
        query = f"""
        SELECT date_label 
        FROM `{table_name}` 
        WHERE goods_id = %s 
        ORDER BY date_label DESC 
        LIMIT 1
        """
        cursor.execute(query, (goods_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        cursor.close()
        conn.close()


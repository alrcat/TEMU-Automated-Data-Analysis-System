# -*- coding: utf-8 -*-
"""
功能2：动销品管理
问题：
    当选定日期时候会出现未来的动销日期
    部分上升期和非上升期数据变动不对应
"""

from db_utils import get_dynamic_goods_data, get_yesterday_date
from plot_utils import plot_goods_batch
from config import get_current_table
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta


def check_columns_exist(cursor, table_name, columns):
    """检查表中是否存在指定列"""
    cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
    existing_columns = [row[0] for row in cursor.fetchall()]
    return all(col in existing_columns for col in columns)


def create_columns_if_not_exist(cursor, table_name):
    """如果Status、Reason、Video、Price列不存在，则创建它们"""
    columns_to_check = ['Status', 'Reason', 'Video', 'Price']
    missing_columns = []
    
    for col in columns_to_check:
        if not check_columns_exist(cursor, table_name, [col]):
            missing_columns.append(col)
    
    if missing_columns:
        print(f"检测到表 {table_name} 缺少以下列，正在创建: {', '.join(missing_columns)}")
        
        # 检查并创建Status列
        if 'Status' in missing_columns:
            cursor.execute(f"""
                ALTER TABLE `{table_name}` 
                ADD COLUMN `Status` INT DEFAULT NULL COMMENT '状态: 1=上升期, 2=过了上升期'
            """)
            print(f"已创建 Status 列")
        
        # 检查并创建Reason列
        if 'Reason' in missing_columns:
            cursor.execute(f"""
                ALTER TABLE `{table_name}` 
                ADD COLUMN `Reason` VARCHAR(255) DEFAULT NULL COMMENT '原因说明'
            """)
            print(f"已创建 Reason 列")
        
        # 检查并创建Video列
        if 'Video' in missing_columns:
            cursor.execute(f"""
                ALTER TABLE `{table_name}` 
                ADD COLUMN `Video` VARCHAR(500) DEFAULT NULL COMMENT '视频链接'
            """)
            print(f"已创建 Video 列")
        
        # 检查并创建Price列
        if 'Price' in missing_columns:
            cursor.execute(f"""
                ALTER TABLE `{table_name}` 
                ADD COLUMN `Price` DECIMAL(10, 2) DEFAULT NULL COMMENT '价格'
            """)
            print(f"已创建 Price 列")
        
        return True
    else:
        print(f"表 {table_name} 已包含所有必需列，跳过创建")
        return False


def analyze_trend(impressions_series):
    """
    分析曝光趋势
    返回: 'rising' (上升期) 或 'declined' (过了上升期)
    """
    if len(impressions_series) < 3:
        return 'rising'
    
    values = np.array(impressions_series)
    max_value = np.max(values)
    max_index = np.argmax(values)
    
    if max_index == len(values) - 1:
        return 'rising'
    
    current_value = values[-1]
    if max_value > 0:
        decline_ratio = (max_value - current_value) / max_value
        if decline_ratio > 0.3:
            return 'declined'
    
    if len(values) >= 7:
        recent_values = values[-7:]
        recent_dates = np.arange(len(recent_values))
        slope = np.polyfit(recent_dates, recent_values, 1)[0]
        
        if slope < 0 and max_value > 0:
            if (max_value - current_value) / max_value > 0.2:
                return 'declined'
    
    return 'rising'


def check_recent_rising_trend(impressions_series, days=7, threshold=0.2):
    """检查近期上升趋势是否明显"""
    if len(impressions_series) < days:
        return False
    
    recent_values = impressions_series[-days:]
    if len(recent_values) < 3:
        return False
    
    recent_dates = np.arange(len(recent_values))
    slope = np.polyfit(recent_dates, recent_values, 1)[0]
    
    if slope > 0:
        start_value = recent_values[0]
        end_value = recent_values[-1]
        if start_value > 0:
            growth_ratio = (end_value - start_value) / start_value
            if growth_ratio > threshold:
                return True
    
    return False


def check_all_goods_have_data_on_date(cursor, table_name, sales_table_name, check_date):
    """
    检查指定日期是否所有动销商品都有数据
    返回: (all_have_data, goods_with_data_count, total_goods_count)
    """
    # 获取目标日期有动销的所有goods_id
    query_total = f"""
    SELECT COUNT(DISTINCT t.goods_id) as count
    FROM `Vida_Traffic`.`{table_name}` t
    WHERE t.date_label = %s
      AND EXISTS (
          SELECT 1
          FROM `Vida_Sales`.`{sales_table_name}` s
          WHERE s.goods_id = t.goods_id AND s.date_label = %s
      )
    """
    cursor.execute(query_total, (check_date, check_date))
    result = cursor.fetchone()
    total_count = result[0] if result else 0
    
    # 获取检查日期有Status数据的goods_id数量
    query_with_status = f"""
    SELECT COUNT(DISTINCT t.goods_id) as count
    FROM `Vida_Traffic`.`{table_name}` t
    WHERE t.date_label = %s
      AND t.Status IS NOT NULL
      AND EXISTS (
          SELECT 1
          FROM `Vida_Sales`.`{sales_table_name}` s
          WHERE s.goods_id = t.goods_id AND s.date_label = %s
      )
    """
    cursor.execute(query_with_status, (check_date, check_date))
    result = cursor.fetchone()
    with_status_count = result[0] if result else 0
    
    return with_status_count == total_count and total_count > 0, with_status_count, total_count


def find_latest_date_with_data(cursor, table_name, sales_table_name, start_date, max_days_back=30):
    """
    从指定日期往前查找，找到所有goods_id都有数据的最近日期
    返回: (found_date, days_back) 或 (None, None)
    """
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    
    for days_back in range(1, max_days_back + 1):
        check_date = (start_dt - timedelta(days=days_back)).strftime('%Y-%m-%d')
        all_have_data, _, _ = check_all_goods_have_data_on_date(cursor, table_name, sales_table_name, check_date)
        
        if all_have_data:
            return check_date, days_back
    
    return None, None


def get_previous_day_status(cursor, table_name, sales_table_name, goods_id, target_date):
    """
    获取goods_id在目标日期前一天的状态
    增加特殊处理：
    1. 如果前一天没有数据，但该goods_id之前有status，检查其他goods_id前一天是否有数据
    2. 如果其他都有数据，只有这个没有，可能是缺货/下架，返回(True, 2, 'out_of_stock')
    3. 如果所有goods_id前一天都没有数据，往前找有数据的日期，尝试导入数据
    返回: (has_status, status, special_note)
    special_note: None, 'out_of_stock', 'data_imported', 'data_missing'
    """
    target_dt = datetime.strptime(target_date, '%Y-%m-%d')
    previous_day = (target_dt - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 先检查该goods_id前一天是否有Status数据
    query = f"""
    SELECT `Status`
    FROM `{table_name}`
    WHERE `goods_id` = %s AND `date_label` = %s AND `Status` IS NOT NULL
    """
    cursor.execute(query, (goods_id, previous_day))
    result = cursor.fetchone()
    
    if result and result[0] is not None:
        return True, result[0], None
    
    # 前一天没有Status数据，检查该goods_id之前是否有status历史
    query_history = f"""
    SELECT COUNT(*) 
    FROM `{table_name}`
    WHERE `goods_id` = %s AND `Status` IS NOT NULL AND `date_label` < %s
    """
    cursor.execute(query_history, (goods_id, target_date))
    has_history = cursor.fetchone()[0] > 0
    
    if has_history:
        # 该goods_id之前有status，检查其他goods_id前一天是否有数据
        all_have_data, goods_with_data, total_goods = check_all_goods_have_data_on_date(
            cursor, table_name, sales_table_name, previous_day
        )
        
        if all_have_data or (goods_with_data > 0 and goods_with_data >= total_goods - 1):
            # 其他goods_id都有数据（或只有这一个没有），可能是缺货/下架
            return True, 2, 'out_of_stock'
    
    # 检查所有goods_id前一天是否都没有数据
    all_have_data, goods_with_data, total_goods = check_all_goods_have_data_on_date(
        cursor, table_name, sales_table_name, previous_day
    )
    
    if not all_have_data and goods_with_data == 0:
        # 所有goods_id前一天都没有数据，往前找有数据的日期
        found_date, days_back = find_latest_date_with_data(
            cursor, table_name, sales_table_name, previous_day, max_days_back=30
        )
        
        if found_date:
            # 找到了有数据的日期，检查从found_date到previous_day之间是否有数据缺失
            # 尝试导入缺失的数据（导入到昨天）
            from db_utils import get_yesterday_date
            yesterday = get_yesterday_date()
            import_success, import_message, imported_count, missing_dates = import_missing_data_for_date_range(
                cursor, table_name, sales_table_name, found_date, yesterday
            )
            
            if import_success:
                # 导入成功（即使有部分日期缺失数据），重新查询前一天的状态
                cursor.execute(query, (goods_id, previous_day))
                result = cursor.fetchone()
                if result and result[0] is not None:
                    print(f"{previous_day}日期没有导入数据，已从数据库导入")
                    return True, result[0], 'data_imported'
                elif len(missing_dates) > 0 and previous_day in missing_dates:
                    # 前一天的数据缺失，无法计算status
                    print(f"数据库没有{previous_day}日期的信息，无法计算status，请手动导入数据到数据库")
                    return False, None, 'data_missing'
            else:
                # 导入失败，检查是否数据库真的缺少数据
                # 检查found_date之后是否有任何goods_id的数据
                check_query = f"""
                SELECT COUNT(DISTINCT goods_id)
                FROM `{table_name}`
                WHERE date_label > %s AND date_label <= %s
                """
                cursor.execute(check_query, (found_date, previous_day))
                result = cursor.fetchone()
                if result and result[0] == 0:
                    # 数据库确实缺少这个日期范围的数据
                    print(f"数据库没有{previous_day}日期的信息，请手动导入数据到数据库")
                    return False, None, 'data_missing'
    
    return False, None, None


def import_missing_data_for_date_range(cursor, table_name, sales_table_name, from_date, to_date):
    """
    尝试导入指定日期范围内的缺失status数据
    从数据库那天的数据计算status，一直导入到to_date（通常是昨天）
    如果数据库没有数据可供status计算，就报告数据库缺失数据
    返回: (success, message, imported_count, missing_dates)
    """
    from datetime import datetime, timedelta
    
    imported_count = 0
    missing_dates = []
    
    # 将日期字符串转换为datetime对象
    from_dt = datetime.strptime(from_date, '%Y-%m-%d')
    to_dt = datetime.strptime(to_date, '%Y-%m-%d')
    
    # 遍历从from_date到to_date的每一天
    current_date = from_dt + timedelta(days=1)  # 从from_date的下一天开始
    while current_date <= to_dt:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # 检查该日期是否有数据可供status计算
        # 需要检查是否有动销商品的数据（Traffic表和Sales表）
        check_query = f"""
        SELECT COUNT(DISTINCT t.goods_id) as count
        FROM `Vida_Traffic`.`{table_name}` t
        WHERE t.date_label = %s
          AND EXISTS (
              SELECT 1
              FROM `Vida_Sales`.`{sales_table_name}` s
              WHERE s.goods_id = t.goods_id AND s.date_label = %s
          )
        """
        cursor.execute(check_query, (date_str, date_str))
        result = cursor.fetchone()
        goods_count = result[0] if result else 0
        
        if goods_count == 0:
            # 数据库没有该日期的数据
            missing_dates.append(date_str)
            current_date += timedelta(days=1)
            continue
        
        # 有数据，尝试计算并导入status
        # 获取该日期有动销的商品
        goods_query = f"""
        SELECT DISTINCT t.goods_id
        FROM `Vida_Traffic`.`{table_name}` t
        WHERE t.date_label = %s
          AND EXISTS (
              SELECT 1
              FROM `Vida_Sales`.`{sales_table_name}` s
              WHERE s.goods_id = t.goods_id AND s.date_label = %s
          )
        """
        cursor.execute(goods_query, (date_str, date_str))
        goods_ids = [row[0] for row in cursor.fetchall()]
        
        if len(goods_ids) == 0:
            missing_dates.append(date_str)
            current_date += timedelta(days=1)
            continue
        
        # 获取这些商品的历史数据用于趋势分析
        placeholders = ','.join(['%s'] * len(goods_ids))
        history_query = f"""
        SELECT 
          t.goods_id,
          t.date_label,
          t.`Product impressions`
        FROM `Vida_Traffic`.`{table_name}` t
        WHERE t.goods_id IN ({placeholders})
          AND t.date_label <= %s
        ORDER BY t.goods_id, t.date_label
        """
        cursor.execute(history_query, goods_ids + [date_str])
        history_data = cursor.fetchall()
        
        if len(history_data) == 0:
            missing_dates.append(date_str)
            current_date += timedelta(days=1)
            continue
        
        # 构建DataFrame用于趋势分析
        df_history = pd.DataFrame(history_data, columns=['goods_id', 'date_label', 'Product impressions'])
        df_history['Product impressions'] = pd.to_numeric(df_history['Product impressions'], errors='coerce').fillna(0)
        
        # 对每个商品分析趋势并更新Status
        updates = []
        for goods_id in goods_ids:
            goods_data = df_history[df_history['goods_id'] == goods_id].sort_values('date_label')
            
            if len(goods_data) == 0:
                continue
            
            impressions = goods_data['Product impressions'].values
            
            # 分析趋势
            trend = analyze_trend(impressions)
            status = 1 if trend == 'rising' else 2
            
            updates.append({
                'goods_id': goods_id,
                'status': status
            })
        
        # 更新Status
        for update in updates:
            goods_id = update['goods_id']
            new_status = update['status']
            
            # 检查该商品在该日期是否有记录
            check_query = f"""
            SELECT COUNT(*) 
            FROM `{table_name}`
            WHERE goods_id = %s AND date_label = %s
            """
            cursor.execute(check_query, (goods_id, date_str))
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                update_sql = f"""
                UPDATE `{table_name}`
                SET `Status` = %s
                WHERE `goods_id` = %s AND `date_label` = %s
                """
                cursor.execute(update_sql, (new_status, goods_id, date_str))
                if cursor.rowcount > 0:
                    imported_count += 1
        
        current_date += timedelta(days=1)
    
    # 提交事务
    try:
        cursor.connection.commit()
    except:
        cursor.connection.rollback()
        return False, "导入数据时发生错误", 0, missing_dates
    
    if len(missing_dates) > 0:
        return True, f"成功导入 {imported_count} 条status数据，但以下日期数据库缺失数据: {', '.join(missing_dates)}", imported_count, missing_dates
    else:
        return True, f"成功导入 {imported_count} 条status数据", imported_count, []


def check_goods_has_any_data_before_date(cursor, table_name, goods_id, target_date):
    """
    检查goods_id在目标日期之前是否有任何数据（包括Status数据）
    返回: bool
    """
    query = f"""
    SELECT COUNT(*) 
    FROM `{table_name}`
    WHERE `goods_id` = %s AND `date_label` < %s
    """
    cursor.execute(query, (goods_id, target_date))
    count = cursor.fetchone()[0]
    return count > 0


def get_recent_history_status(cursor, table_name, goods_id, target_date):
    """
    获取goods_id在目标日期之前的最近一次历史状态
    返回: (has_status, recent_status) 或 (False, None)
    """
    query = f"""
    SELECT `Status`
    FROM `{table_name}`
    WHERE `goods_id` = %s AND `Status` IS NOT NULL AND `date_label` < %s
    ORDER BY `date_label` DESC
    LIMIT 1
    """
    cursor.execute(query, (goods_id, target_date))
    result = cursor.fetchone()
    
    if result and result[0] is not None:
        return True, result[0]
    
    return False, None


def get_status_statistics(table_name, sales_table_name, target_date):
    """
    获取状态统计信息（包含变更统计）
    返回统计字典
    """
    from config import get_db_config
    import pymysql
    
    traffic_config, sales_config, pallet_config, product_config = get_db_config()
    conn = pymysql.connect(**traffic_config)
    conn_sales = pymysql.connect(**sales_config)
    
    try:
        cursor = conn.cursor()
        cursor_sales = conn_sales.cursor()
        
        # 获取所有动销品goods_id（包括下架缺货的）
        all_sales_goods = get_active_sales_goods_ids(table_name, sales_table_name)
        
        # 获取前一天日期
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        previous_day = (target_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 获取前一天上升期的商品数量和goods_id列表
        query_previous_rising = f"""
        SELECT DISTINCT t.goods_id
        FROM `Vida_Traffic`.`{table_name}` t
        WHERE t.date_label = %s
          AND t.Status = 1
          AND EXISTS (
              SELECT 1
              FROM `Vida_Sales`.`{sales_table_name}` s
              WHERE s.goods_id = t.goods_id
          )
        """
        cursor.execute(query_previous_rising, (previous_day,))
        previous_rising_goods = [row[0] for row in cursor.fetchall()]
        previous_rising_count = len(previous_rising_goods)
        
        # 获取上升期的商品数量（选定日期有Status=1的）- 实际上升期
        query_rising = f"""
        SELECT DISTINCT t.goods_id
        FROM `Vida_Traffic`.`{table_name}` t
        WHERE t.date_label = %s
          AND t.Status = 1
          AND EXISTS (
              SELECT 1
              FROM `Vida_Sales`.`{sales_table_name}` s
              WHERE s.goods_id = t.goods_id
          )
        """
        cursor.execute(query_rising, (target_date,))
        actual_rising_goods = [row[0] for row in cursor.fetchall()]
        rising_count = len(actual_rising_goods)
        
        # 获取非上升期的商品数量（包括Status=2的和下架缺货的）
        # 1. 获取选定日期有Status=2的商品
        query_status_2 = f"""
        SELECT DISTINCT t.goods_id
        FROM `Vida_Traffic`.`{table_name}` t
        WHERE t.date_label = %s
          AND t.Status = 2
          AND EXISTS (
              SELECT 1
              FROM `Vida_Sales`.`{sales_table_name}` s
              WHERE s.goods_id = t.goods_id
          )
        """
        cursor.execute(query_status_2, (target_date,))
        status_2_goods = [row[0] for row in cursor.fetchall()]
        
        # 2. 获取下架缺货的商品（在target_date没有数据，但之前有动销记录）
        if len(all_sales_goods) > 0:
            placeholders = ','.join(['%s'] * len(all_sales_goods))
            query_discontinued = f"""
            SELECT DISTINCT s.goods_id
            FROM `Vida_Sales`.`{sales_table_name}` s
            WHERE s.goods_id IN ({placeholders})
              AND s.Buyers IS NOT NULL 
              AND s.Buyers > 0
              AND s.goods_id NOT IN (
                  SELECT DISTINCT t.goods_id
                  FROM `Vida_Traffic`.`{table_name}` t
                  WHERE t.date_label = %s
              )
              AND s.goods_id IN (
                  SELECT DISTINCT t2.goods_id
                  FROM `Vida_Traffic`.`{table_name}` t2
                  WHERE t2.date_label < %s
              )
            """
            cursor.execute(query_discontinued, all_sales_goods + [target_date, target_date])
            discontinued_goods = [row[0] for row in cursor.fetchall()]
        else:
            discontinued_goods = []
        
        # 合并所有非上升期商品（Status=2 + 下架缺货）
        all_declined_goods = list(set(status_2_goods + discontinued_goods))
        declined_count = len(all_declined_goods)
        
        # 获取所有动销商品及其曝光数据用于分析变更
        # 需要包含所有在选定日期有Status=1或Status=2的商品，以及前一天没有Status但选定日期有Status的商品
        query_all = f"""
        SELECT 
          t.goods_id,
          t.date_label,
          t.`Product impressions`,
          t.`Status`
        FROM `Vida_Traffic`.`{table_name}` t
        WHERE t.date_label = %s
          AND t.Status IN (1, 2)
          AND EXISTS (
              SELECT 1
              FROM `Vida_Sales`.`{sales_table_name}` s
              WHERE s.goods_id = t.goods_id
          )
        ORDER BY t.goods_id
        """
        cursor.execute(query_all, (target_date,))
        current_goods = cursor.fetchall()
        
        # 获取所有在选定日期有Status=1的商品ID（用于验证）
        query_rising_goods = f"""
        SELECT DISTINCT t.goods_id
        FROM `Vida_Traffic`.`{table_name}` t
        WHERE t.date_label = %s
          AND t.Status = 1
          AND EXISTS (
              SELECT 1
              FROM `Vida_Sales`.`{sales_table_name}` s
              WHERE s.goods_id = t.goods_id
          )
        """
        cursor.execute(query_rising_goods, (target_date,))
        all_rising_goods_ids = set([row[0] for row in cursor.fetchall()])
        
        # 获取current_goods中的Status=1的商品ID
        current_rising_goods_ids = set([row[0] for row in current_goods if row[3] == 1])
        
        # 检查是否有遗漏的Status=1商品（这些商品在变更统计中可能被遗漏）
        missing_rising_goods = all_rising_goods_ids - current_rising_goods_ids
        
        # 获取历史数据用于分析趋势
        if len(current_goods) > 0:
            goods_ids = [row[0] for row in current_goods]
            placeholders = ','.join(['%s'] * len(goods_ids))
            query_history = f"""
            SELECT 
              t.goods_id,
              t.date_label,
              t.`Product impressions`,
              t.`Status`
            FROM `Vida_Traffic`.`{table_name}` t
            WHERE t.goods_id IN ({placeholders})
            ORDER BY t.goods_id, t.date_label
            """
            cursor.execute(query_history, goods_ids)
            history_data = cursor.fetchall()
        else:
            history_data = []
        
        # 构建DataFrame
        df_history = pd.DataFrame(history_data, columns=['goods_id', 'date_label', 'Product impressions', 'Status'])
        if len(df_history) > 0:
            df_history['date_label'] = pd.to_datetime(df_history['date_label'])
            df_history['Product impressions'] = pd.to_numeric(df_history['Product impressions'], errors='coerce').fillna(0)
        
        # 统计变更类型
        new_rising = 0
        new_declined = 0
        updated_to_rising = 0
        back_to_rising = 0
        declined_from_rising = 0
        
        # 记录每个分类的goods_id列表
        new_rising_goods = []
        new_declined_goods = []
        updated_to_rising_goods = []
        back_to_rising_goods = []
        declined_from_rising_goods = []
        
        # 记录特殊说明
        special_notes = []  # 存储特殊说明信息
        
        for goods_id, date_label, impressions, status in current_goods:
            # 获取前一天的状态（包含特殊处理）
            has_previous_day, previous_status, special_note = get_previous_day_status(
                cursor, table_name, sales_table_name, goods_id, target_date
            )
            
            # 处理特殊说明
            if special_note == 'out_of_stock':
                previous_day = (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
                special_notes.append(f"goods id {goods_id}查询日期的前一日({previous_day})单独没有status数据，可能缺货下架了")
                # 将前一天状态设为2（缺货/下架）
                previous_status = 2
                has_previous_day = True
            elif special_note == 'data_missing':
                previous_day = (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
                special_notes.append(f"数据库没有{previous_day}日期的信息，请手动导入数据到数据库")
            
            # 检查goods_id在选定日期前是否有任何数据（用于判断是否为新增）
            has_any_data_before = check_goods_has_any_data_before_date(cursor, table_name, goods_id, target_date)
            
            # 获取该商品的曝光数据用于判断趋势
            goods_data = df_history[df_history['goods_id'] == goods_id].sort_values('date_label')
            impressions_series = goods_data['Product impressions'].values if len(goods_data) > 0 else []
            
            if status == 1:  # 当前状态为上升期
                if not has_previous_day:
                    # 前一天没有数据
                    # 检查历史是否有Status数据（不仅仅是Traffic数据）
                    has_recent_status, recent_status = get_recent_history_status(cursor, table_name, goods_id, target_date)
                    
                    if not has_recent_status:
                        # 历史没有Status数据 → 新增上升期
                        new_rising += 1
                        new_rising_goods.append(goods_id)
                    else:
                        # 历史有Status数据，但前一天没有（可能是缺货后恢复）
                        if recent_status == 2:
                            # 最近历史为2 → 由非上升期重回上升期
                            back_to_rising += 1
                            back_to_rising_goods.append(goods_id)
                        elif recent_status == 1:
                            # 最近历史为1，但前一天没有数据（可能是缺货后恢复，之前是上升期）
                            # 这种情况算作"更新为上升期"（因为之前就是上升期，只是中间缺货了）
                            updated_to_rising += 1
                            updated_to_rising_goods.append(goods_id)
                        else:
                            # 其他情况，算作"更新为上升期"
                            updated_to_rising += 1
                            updated_to_rising_goods.append(goods_id)
                elif previous_status == 1:
                    # 前一天是1，选定日期也是1 → 不记录（保持上升期）
                    pass
                elif previous_status == 2:
                    # 前一天是2，选定日期是1 → 由非上升期重回上升期（简化判断，不检查上升趋势）
                    back_to_rising += 1
                    back_to_rising_goods.append(goods_id)
            elif status == 2:  # 当前状态为非上升期
                if not has_previous_day:
                    # 前一天没有数据
                    if not has_any_data_before:
                        # 选定日期前一直没有数据 → 新增非上升期
                        new_declined += 1
                        new_declined_goods.append(goods_id)
                    else:
                        # 选定日期前有数据，但前一天没有
                        # 这种情况可能是缺货了，但他动销，所以可能存在个别的goods_id没有数据了
                        # 这种就放在2中不管，status一直为2，不记录变更
                        pass
                elif previous_status == 2:
                    # 前一天是2，选定日期也是2 → 不记录（保持非上升期）
                    pass
                elif previous_status == 1:
                    # 前一天是1，选定日期是2 → 由上升期到非上升期
                    declined_from_rising += 1
                    declined_from_rising_goods.append(goods_id)
        
        # 处理遗漏的Status=1商品（这些商品在选定日期有Status=1，但可能前一天没有Status数据）
        # 这些商品应该被统计到变更类型中，以确保统计数量一致
        if len(missing_rising_goods) > 0:
            for goods_id in missing_rising_goods:
                # 获取前一天的状态
                has_previous_day, previous_status, special_note = get_previous_day_status(
                    cursor, table_name, sales_table_name, goods_id, target_date
                )
                
                # 检查goods_id在选定日期前是否有任何数据
                has_any_data_before = check_goods_has_any_data_before_date(cursor, table_name, goods_id, target_date)
                
                # 获取该商品的历史数据用于判断趋势
                query_goods_history = f"""
                SELECT 
                  t.goods_id,
                  t.date_label,
                  t.`Product impressions`,
                  t.`Status`
                FROM `Vida_Traffic`.`{table_name}` t
                WHERE t.goods_id = %s
                ORDER BY t.date_label
                """
                cursor.execute(query_goods_history, (goods_id,))
                goods_history = cursor.fetchall()
                
                if len(goods_history) > 0:
                    df_goods = pd.DataFrame(goods_history, columns=['goods_id', 'date_label', 'Product impressions', 'Status'])
                    df_goods['date_label'] = pd.to_datetime(df_goods['date_label'])
                    df_goods['Product impressions'] = pd.to_numeric(df_goods['Product impressions'], errors='coerce').fillna(0)
                    impressions_series = df_goods['Product impressions'].values
                else:
                    impressions_series = []
                
                # 判断变更类型
                if not has_previous_day:
                    # 前一天没有数据
                    # 检查历史是否有Status数据（不仅仅是Traffic数据）
                    has_recent_status, recent_status = get_recent_history_status(cursor, table_name, goods_id, target_date)
                    
                    if not has_recent_status:
                        # 历史没有Status数据 → 新增上升期
                        new_rising += 1
                        new_rising_goods.append(goods_id)
                    else:
                        # 历史有Status数据，但前一天没有（可能是缺货后恢复）
                        if recent_status == 2:
                            # 最近历史为2 → 由非上升期重回上升期
                            back_to_rising += 1
                            back_to_rising_goods.append(goods_id)
                        elif recent_status == 1:
                            # 最近历史为1，但前一天没有数据 → 更新为上升期
                            updated_to_rising += 1
                            updated_to_rising_goods.append(goods_id)
                        else:
                            # 其他情况，算作"更新为上升期"
                            updated_to_rising += 1
                            updated_to_rising_goods.append(goods_id)
                elif previous_status == 1:
                    # 前一天是1，选定日期也是1 → 不记录（保持上升期）
                    pass
                elif previous_status == 2:
                    # 前一天是2，选定日期是1 → 由非上升期重回上升期（简化判断，不检查上升趋势）
                    back_to_rising += 1
                    back_to_rising_goods.append(goods_id)
        
        # 计算计算上升期
        # 计算上升期 = 前一天上升期数量 + 新增上升期 + 更新为上升期 + 由非上升期重回上升期 - 由上升期到非上升期
        calculated_rising_count = previous_rising_count + new_rising + updated_to_rising + back_to_rising - declined_from_rising
        
        # 计算计算上升期的goods_id列表
        # 前一天上升期的goods_id（排除掉"由上升期到非上升期"的goods_id）
        calculated_rising_goods = set(previous_rising_goods) - set(declined_from_rising_goods)
        # 加上新增上升期、更新为上升期、由非上升期重回上升期的goods_id
        calculated_rising_goods.update(new_rising_goods)
        calculated_rising_goods.update(updated_to_rising_goods)
        calculated_rising_goods.update(back_to_rising_goods)
        calculated_rising_goods = list(calculated_rising_goods)
        
        # 计算差值：计算上升期的goods_id - 实际上升期的goods_id
        calculated_set = set(calculated_rising_goods)
        actual_set = set(actual_rising_goods)
        # 在计算上升期中但不在实际上升期中的goods_id
        diff_in_calculated_not_actual = list(calculated_set - actual_set)
        # 在实际上升期中但不在计算上升期中的goods_id
        diff_in_actual_not_calculated = list(actual_set - calculated_set)
        
        return {
            'date': target_date,
            'rising_count': rising_count,  # 实际上升期
            'calculated_rising_count': calculated_rising_count,  # 计算上升期
            'previous_rising_count': previous_rising_count,  # 前一天上升期数量
            'declined_count': declined_count,
            'new_rising': new_rising,
            'new_declined': new_declined,
            'updated_to_rising': updated_to_rising,
            'back_to_rising': back_to_rising,
            'declined_from_rising': declined_from_rising,
            'new_rising_goods': new_rising_goods,
            'new_declined_goods': new_declined_goods,
            'updated_to_rising_goods': updated_to_rising_goods,
            'back_to_rising_goods': back_to_rising_goods,
            'declined_from_rising_goods': declined_from_rising_goods,
            'calculated_rising_goods': calculated_rising_goods,
            'actual_rising_goods': actual_rising_goods,
            'diff_in_calculated_not_actual': diff_in_calculated_not_actual,
            'diff_in_actual_not_calculated': diff_in_actual_not_calculated,
            'special_notes': special_notes
        }
    finally:
        cursor.close()
        cursor_sales.close()
        conn.close()
        conn_sales.close()


def parse_reason_category(reason):
    """
    解析Reason字段，去除括号及括号里面的内容，判断类别
    返回: 'Out_of_stock', 'Secondary_traffic_restricted', 'Blocked', 'Normal', 'None' 之一
    例如：Blocked (XX_Secondary_traffic_restricted_0000) -> 'Blocked'
    """
    import re
    
    if not reason or reason == 'None' or reason == '':
        return 'None'
    
    # 去除括号及括号里面的内容
    reason_cleaned = re.sub(r'\([^)]*\)', '', reason).strip()
    
    # 判断类别（按优先级顺序，Blocked优先于Secondary_traffic_restricted）
    if 'Blocked' in reason_cleaned:
        return 'Blocked'
    elif 'Secondary_traffic_restricted' in reason_cleaned:
        return 'Secondary_traffic_restricted'
    elif 'Out_of_stock' in reason_cleaned:
        return 'Out_of_stock'
    elif 'Normal' in reason_cleaned:
        return 'Normal'
    else:
        return 'None'


def count_reason_categories(goods_info_list):
    """
    统计goods_info列表中各个Reason类别的数量
    参数:
        goods_info_list: list of dict，每个dict包含goods_id和reason字段
    返回: dict，包含各个类别的数量
    """
    counts = {
        'Out_of_stock': 0,
        'Secondary_traffic_restricted': 0,
        'Blocked': 0,
        'Normal': 0,
        'None': 0
    }
    
    for goods_info in goods_info_list:
        reason = goods_info.get('reason', 'None')
        category = parse_reason_category(reason)
        counts[category] = counts.get(category, 0) + 1
    
    return counts


def get_goods_info_with_status(df, table_name, sales_table_name):
    """
    获取商品信息，包括加入时间和Reason
    返回: list of dict
    加入时间：第一个动销的时间（Vida_Sales表中Buyers > 0的最早日期）
    """
    from config import get_db_config
    import pymysql
    
    traffic_config, sales_config, pallet_config, product_config = get_db_config()
    conn = pymysql.connect(**traffic_config)
    conn_sales = pymysql.connect(**sales_config)
    
    try:
        cursor = conn.cursor()
        cursor_sales = conn_sales.cursor()
        goods_info_list = []
        
        # 按照goods_id排序，确保与plot_goods_batch的顺序一致
        for goods_id, group in df.groupby('goods_id', sort=True):
            group_sorted = group.sort_values('date')
            
            # 获取Reason（取最新的非空Reason）
            reason = None
            if 'Reason' in group_sorted.columns:
                reasons = group_sorted['Reason'].dropna()
                reasons = reasons[reasons != '']
                if len(reasons) > 0:
                    reason = reasons.iloc[-1]
            
            # 获取该商品的第一个动销日期（Vida_Sales表中Buyers > 0的最早日期）
            query_first_sales = f"""
            SELECT MIN(date_label) as first_sales_date
            FROM `Vida_Sales`.`{sales_table_name}`
            WHERE goods_id = %s
              AND Buyers IS NOT NULL 
              AND Buyers > 0
            """
            cursor_sales.execute(query_first_sales, (goods_id,))
            result = cursor_sales.fetchone()
            
            join_date = None
            if result and result[0] is not None:
                first_sales_date = result[0]
                # 处理不同的日期类型
                if isinstance(first_sales_date, datetime):
                    join_date = first_sales_date
                elif hasattr(first_sales_date, 'strftime'):
                    # 如果是date对象，转换为datetime
                    join_date = datetime.combine(first_sales_date, datetime.min.time())
                elif isinstance(first_sales_date, str):
                    try:
                        join_date = datetime.strptime(first_sales_date, '%Y-%m-%d')
                    except:
                        join_date = None
            
            goods_info_list.append({
                'goods_id': goods_id,
                'reason': reason if reason else 'None',
                'join_date': join_date.strftime('%Y-%m-%d') if join_date else 'N/A'
            })
        
        return goods_info_list
    finally:
        cursor.close()
        cursor_sales.close()
        conn.close()
        conn_sales.close()


def save_dynamic_management_history(target_date, stats, rising_info, declined_info, table_name):
    """
    保存动销品管理的历史记录到txt文件
    如果有新增的商品（新增上升期、新增非上升期、更新为上升期、由非上升期重回上升期、由上升期到非上升期），
    就覆盖文件；否则如果文件已存在就跳过
    """
    try:
        # 创建History_Dynamic目录（如果不存在）
        history_dir = 'History_Dynamic'
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)
        
        # 生成文件名（包含日期和表名）
        filename = f"{target_date}_{table_name}.txt"
        filepath = os.path.join(history_dir, filename)
        
        # 检查是否有新增的商品
        has_new_changes = (
            stats.get('new_rising', 0) > 0 or
            stats.get('new_declined', 0) > 0 or
            stats.get('updated_to_rising', 0) > 0 or
            stats.get('back_to_rising', 0) > 0 or
            stats.get('declined_from_rising', 0) > 0
        )
        
        # 如果没有新增且文件已存在，则跳过
        if not has_new_changes and os.path.exists(filepath):
            return  # 没有新增且文件已存在，直接返回，不重复记录
        
        # 准备写入内容
        content_lines = []
        content_lines.append("=" * 80)
        content_lines.append(f"动销品管理记录 - {target_date}")
        content_lines.append(f"表名: {table_name}")
        content_lines.append(f"记录时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content_lines.append("=" * 80)
        content_lines.append("")
        
        # 统计信息
        content_lines.append("【统计信息】")
        content_lines.append(f"日期：{stats.get('date', target_date)}")
        content_lines.append(f"前一天上升期：{stats.get('previous_rising_count', 0)}个")
        content_lines.append(f"计算上升期：{stats.get('calculated_rising_count', 0)}个（前一天上升期 + 新增上升期 + 更新为上升期 + 由非上升期重回上升期 - 由上升期到非上升期）")
        content_lines.append(f"实际上升期：{stats.get('rising_count', 0)}个（选定日期Status=1的数量）")
        content_lines.append(f"差值：{stats.get('calculated_rising_count', 0) - stats.get('rising_count', 0)}个")
        content_lines.append(f"非上升期：{stats.get('declined_count', 0)}个")
        content_lines.append(f"新增上升期：{stats.get('new_rising', 0)}个")
        content_lines.append(f"新增非上升期：{stats.get('new_declined', 0)}个")
        content_lines.append(f"更新为上升期：{stats.get('updated_to_rising', 0)}个")
        content_lines.append(f"由非上升期重回上升期：{stats.get('back_to_rising', 0)}个")
        content_lines.append(f"！！！由上升期到非上升期：{stats.get('declined_from_rising', 0)}个")
        content_lines.append("")
        
        # 输出各分类的goods_id列表
        new_rising_goods = stats.get('new_rising_goods', [])
        if len(new_rising_goods) > 0:
            content_lines.append("【新增上升期商品ID】")
            content_lines.append(f"商品数量: {len(new_rising_goods)}个")
            content_lines.append(f"goods_id: {', '.join(map(str, new_rising_goods))}")
            content_lines.append("")
        
        new_declined_goods = stats.get('new_declined_goods', [])
        if len(new_declined_goods) > 0:
            content_lines.append("【新增非上升期商品ID】")
            content_lines.append(f"商品数量: {len(new_declined_goods)}个")
            content_lines.append(f"goods_id: {', '.join(map(str, new_declined_goods))}")
            content_lines.append("")
        
        updated_to_rising_goods = stats.get('updated_to_rising_goods', [])
        if len(updated_to_rising_goods) > 0:
            content_lines.append("【更新为上升期商品ID】")
            content_lines.append(f"商品数量: {len(updated_to_rising_goods)}个")
            content_lines.append(f"goods_id: {', '.join(map(str, updated_to_rising_goods))}")
            content_lines.append("")
        
        back_to_rising_goods = stats.get('back_to_rising_goods', [])
        if len(back_to_rising_goods) > 0:
            content_lines.append("【由非上升期重回上升期商品ID】")
            content_lines.append(f"商品数量: {len(back_to_rising_goods)}个")
            content_lines.append(f"goods_id: {', '.join(map(str, back_to_rising_goods))}")
            content_lines.append("")
        
        declined_from_rising_goods = stats.get('declined_from_rising_goods', [])
        if len(declined_from_rising_goods) > 0:
            content_lines.append("【！！！由上升期到非上升期商品ID】")
            content_lines.append(f"商品数量: {len(declined_from_rising_goods)}个")
            content_lines.append(f"goods_id: {', '.join(map(str, declined_from_rising_goods))}")
            content_lines.append("")
        
        # 上升期商品信息
        if rising_info and len(rising_info) > 0:
            content_lines.append("【上升期商品】")
            content_lines.append(f"商品数量: {len(rising_info)}个")
            content_lines.append("")
            for info in rising_info:
                content_lines.append(f"{info['goods_id']} - 加入时间: {info['join_date']}, Reason: {info['reason']}")
            content_lines.append("")
        
        # 非上升期商品信息
        if declined_info and len(declined_info) > 0:
            content_lines.append("【非上升期商品】")
            content_lines.append(f"商品数量: {len(declined_info)}个")
            content_lines.append("")
            for info in declined_info:
                content_lines.append(f"{info['goods_id']} - 加入时间: {info['join_date']}, Reason: {info['reason']}")
            content_lines.append("")
        
        # 输出差值goods_id
        diff_in_calculated_not_actual = stats.get('diff_in_calculated_not_actual', [])
        diff_in_actual_not_calculated = stats.get('diff_in_actual_not_calculated', [])
        
        if len(diff_in_calculated_not_actual) > 0:
            content_lines.append("【计算上升期中有但实际上升期中没有的商品ID】")
            content_lines.append(f"商品数量: {len(diff_in_calculated_not_actual)}个")
            content_lines.append(f"goods_id: {', '.join(map(str, diff_in_calculated_not_actual))}")
            content_lines.append("")
        
        if len(diff_in_actual_not_calculated) > 0:
            content_lines.append("【实际上升期中有但计算上升期中没有的商品ID】")
            content_lines.append(f"商品数量: {len(diff_in_actual_not_calculated)}个")
            content_lines.append(f"goods_id: {', '.join(map(str, diff_in_actual_not_calculated))}")
            content_lines.append("")
        
        content_lines.append("=" * 80)
        content_lines.append("")
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_lines))
        
    except Exception as e:
        # 记录保存失败，但不影响主功能
        print(f"保存历史记录失败: {e}")


def check_target_date_has_status_data(table_name, target_date):
    """
    检查目标日期是否有Status数据
    返回: (has_data, count)
    """
    from config import get_db_config
    import pymysql
    
    traffic_config, _, _, _ = get_db_config()
    conn = pymysql.connect(**traffic_config)
    
    try:
        cursor = conn.cursor()
        query = f"""
        SELECT COUNT(*) 
        FROM `{table_name}` 
        WHERE date_label = %s AND Status IN (1, 2)
        """
        cursor.execute(query, (target_date,))
        result = cursor.fetchone()
        count = result[0] if result else 0
        return count > 0, count
    finally:
        cursor.close()
        conn.close()


def get_active_sales_goods_ids(table_name, sales_table_name, filter_mode=False):
    """
    获取所有历史动销品的goods_id列表
    动销品定义：单个goods_id中所有不同的date_label对应的行有Buyers不为空值或者0的值
    filter_mode: 过滤模式，如果为True，只返回Buyers > 1的商品
    返回: list of goods_id
    """
    from config import get_db_config
    import pymysql
    
    traffic_config, sales_config, pallet_config, product_config = get_db_config()
    conn = pymysql.connect(**traffic_config)
    conn_sales = pymysql.connect(**sales_config)
    
    try:
        cursor = conn.cursor()
        cursor_sales = conn_sales.cursor()
        
        # 根据过滤模式决定Buyers的筛选条件
        buyers_condition = "> 1" if filter_mode else "> 0"
        
        # 获取所有有动销记录的goods_id（Buyers不为空且不为0）
        query = f"""
        SELECT DISTINCT s.goods_id
        FROM `Vida_Sales`.`{sales_table_name}` s
        WHERE s.Buyers IS NOT NULL 
          AND s.Buyers {buyers_condition}
        """
        cursor_sales.execute(query)
        goods_ids = [row[0] for row in cursor_sales.fetchall()]
        
        return goods_ids
    finally:
        cursor.close()
        cursor_sales.close()
        conn.close()
        conn_sales.close()


def get_declined_goods_data_with_discontinued(table_name, sales_table_name, target_date, filter_mode=None):
    """
    获取非上升期数据，包括status=2的商品和下架缺货的商品
    对于下架缺货的商品，图片日期截止到其上架日期
    filter_mode: 过滤模式，None=不过滤, 字典格式：{'min': 最小值, 'max': 最大值或None}
    返回: DataFrame
    """
    from db_utils import build_filter_condition
    from config import get_db_config
    import pymysql
    
    traffic_config, sales_config, pallet_config, product_config = get_db_config()
    conn = pymysql.connect(**traffic_config)
    conn_sales = pymysql.connect(**sales_config)
    
    try:
        cursor = conn.cursor()
        cursor_sales = conn_sales.cursor()
        
        # 获取所有动销品goods_id（不使用filter_mode，因为这是获取所有动销品）
        all_sales_goods = get_active_sales_goods_ids(table_name, sales_table_name, filter_mode=False)
        
        if len(all_sales_goods) == 0:
            return pd.DataFrame()
        
        # 获取status=2的商品（确保在选定日期或之前已经开始动销）
        filter_condition, filter_params = build_filter_condition(filter_mode, sales_table_name, target_date)
        query_status_2 = f"""
        SELECT DISTINCT t2.goods_id
        FROM `Vida_Traffic`.`{table_name}` t2
        WHERE t2.date_label = %s
          AND t2.Status = 2
          AND EXISTS (
              SELECT 1
              FROM `Vida_Sales`.`{sales_table_name}` s2
              WHERE s2.goods_id = t2.goods_id
          )
          AND {filter_condition}
        """
        cursor.execute(query_status_2, [target_date] + filter_params)
        status_2_goods = [row[0] for row in cursor.fetchall()]
        
        # 获取下架缺货的商品（在target_date没有数据，但之前有动销记录）
        placeholders = ','.join(['%s'] * len(all_sales_goods))
        
        # 构建下架缺货商品的过滤条件（使用 < target_date）
        if filter_mode is None:
            discontinued_filter = f"EXISTS (SELECT 1 FROM `Vida_Sales`.`{sales_table_name}` s5 WHERE s5.goods_id = s.goods_id AND s5.date_label < %s AND s5.Buyers IS NOT NULL AND s5.Buyers > 0)"
            discontinued_params = [target_date]
        else:
            min_val = filter_mode.get('min', 0)
            max_val = filter_mode.get('max')
            if max_val is not None:
                discontinued_filter = f"(SELECT COALESCE(SUM(s5.Buyers), 0) FROM `Vida_Sales`.`{sales_table_name}` s5 WHERE s5.goods_id = s.goods_id AND s5.date_label < %s AND s5.Buyers IS NOT NULL) >= %s AND (SELECT COALESCE(SUM(s5.Buyers), 0) FROM `Vida_Sales`.`{sales_table_name}` s5 WHERE s5.goods_id = s.goods_id AND s5.date_label < %s AND s5.Buyers IS NOT NULL) <= %s"
                discontinued_params = [target_date, min_val, target_date, max_val]
            else:
                discontinued_filter = f"(SELECT COALESCE(SUM(s5.Buyers), 0) FROM `Vida_Sales`.`{sales_table_name}` s5 WHERE s5.goods_id = s.goods_id AND s5.date_label < %s AND s5.Buyers IS NOT NULL) >= %s"
                discontinued_params = [target_date, min_val]
        
        query_discontinued = f"""
        SELECT DISTINCT s.goods_id
        FROM `Vida_Sales`.`{sales_table_name}` s
        WHERE s.goods_id IN ({placeholders})
          AND s.goods_id NOT IN (
              SELECT DISTINCT t.goods_id
              FROM `Vida_Traffic`.`{table_name}` t
              WHERE t.date_label = %s
          )
          AND s.goods_id IN (
              SELECT DISTINCT t2.goods_id
              FROM `Vida_Traffic`.`{table_name}` t2
              WHERE t2.date_label < %s
          )
          AND {discontinued_filter}
        """
        cursor.execute(query_discontinued, all_sales_goods + [target_date, target_date] + discontinued_params)
        discontinued_goods = [row[0] for row in cursor.fetchall()]
        
        # 合并所有非上升期商品
        all_declined_goods = list(set(status_2_goods + discontinued_goods))
        
        if len(all_declined_goods) == 0:
            return pd.DataFrame()
        
        # 获取这些商品的所有历史数据
        # 对于下架缺货的商品，只获取到上架日期（最后一个有数据的日期）
        placeholders2 = ','.join(['%s'] * len(all_declined_goods))
        query = f"""
        SELECT 
          t.*,
          s.Buyers
        FROM `Vida_Traffic`.`{table_name}` t
        LEFT JOIN `Vida_Sales`.`{sales_table_name}` s
          ON t.goods_id = s.goods_id
          AND t.date_label = s.date_label
        WHERE t.goods_id IN ({placeholders2})
          AND t.date_label <= %s
        ORDER BY t.goods_id, t.date_label;
        """
        cursor.execute(query, all_declined_goods + [target_date])
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


def refresh_status_data(table_name, sales_table_name):
    """
    刷新status数据：对所有有动销的goods_id，从首次动销日期（含动销当天）开始，
    到昨天为止，所有日期的status都进行计算和更新
    返回: (success, message, updated_count, missing_dates_info)
    """
    from config import get_db_config
    import pymysql
    from db_utils import get_yesterday_date
    
    traffic_config, sales_config, pallet_config, product_config = get_db_config()
    conn = pymysql.connect(**traffic_config)
    conn_sales = pymysql.connect(**sales_config)
    
    try:
        cursor = conn.cursor()
        cursor_sales = conn_sales.cursor()
        
        # 检查并创建必需的列
        create_columns_if_not_exist(cursor, table_name)
        conn.commit()
        
        # 获取所有动销品goods_id
        goods_ids = get_active_sales_goods_ids(table_name, sales_table_name)
        
        if len(goods_ids) == 0:
            return False, "没有找到动销品", 0, []
        
        # 获取昨天日期
        yesterday = get_yesterday_date()
        yesterday_dt = datetime.strptime(yesterday, '%Y-%m-%d')
        
        missing_dates_info = []
        updated_count = 0
        
        # 对每个动销品，找到首次动销日期，然后从该日期到昨天，计算并更新所有日期的status
        placeholders = ','.join(['%s'] * len(goods_ids))
        
        # 获取每个goods_id的首次动销日期
        first_sales_query = f"""
        SELECT 
            s.goods_id,
            MIN(s.date_label) as first_sales_date
        FROM `Vida_Sales`.`{sales_table_name}` s
        WHERE s.goods_id IN ({placeholders})
          AND s.Buyers IS NOT NULL 
          AND s.Buyers > 0
        GROUP BY s.goods_id
        """
        cursor_sales.execute(first_sales_query, goods_ids)
        first_sales_data = cursor_sales.fetchall()
        
        if len(first_sales_data) == 0:
            return False, "没有找到动销日期数据", 0, []
        
        # 构建goods_id到首次动销日期的映射
        # 处理日期类型：可能是字符串或datetime.date对象
        goods_first_sales = {}
        for row in first_sales_data:
            goods_id = row[0]
            first_sales_date = row[1]
            # 处理不同的日期类型
            if first_sales_date is None:
                continue
            # 如果是datetime对象，转换为字符串
            if isinstance(first_sales_date, datetime):
                first_sales_date = first_sales_date.strftime('%Y-%m-%d')
            # 如果是date对象，转换为字符串
            elif hasattr(first_sales_date, 'strftime'):
                try:
                    first_sales_date = first_sales_date.strftime('%Y-%m-%d')
                except:
                    first_sales_date = str(first_sales_date)
            # 如果不是字符串，转换为字符串
            elif not isinstance(first_sales_date, str):
                first_sales_date = str(first_sales_date)
            goods_first_sales[goods_id] = first_sales_date
        
        # 对每个goods_id，清除首次动销日期前的status数据
        for goods_id, first_sales_date in goods_first_sales.items():
            # 清除首次动销日期之前的所有status数据
            clear_status_query = f"""
            UPDATE `{table_name}`
            SET `Status` = NULL
            WHERE `goods_id` = %s AND `date_label` < %s AND `Status` IS NOT NULL
            """
            cursor.execute(clear_status_query, (goods_id, first_sales_date))
            cleared_count = cursor.rowcount
            if cleared_count > 0:
                updated_count += cleared_count  # 记录清除的数量（虽然不算更新，但算作操作）
        
        # 对每个goods_id，从首次动销日期到昨天，计算并更新status
        for goods_id, first_sales_date in goods_first_sales.items():
            # 确保first_sales_date是字符串格式
            if not isinstance(first_sales_date, str):
                if hasattr(first_sales_date, 'strftime'):
                    first_sales_date = first_sales_date.strftime('%Y-%m-%d')
                else:
                    first_sales_date = str(first_sales_date)
            first_sales_dt = datetime.strptime(first_sales_date, '%Y-%m-%d')
            
            # 从首次动销日期到昨天，遍历每一天
            current_date = first_sales_dt
            while current_date <= yesterday_dt:
                date_str = current_date.strftime('%Y-%m-%d')
                
                # 检查该日期是否有Traffic数据（用于计算status）
                check_traffic_query = f"""
                SELECT COUNT(*) 
                FROM `{table_name}`
                WHERE goods_id = %s AND date_label = %s
                """
                cursor.execute(check_traffic_query, (goods_id, date_str))
                has_traffic_data = cursor.fetchone()[0] > 0
                
                if not has_traffic_data:
                    # 如果没有Traffic数据，检查是否有动销数据
                    check_sales_query = f"""
                    SELECT COUNT(*) 
                    FROM `{sales_table_name}`
                    WHERE goods_id = %s AND date_label = %s
                      AND Buyers IS NOT NULL AND Buyers > 0
                    """
                    cursor_sales.execute(check_sales_query, (goods_id, date_str))
                    has_sales_data = cursor_sales.fetchone()[0] > 0
                    
                    if has_sales_data:
                        # 有动销数据但没有Traffic数据，说明数据库缺失数据
                        if date_str not in [info.get('date', '') for info in missing_dates_info]:
                            missing_dates_info.append({
                                'date': date_str,
                                'goods_id': goods_id,
                                'message': f'goods_id {goods_id} 在 {date_str} 有动销数据但缺少Traffic数据，无法计算status'
                            })
                    # 没有Traffic数据，无法计算status，跳过
                    current_date += timedelta(days=1)
                    continue
                
                # 检查该日期是否已经有status数据
                check_status_query = f"""
                SELECT Status
                FROM `{table_name}`
                WHERE goods_id = %s AND date_label = %s AND Status IS NOT NULL
                """
                cursor.execute(check_status_query, (goods_id, date_str))
                result = cursor.fetchone()
                
                # 无论是否已有status，都重新计算并更新（确保status是最新的）
                # 计算该日期的status
                try:
                    success, msg, count = auto_update_status_for_goods(
                        cursor, table_name, sales_table_name, date_str, [goods_id]
                    )
                    if success:
                        updated_count += count
                except Exception as e:
                    # 如果单个商品更新失败，记录错误但继续处理其他商品
                    print(f"更新goods_id {goods_id} 在 {date_str} 的status失败: {str(e)}")
                    # 继续处理下一个日期
                
                current_date += timedelta(days=1)
        
        conn.commit()
        
        # 检查昨天和之前数据库没有数据的日期范围
        # 检查昨天是否有Traffic数据
        check_yesterday_query = f"""
        SELECT COUNT(DISTINCT goods_id)
        FROM `{table_name}`
        WHERE date_label = %s
        """
        cursor.execute(check_yesterday_query, (yesterday,))
        result = cursor.fetchone()
        yesterday_count = result[0] if result else 0
        
        # 向前查找，找到第一个有数据的日期
        missing_date_ranges = []
        if yesterday_count == 0:
            # 昨天没有数据，向前查找
            found_date = None
            for days_back in range(1, 90):  # 最多往前查找90天
                check_date = (yesterday_dt - timedelta(days=days_back)).strftime('%Y-%m-%d')
                cursor.execute(check_yesterday_query, (check_date,))
                result = cursor.fetchone()
                count = result[0] if result else 0
                if count > 0:
                    found_date = check_date
                    break
            
            if found_date:
                missing_date_ranges.append({
                    'start_date': found_date,
                    'end_date': yesterday,
                    'message': f'从{found_date}到{yesterday}数据库没有Traffic数据，需要手动导入数据'
                })
            else:
                missing_date_ranges.append({
                    'start_date': None,
                    'end_date': yesterday,
                    'message': f'数据库最近90天内都没有Traffic数据，需要手动导入数据'
                })
        
        # 整理缺失数据信息（个别商品缺少Traffic数据）
        if len(missing_dates_info) > 0:
            # 按日期分组缺失信息
            missing_by_date = {}
            for info in missing_dates_info:
                date = info['date']
                if date not in missing_by_date:
                    missing_by_date[date] = []
                missing_by_date[date].append(info['goods_id'])
            
            missing_messages = []
            for date, goods_list in missing_by_date.items():
                if len(goods_list) <= 5:
                    missing_messages.append(f'{date}: goods_id {", ".join(map(str, goods_list))} 缺少Traffic数据')
                else:
                    missing_messages.append(f'{date}: {len(goods_list)}个goods_id缺少Traffic数据')
            
            if len(missing_date_ranges) > 0:
                message = f"刷新完成，更新了 {updated_count} 条status数据。\n注意：{missing_date_ranges[0]['message']}\n另外，以下日期个别商品缺少Traffic数据：\n" + "\n".join(missing_messages)
            else:
                message = f"刷新完成，更新了 {updated_count} 条status数据。\n注意：以下日期个别商品缺少Traffic数据，无法计算status：\n" + "\n".join(missing_messages)
            return True, message, updated_count, missing_dates_info + missing_date_ranges
        elif len(missing_date_ranges) > 0:
            message = f"刷新完成，更新了 {updated_count} 条status数据。\n注意：{missing_date_ranges[0]['message']}"
            return True, message, updated_count, missing_date_ranges
        else:
            return True, f"刷新完成，更新了 {updated_count} 条status数据", updated_count, []
            
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False, f"刷新失败: {str(e)}", 0, []
    finally:
        cursor.close()
        cursor_sales.close()
        conn.close()
        conn_sales.close()


def quick_refresh_status_data(table_name, sales_table_name):
    """
    快速刷新status数据：刷新所有动销品在昨天的status数据
    返回: (success, message, updated_count, missing_dates_info)
    """
    from config import get_db_config
    import pymysql
    from db_utils import get_yesterday_date
    
    traffic_config, sales_config, pallet_config, product_config = get_db_config()
    conn = pymysql.connect(**traffic_config)
    conn_sales = pymysql.connect(**sales_config)
    
    try:
        cursor = conn.cursor()
        cursor_sales = conn_sales.cursor()
        
        # 检查并创建必需的列
        create_columns_if_not_exist(cursor, table_name)
        conn.commit()
        
        # 获取昨天日期
        yesterday = get_yesterday_date()
        
        # 获取所有动销品goods_id（所有历史有动销的商品）
        all_sales_goods = get_active_sales_goods_ids(table_name, sales_table_name)
        
        if len(all_sales_goods) == 0:
            return False, "没有找到动销品", 0, []
        
        missing_dates_info = []
        updated_count = 0
        
        # 对每个动销品，检查昨天是否有Traffic数据，如果有则更新status
        for goods_id in all_sales_goods:
            # 检查该日期是否有Traffic数据（用于计算status）
            check_traffic_query = f"""
            SELECT COUNT(*) 
            FROM `{table_name}`
            WHERE goods_id = %s AND date_label = %s
            """
            cursor.execute(check_traffic_query, (goods_id, yesterday))
            has_traffic_data = cursor.fetchone()[0] > 0
            
            if not has_traffic_data:
                # 如果没有Traffic数据，跳过（不记录缺失信息，因为可能是正常下架）
                continue
            
            # 计算该日期的status
            try:
                success, msg, count = auto_update_status_for_goods(
                    cursor, table_name, sales_table_name, yesterday, [goods_id]
                )
                if success:
                    updated_count += count
            except Exception as e:
                # 如果单个商品更新失败，记录错误但继续处理其他商品
                print(f"更新goods_id {goods_id} 在 {yesterday} 的status失败: {str(e)}")
        
        conn.commit()
        
        return True, f"成功快速刷新所有动销品在昨天({yesterday})的status数据，共更新 {updated_count} 条记录", updated_count, missing_dates_info
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False, f"快速刷新失败: {str(e)}", 0, []
    finally:
        cursor.close()
        cursor_sales.close()
        conn.close()
        conn_sales.close()


def auto_update_status_for_goods(cursor, table_name, sales_table_name, target_date, goods_ids):
    """
    为指定的goods_id列表计算并更新status
    返回: (success, message, updated_count)
    """
    if len(goods_ids) == 0:
        return False, "没有需要更新的商品", 0
    
    # 获取这些商品的所有历史数据（用于趋势分析）
    placeholders = ','.join(['%s'] * len(goods_ids))
    query_history = f"""
    SELECT 
      t.goods_id,
      t.date_label,
      t.`Product impressions`
    FROM `Vida_Traffic`.`{table_name}` t
    WHERE t.goods_id IN ({placeholders})
      AND t.date_label <= %s
    ORDER BY t.goods_id, t.date_label
    """
    cursor.execute(query_history, goods_ids + [target_date])
    history_data = cursor.fetchall()
    
    if len(history_data) == 0:
        return False, f"目标日期 {target_date} 没有历史曝光数据", 0
    
    # 构建DataFrame
    df_history = pd.DataFrame(history_data, columns=['goods_id', 'date_label', 'Product impressions'])
    df_history['Product impressions'] = pd.to_numeric(df_history['Product impressions'], errors='coerce').fillna(0)
    
    # 对每个商品分析趋势并更新Status
    updated_count = 0
    for goods_id in goods_ids:
        # 获取该商品的历史曝光数据
        goods_data = df_history[df_history['goods_id'] == goods_id].sort_values('date_label')
        
        if len(goods_data) == 0:
            continue
        
        impressions = goods_data['Product impressions'].values
        
        # 分析趋势
        trend = analyze_trend(impressions)
        status = 1 if trend == 'rising' else 2
        
        # 检查该商品在目标日期是否有记录
        check_query = f"""
        SELECT COUNT(*) 
        FROM `{table_name}`
        WHERE goods_id = %s AND date_label = %s
        """
        cursor.execute(check_query, (goods_id, target_date))
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            update_sql = f"""
            UPDATE `{table_name}`
            SET `Status` = %s
            WHERE `goods_id` = %s AND `date_label` = %s
            """
            cursor.execute(update_sql, (status, goods_id, target_date))
            updated_count += cursor.rowcount
    
    return True, f"成功更新 {updated_count} 条记录的Status", updated_count


def auto_update_status_for_date(table_name, sales_table_name, target_date):
    """
    自动更新目标日期的Status数据
    返回: (success, message, updated_count)
    """
    from config import get_db_config
    import pymysql
    
    traffic_config, sales_config, pallet_config, product_config = get_db_config()
    conn = pymysql.connect(**traffic_config)
    conn_sales = pymysql.connect(**sales_config)
    
    try:
        cursor = conn.cursor()
        cursor_sales = conn_sales.cursor()
        
        # 获取目标日期有动销的商品
        query_goods = f"""
        SELECT DISTINCT t.goods_id
        FROM `Vida_Traffic`.`{table_name}` t
        WHERE t.date_label = %s
          AND EXISTS (
              SELECT 1
              FROM `Vida_Sales`.`{sales_table_name}` s
              WHERE s.goods_id = t.goods_id AND s.date_label = %s
                AND s.Buyers IS NOT NULL AND s.Buyers > 0
          )
        """
        cursor.execute(query_goods, (target_date, target_date))
        goods_ids = [row[0] for row in cursor.fetchall()]
        
        if len(goods_ids) == 0:
            return False, f"目标日期 {target_date} 没有动销商品", 0
        
        # 使用auto_update_status_for_goods来更新
        success, message, updated_count = auto_update_status_for_goods(
            cursor, table_name, sales_table_name, target_date, goods_ids
        )
        
        if success:
            conn.commit()
        else:
            conn.rollback()
        
        return success, message, updated_count
        
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        return False, f"更新Status失败: {str(e)}", 0
    finally:
        cursor.close()
        cursor_sales.close()
        conn.close()
        conn_sales.close()


def get_cache_file_path(table_name, target_date):
    """
    获取缓存文件路径
    返回: 缓存文件路径
    """
    cache_dir = 'Cache_Dynamic'
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    # 文件名格式：表名_日期.json，例如：ROA1_FR_2025-12-16.json
    # 去掉表名中的ROA1_前缀（如果存在）
    table_suffix = table_name.replace('ROA1_', '')
    filename = f"{table_suffix}_{target_date}.json"
    return os.path.join(cache_dir, filename)


def load_dynamic_management_cache(table_name, target_date):
    """
    加载动销品管理缓存
    返回: 缓存数据字典，如果不存在则返回None
    """
    try:
        cache_file = get_cache_file_path(table_name, target_date)
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                return cache_data
        return None
    except Exception as e:
        print(f"加载缓存失败: {e}")
        return None


def save_dynamic_management_cache(table_name, target_date, statistics, rising_info, declined_info, rising_summary, declined_summary, analysis_time, total_summary=None):
    """
    保存动销品管理缓存
    参数:
        table_name: 表名
        target_date: 目标日期
        statistics: 统计信息
        rising_info: 上升期商品信息
        declined_info: 非上升期商品信息
        rising_summary: 上升期统计摘要
        declined_summary: 非上升期统计摘要
        analysis_time: 分析耗时
        total_summary: 汇总统计摘要
    """
    try:
        cache_file = get_cache_file_path(table_name, target_date)
        
        # 构建缓存数据，格式与参考文件一致
        cache_data = {
            'statistics': {
                'date': statistics.get('date', target_date),
                'rising_count': statistics.get('rising_count', 0),
                'declined_count': statistics.get('declined_count', 0),
                'new_rising': statistics.get('new_rising', 0),
                'new_declined': statistics.get('new_declined', 0),
                'updated_to_rising': statistics.get('updated_to_rising', 0),
                'back_to_rising': statistics.get('back_to_rising', 0),
                'declined_from_rising': statistics.get('declined_from_rising', 0),
                'special_notes': statistics.get('special_notes', []),
                'elapsed_time': analysis_time
            },
            'rising': {
                'goods_info': rising_info if rising_info else [],
                'summary': rising_summary if rising_summary else {}
            },
            'declined': {
                'goods_info': declined_info if declined_info else [],
                'summary': declined_summary if declined_summary else {}
            },
            'total_summary': total_summary if total_summary else {}
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        print(f"缓存已保存到: {cache_file}")
    except Exception as e:
        print(f"保存缓存失败: {e}")


def dynamic_management(target_date=None, use_cache=True, half_image_mode=None, filter_mode=None):
    """
    动销品管理功能
    参数:
        target_date: 目标日期
        use_cache: 是否使用缓存，默认True
        half_image_mode: 半图片模式，默认None（空列表）。
            如果为None或空列表，不生成任何图片
            如果为列表，只生成列表中指定类别的图片。可选类别：
                - 'rising': 上升期（所有上升期商品）
                - 'declined': 非上升期（所有非上升期商品）
                - 'new_rising': 新增上升期
                - 'new_declined': 新增非上升期
                - 'updated_to_rising': 更新为上升期
                - 'back_to_rising': 由非上升期重回上升期
                - 'declined_from_rising': 由上升期到非上升期
            注意：所有模块都会返回数据，只有勾选的模块才会生成图片
        filter_mode: 过滤模式，None=不过滤, 2=总和>1, 3=总和>2
    返回: {
        'success': bool,
        'data': dict or None,
        'error': str or None,
        'need_refresh': bool,  # 是否需要刷新数据
        'analysis_time': float,  # 分析耗时（秒）
        'from_cache': bool  # 是否来自缓存
    }
    """
    import time
    start_time = time.time()
    
    try:
        if target_date is None:
            target_date = get_yesterday_date()
        
        table_name = get_current_table()
        sales_table_name = f"{table_name}_Sales"
        
        # 如果使用缓存，先检查缓存
        if use_cache:
            cache_data = load_dynamic_management_cache(table_name, target_date)
            if cache_data:
                # 从缓存加载数据
                end_time = time.time()
                cache_analysis_time = end_time - start_time
                
                # 获取汇总统计信息（如果缓存中没有，则从上升期和非上升期计算）
                total_summary = cache_data.get('total_summary', {})
                if not total_summary:
                    # 从上升期和非上升期统计信息计算汇总
                    rising_summary = cache_data.get('rising', {}).get('summary', {})
                    declined_summary = cache_data.get('declined', {}).get('summary', {})
                    if rising_summary and declined_summary:
                        # 计算汇总统计
                        total_records = rising_summary.get('total_records', 0) + declined_summary.get('total_records', 0)
                        # 合并商品ID（需要从goods_info中获取）
                        rising_goods_ids = set([info.get('goods_id') for info in cache_data.get('rising', {}).get('goods_info', [])])
                        declined_goods_ids = set([info.get('goods_id') for info in cache_data.get('declined', {}).get('goods_info', [])])
                        unique_goods = len(rising_goods_ids | declined_goods_ids)
                        # 计算日期范围
                        min_dates = []
                        max_dates = []
                        if rising_summary.get('min_date'):
                            min_dates.append(rising_summary['min_date'])
                        if rising_summary.get('max_date'):
                            max_dates.append(rising_summary['max_date'])
                        if declined_summary.get('min_date'):
                            min_dates.append(declined_summary['min_date'])
                        if declined_summary.get('max_date'):
                            max_dates.append(declined_summary['max_date'])
                        if min_dates and max_dates:
                            min_date = min(min_dates)
                            max_date = max(max_dates)
                            min_date_dt = datetime.strptime(min_date, '%Y-%m-%d')
                            max_date_dt = datetime.strptime(max_date, '%Y-%m-%d')
                            date_range = (max_date_dt - min_date_dt).days + 1
                            
                            # 统计Reason类别数量（从缓存中的goods_info中统计）
                            all_goods_info = []
                            if cache_data.get('rising', {}).get('goods_info'):
                                all_goods_info.extend(cache_data.get('rising', {}).get('goods_info', []))
                            if cache_data.get('declined', {}).get('goods_info'):
                                all_goods_info.extend(cache_data.get('declined', {}).get('goods_info', []))
                            
                            reason_counts = count_reason_categories(all_goods_info)
                            
                            # 生成Reason类别饼图
                            reason_pie_chart = None
                            if any(reason_counts.values()):  # 如果有任何类别的数量大于0
                                from plot_utils import plot_reason_category_pie
                                reason_pie_chart = plot_reason_category_pie(reason_counts)
                            
                            # 计算在售占比：(None + Normal) / 总去重商品ID数量
                            on_sale_ratio = 0.0
                            if unique_goods > 0:
                                on_sale_count = reason_counts['None'] + reason_counts['Normal']
                                on_sale_ratio = (on_sale_count / unique_goods) * 100
                            
                            total_summary = {
                                'total_records': total_records,
                                'unique_goods': unique_goods,
                                'min_date': min_date,
                                'max_date': max_date,
                                'date_range': date_range,
                                'out_of_stock_count': reason_counts['Out_of_stock'],
                                'secondary_traffic_restricted_count': reason_counts['Secondary_traffic_restricted'],
                                'blocked_count': reason_counts['Blocked'],
                                'normal_count': reason_counts['Normal'],
                                'none_count': reason_counts['None'],
                                'on_sale_ratio': on_sale_ratio,  # 在售占比（百分数）
                                'reason_pie_chart': reason_pie_chart  # 添加饼图
                            }
                
                # 构建返回数据（不包含图片）
                result_data = {
                    'statistics': cache_data.get('statistics', {}),
                    'rising': {
                        'images': [],  # 缓存不包含图片
                        'goods_info': cache_data.get('rising', {}).get('goods_info', []),
                        'summary': cache_data.get('rising', {}).get('summary', {})
                    },
                    'declined': {
                        'images': [],  # 缓存不包含图片
                        'goods_info': cache_data.get('declined', {}).get('goods_info', []),
                        'summary': cache_data.get('declined', {}).get('summary', {})
                    },
                    'total_summary': total_summary
                }
                
                # 初始化各类别的图片和商品信息
                category_images = {
                    'rising': [],
                    'declined': [],
                    'new_rising': [],
                    'new_declined': [],
                    'updated_to_rising': [],
                    'back_to_rising': [],
                    'declined_from_rising': []
                }
                category_goods_info = {
                    'rising': [],
                    'declined': [],
                    'new_rising': [],
                    'new_declined': [],
                    'updated_to_rising': [],
                    'back_to_rising': [],
                    'declined_from_rising': []
                }
                
                # 处理半图片模式：根据选择的类别生成图片
                if half_image_mode is None:
                    half_image_mode = []
                
                if isinstance(half_image_mode, list) and len(half_image_mode) > 0:
                    stats = cache_data.get('statistics', {})
                    
                    # 获取各类别的goods_id
                    new_rising_goods = stats.get('new_rising_goods', [])
                    new_declined_goods = stats.get('new_declined_goods', [])
                    updated_to_rising_goods = stats.get('updated_to_rising_goods', [])
                    back_to_rising_goods = stats.get('back_to_rising_goods', [])
                    declined_from_rising_goods = stats.get('declined_from_rising_goods', [])
                    
                    # 获取所有上升期和非上升期的goods_id
                    df_rising = get_dynamic_goods_data(table_name, sales_table_name, 1, target_date, filter_mode=filter_mode)
                    df_declined = get_declined_goods_data_with_discontinued(table_name, sales_table_name, target_date, filter_mode=filter_mode)
                    
                    rising_goods_ids = set()
                    declined_goods_ids = set()
                    if len(df_rising) > 0:
                        rising_goods_ids = set(df_rising['goods_id'].unique())
                    if len(df_declined) > 0:
                        declined_goods_ids = set(df_declined['goods_id'].unique())
                    
                    # 为每个勾选的类别生成图片
                    if 'rising' in half_image_mode and len(rising_goods_ids) > 0:
                        df_rising_selected = get_goods_data_by_ids(table_name, sales_table_name, list(rising_goods_ids), target_date, filter_mode=filter_mode)
                        if len(df_rising_selected) > 0:
                            category_images['rising'] = plot_goods_batch(df_rising_selected, cols=3)
                            category_goods_info['rising'] = get_goods_info_with_status(df_rising_selected, table_name, sales_table_name)
                    
                    if 'declined' in half_image_mode and len(declined_goods_ids) > 0:
                        df_declined_selected = get_goods_data_by_ids(table_name, sales_table_name, list(declined_goods_ids), target_date, filter_mode=filter_mode)
                        if len(df_declined_selected) > 0:
                            category_images['declined'] = plot_goods_batch(df_declined_selected, cols=3)
                            category_goods_info['declined'] = get_goods_info_with_status(df_declined_selected, table_name, sales_table_name)
                    
                    if 'new_rising' in half_image_mode and len(new_rising_goods) > 0:
                        df_new_rising = get_goods_data_by_ids(table_name, sales_table_name, new_rising_goods, target_date, filter_mode=filter_mode)
                        if len(df_new_rising) > 0:
                            category_images['new_rising'] = plot_goods_batch(df_new_rising, cols=3)
                            category_goods_info['new_rising'] = get_goods_info_with_status(df_new_rising, table_name, sales_table_name)
                    
                    if 'new_declined' in half_image_mode and len(new_declined_goods) > 0:
                        df_new_declined = get_goods_data_by_ids(table_name, sales_table_name, new_declined_goods, target_date, filter_mode=filter_mode)
                        if len(df_new_declined) > 0:
                            category_images['new_declined'] = plot_goods_batch(df_new_declined, cols=3)
                            category_goods_info['new_declined'] = get_goods_info_with_status(df_new_declined, table_name, sales_table_name)
                    
                    if 'updated_to_rising' in half_image_mode and len(updated_to_rising_goods) > 0:
                        df_updated_to_rising = get_goods_data_by_ids(table_name, sales_table_name, updated_to_rising_goods, target_date, filter_mode=filter_mode)
                        if len(df_updated_to_rising) > 0:
                            category_images['updated_to_rising'] = plot_goods_batch(df_updated_to_rising, cols=3)
                            category_goods_info['updated_to_rising'] = get_goods_info_with_status(df_updated_to_rising, table_name, sales_table_name)
                    
                    if 'back_to_rising' in half_image_mode and len(back_to_rising_goods) > 0:
                        df_back_to_rising = get_goods_data_by_ids(table_name, sales_table_name, back_to_rising_goods, target_date, filter_mode=filter_mode)
                        if len(df_back_to_rising) > 0:
                            category_images['back_to_rising'] = plot_goods_batch(df_back_to_rising, cols=3)
                            category_goods_info['back_to_rising'] = get_goods_info_with_status(df_back_to_rising, table_name, sales_table_name)
                    
                    if 'declined_from_rising' in half_image_mode and len(declined_from_rising_goods) > 0:
                        df_declined_from_rising = get_goods_data_by_ids(table_name, sales_table_name, declined_from_rising_goods, target_date, filter_mode=filter_mode)
                        if len(df_declined_from_rising) > 0:
                            category_images['declined_from_rising'] = plot_goods_batch(df_declined_from_rising, cols=3)
                            category_goods_info['declined_from_rising'] = get_goods_info_with_status(df_declined_from_rising, table_name, sales_table_name)
                
                # 获取各类别的商品信息（即使没有勾选也要返回数据）
                stats = cache_data.get('statistics', {})
                new_rising_goods = stats.get('new_rising_goods', [])
                new_declined_goods = stats.get('new_declined_goods', [])
                updated_to_rising_goods = stats.get('updated_to_rising_goods', [])
                back_to_rising_goods = stats.get('back_to_rising_goods', [])
                declined_from_rising_goods = stats.get('declined_from_rising_goods', [])
                
                if len(new_rising_goods) > 0:
                    if 'new_rising' not in category_goods_info or len(category_goods_info['new_rising']) == 0:
                        df_new_rising = get_goods_data_by_ids(table_name, sales_table_name, new_rising_goods, target_date, filter_mode=filter_mode)
                        if len(df_new_rising) > 0:
                            category_goods_info['new_rising'] = get_goods_info_with_status(df_new_rising, table_name, sales_table_name)
                
                if len(new_declined_goods) > 0:
                    if 'new_declined' not in category_goods_info or len(category_goods_info['new_declined']) == 0:
                        df_new_declined = get_goods_data_by_ids(table_name, sales_table_name, new_declined_goods, target_date, filter_mode=filter_mode)
                        if len(df_new_declined) > 0:
                            category_goods_info['new_declined'] = get_goods_info_with_status(df_new_declined, table_name, sales_table_name)
                
                if len(updated_to_rising_goods) > 0:
                    if 'updated_to_rising' not in category_goods_info or len(category_goods_info['updated_to_rising']) == 0:
                        df_updated_to_rising = get_goods_data_by_ids(table_name, sales_table_name, updated_to_rising_goods, target_date, filter_mode=filter_mode)
                        if len(df_updated_to_rising) > 0:
                            category_goods_info['updated_to_rising'] = get_goods_info_with_status(df_updated_to_rising, table_name, sales_table_name)
                
                if len(back_to_rising_goods) > 0:
                    if 'back_to_rising' not in category_goods_info or len(category_goods_info['back_to_rising']) == 0:
                        df_back_to_rising = get_goods_data_by_ids(table_name, sales_table_name, back_to_rising_goods, target_date, filter_mode=filter_mode)
                        if len(df_back_to_rising) > 0:
                            category_goods_info['back_to_rising'] = get_goods_info_with_status(df_back_to_rising, table_name, sales_table_name)
                
                if len(declined_from_rising_goods) > 0:
                    if 'declined_from_rising' not in category_goods_info or len(category_goods_info['declined_from_rising']) == 0:
                        df_declined_from_rising = get_goods_data_by_ids(table_name, sales_table_name, declined_from_rising_goods, target_date, filter_mode=filter_mode)
                        if len(df_declined_from_rising) > 0:
                            category_goods_info['declined_from_rising'] = get_goods_info_with_status(df_declined_from_rising, table_name, sales_table_name)
                
                # 更新返回数据，包含各类别的数据
                result_data['rising']['images'] = category_images.get('rising', [])
                result_data['declined']['images'] = category_images.get('declined', [])
                result_data['categories'] = {
                    'new_rising': {
                        'images': category_images.get('new_rising', []),
                        'goods_info': category_goods_info.get('new_rising', [])
                    },
                    'new_declined': {
                        'images': category_images.get('new_declined', []),
                        'goods_info': category_goods_info.get('new_declined', [])
                    },
                    'updated_to_rising': {
                        'images': category_images.get('updated_to_rising', []),
                        'goods_info': category_goods_info.get('updated_to_rising', [])
                    },
                    'back_to_rising': {
                        'images': category_images.get('back_to_rising', []),
                        'goods_info': category_goods_info.get('back_to_rising', [])
                    },
                    'declined_from_rising': {
                        'images': category_images.get('declined_from_rising', []),
                        'goods_info': category_goods_info.get('declined_from_rising', [])
                    }
                }
                
                # 过滤模式：如果启用过滤模式，需要从缓存数据中过滤掉Buyers = 1的商品信息
                if filter_mode:
                    # 需要重新获取数据来应用过滤（因为缓存中没有Buyers信息）
                    # 获取上升期数据（传递filter_mode参数，在SQL层面过滤）
                    df_rising = get_dynamic_goods_data(table_name, sales_table_name, 1, target_date, filter_mode=filter_mode)
                    if len(df_rising) > 0:
                        # 获取过滤后的goods_id列表
                        filtered_rising_goods = set(df_rising['goods_id'].unique())
                        # 过滤掉不在过滤后列表中的商品信息
                        result_data['rising']['goods_info'] = [
                            info for info in result_data['rising']['goods_info']
                            if info['goods_id'] in filtered_rising_goods
                        ]
                    
                    # 获取非上升期数据（传递filter_mode参数，在SQL层面过滤）
                    df_declined = get_declined_goods_data_with_discontinued(table_name, sales_table_name, target_date, filter_mode=filter_mode)
                    if len(df_declined) > 0:
                        # 获取过滤后的goods_id列表
                        filtered_declined_goods = set(df_declined['goods_id'].unique())
                        # 过滤掉不在过滤后列表中的商品信息
                        result_data['declined']['goods_info'] = [
                            info for info in result_data['declined']['goods_info']
                            if info['goods_id'] in filtered_declined_goods
                        ]
                
                return {
                    'success': True,
                    'data': result_data,
                    'error': None,
                    'analysis_time': round(cache_analysis_time, 2),
                    'from_cache': True
                }
        
        # 检查目标日期是否有任何goods_id的数据
        from config import get_db_config
        import pymysql
        
        traffic_config, sales_config, pallet_config, product_config = get_db_config()
        conn = pymysql.connect(**traffic_config)
        conn_sales = pymysql.connect(**sales_config)
        
        try:
            cursor = conn.cursor()
            cursor_sales = conn_sales.cursor()
            
            # 检查目标日期是否有任何goods_id的数据
            check_date_query = f"""
            SELECT COUNT(DISTINCT goods_id)
            FROM `{table_name}`
            WHERE date_label = %s
            """
            cursor.execute(check_date_query, (target_date,))
            result = cursor.fetchone()
            target_date_goods_count = result[0] if result else 0
            
            # 检查前一天是否有任何goods_id的数据
            target_dt = datetime.strptime(target_date, '%Y-%m-%d')
            previous_day = (target_dt - timedelta(days=1)).strftime('%Y-%m-%d')
            cursor.execute(check_date_query, (previous_day,))
            result = cursor.fetchone()
            previous_day_goods_count = result[0] if result else 0
            
            # 如果目标日期和前一天都没有数据，报告需要刷新
            if target_date_goods_count == 0 and previous_day_goods_count == 0:
                end_time = time.time()
                analysis_time = end_time - start_time
                return {
                    'success': False,
                    'data': None,
                    'error': f'选定日期 {target_date} 和前一天 {previous_day} 都没有数据，请点击刷新按钮刷新数据。',
                    'need_refresh': True,
                    'analysis_time': round(analysis_time, 2)
                }
            
            # 如果目标日期没有数据，但前一天有数据，也报告需要刷新
            if target_date_goods_count == 0:
                end_time = time.time()
                analysis_time = end_time - start_time
                return {
                    'success': False,
                    'data': None,
                    'error': f'选定日期 {target_date} 没有数据，请点击刷新按钮刷新数据。',
                    'need_refresh': True,
                    'analysis_time': round(analysis_time, 2)
                }
        finally:
            cursor.close()
            cursor_sales.close()
            conn.close()
            conn_sales.close()
        
        # 检查目标日期是否有Status数据
        has_status_data, status_count = check_target_date_has_status_data(table_name, target_date)
        
        # 如果没有Status数据，尝试自动更新
        if not has_status_data:
            update_success, update_message, updated_count = auto_update_status_for_date(
                table_name, sales_table_name, target_date
            )
            
            if not update_success:
                end_time = time.time()
                analysis_time = end_time - start_time
                return {
                    'success': False,
                    'data': None,
                    'error': f'未找到日期 {target_date} 的Status数据。尝试自动更新失败: {update_message}。请点击刷新按钮刷新数据。',
                    'need_refresh': True,
                    'analysis_time': round(analysis_time, 2)
                }
            
            # 更新后再次检查
            has_status_data, status_count = check_target_date_has_status_data(table_name, target_date)
            if not has_status_data:
                end_time = time.time()
                analysis_time = end_time - start_time
                return {
                    'success': False,
                    'data': None,
                    'error': f'未找到日期 {target_date} 的Status数据。已尝试自动更新Status，但仍无数据。请点击刷新按钮刷新数据。',
                    'need_refresh': True,
                    'analysis_time': round(analysis_time, 2)
                }
        
        # 获取统计信息
        stats = get_status_statistics(table_name, sales_table_name, target_date)
        
        # 获取所有数据（上升期和非上升期）
        df_rising = get_dynamic_goods_data(table_name, sales_table_name, 1, target_date, filter_mode=filter_mode)
        df_declined = get_declined_goods_data_with_discontinued(table_name, sales_table_name, target_date, filter_mode=filter_mode)
        
        # 获取所有商品信息（所有模块都返回数据）
        rising_info = []
        declined_info = []
        if len(df_rising) > 0:
            rising_info = get_goods_info_with_status(df_rising, table_name, sales_table_name)
        if len(df_declined) > 0:
            declined_info = get_goods_info_with_status(df_declined, table_name, sales_table_name)
        
        # 初始化各类别的图片和商品信息
        category_images = {
            'rising': [],
            'declined': [],
            'new_rising': [],
            'new_declined': [],
            'updated_to_rising': [],
            'back_to_rising': [],
            'declined_from_rising': []
        }
        category_goods_info = {
            'rising': [],
            'declined': [],
            'new_rising': [],
            'new_declined': [],
            'updated_to_rising': [],
            'back_to_rising': [],
            'declined_from_rising': []
        }
        
        # 获取各类别的goods_id（从统计信息中获取）
        new_rising_goods = stats.get('new_rising_goods', [])
        new_declined_goods = stats.get('new_declined_goods', [])
        updated_to_rising_goods = stats.get('updated_to_rising_goods', [])
        back_to_rising_goods = stats.get('back_to_rising_goods', [])
        declined_from_rising_goods = stats.get('declined_from_rising_goods', [])
        
        # 获取所有上升期和非上升期的goods_id
        rising_goods_ids = set()
        declined_goods_ids = set()
        if len(df_rising) > 0:
            rising_goods_ids = set(df_rising['goods_id'].unique())
        if len(df_declined) > 0:
            declined_goods_ids = set(df_declined['goods_id'].unique())
        
        # 处理半图片模式：根据选择的类别生成图片
        if half_image_mode is None:
            half_image_mode = []
        
        if isinstance(half_image_mode, list):
            
            # 为每个勾选的类别生成图片
            if 'rising' in half_image_mode and len(rising_goods_ids) > 0:
                df_rising_selected = get_goods_data_by_ids(table_name, sales_table_name, list(rising_goods_ids), target_date, filter_mode=filter_mode)
                if len(df_rising_selected) > 0:
                    category_images['rising'] = plot_goods_batch(df_rising_selected, cols=3)
                    category_goods_info['rising'] = get_goods_info_with_status(df_rising_selected, table_name, sales_table_name)
            
            if 'declined' in half_image_mode and len(declined_goods_ids) > 0:
                df_declined_selected = get_goods_data_by_ids(table_name, sales_table_name, list(declined_goods_ids), target_date, filter_mode=filter_mode)
                if len(df_declined_selected) > 0:
                    category_images['declined'] = plot_goods_batch(df_declined_selected, cols=3)
                    category_goods_info['declined'] = get_goods_info_with_status(df_declined_selected, table_name, sales_table_name)
            
            if 'new_rising' in half_image_mode and len(new_rising_goods) > 0:
                df_new_rising = get_goods_data_by_ids(table_name, sales_table_name, new_rising_goods, target_date, filter_mode=filter_mode)
                if len(df_new_rising) > 0:
                    category_images['new_rising'] = plot_goods_batch(df_new_rising, cols=3)
                    category_goods_info['new_rising'] = get_goods_info_with_status(df_new_rising, table_name, sales_table_name)
            
            if 'new_declined' in half_image_mode and len(new_declined_goods) > 0:
                df_new_declined = get_goods_data_by_ids(table_name, sales_table_name, new_declined_goods, target_date, filter_mode=filter_mode)
                if len(df_new_declined) > 0:
                    category_images['new_declined'] = plot_goods_batch(df_new_declined, cols=3)
                    category_goods_info['new_declined'] = get_goods_info_with_status(df_new_declined, table_name, sales_table_name)
            
            if 'updated_to_rising' in half_image_mode and len(updated_to_rising_goods) > 0:
                df_updated_to_rising = get_goods_data_by_ids(table_name, sales_table_name, updated_to_rising_goods, target_date, filter_mode=filter_mode)
                if len(df_updated_to_rising) > 0:
                    category_images['updated_to_rising'] = plot_goods_batch(df_updated_to_rising, cols=3)
                    category_goods_info['updated_to_rising'] = get_goods_info_with_status(df_updated_to_rising, table_name, sales_table_name)
            
            if 'back_to_rising' in half_image_mode and len(back_to_rising_goods) > 0:
                df_back_to_rising = get_goods_data_by_ids(table_name, sales_table_name, back_to_rising_goods, target_date, filter_mode=filter_mode)
                if len(df_back_to_rising) > 0:
                    category_images['back_to_rising'] = plot_goods_batch(df_back_to_rising, cols=3)
                    category_goods_info['back_to_rising'] = get_goods_info_with_status(df_back_to_rising, table_name, sales_table_name)
            
            if 'declined_from_rising' in half_image_mode and len(declined_from_rising_goods) > 0:
                df_declined_from_rising = get_goods_data_by_ids(table_name, sales_table_name, declined_from_rising_goods, target_date, filter_mode=filter_mode)
                if len(df_declined_from_rising) > 0:
                    category_images['declined_from_rising'] = plot_goods_batch(df_declined_from_rising, cols=3)
                    category_goods_info['declined_from_rising'] = get_goods_info_with_status(df_declined_from_rising, table_name, sales_table_name)
        
        # 获取各类别的商品信息（即使没有勾选也要返回数据）
        if len(new_rising_goods) > 0:
            if 'new_rising' not in category_goods_info or len(category_goods_info['new_rising']) == 0:
                df_new_rising = get_goods_data_by_ids(table_name, sales_table_name, new_rising_goods, target_date, filter_mode=filter_mode)
                if len(df_new_rising) > 0:
                    category_goods_info['new_rising'] = get_goods_info_with_status(df_new_rising, table_name, sales_table_name)
        
        if len(new_declined_goods) > 0:
            if 'new_declined' not in category_goods_info or len(category_goods_info['new_declined']) == 0:
                df_new_declined = get_goods_data_by_ids(table_name, sales_table_name, new_declined_goods, target_date, filter_mode=filter_mode)
                if len(df_new_declined) > 0:
                    category_goods_info['new_declined'] = get_goods_info_with_status(df_new_declined, table_name, sales_table_name)
        
        if len(updated_to_rising_goods) > 0:
            if 'updated_to_rising' not in category_goods_info or len(category_goods_info['updated_to_rising']) == 0:
                df_updated_to_rising = get_goods_data_by_ids(table_name, sales_table_name, updated_to_rising_goods, target_date, filter_mode=filter_mode)
                if len(df_updated_to_rising) > 0:
                    category_goods_info['updated_to_rising'] = get_goods_info_with_status(df_updated_to_rising, table_name, sales_table_name)
        
        if len(back_to_rising_goods) > 0:
            if 'back_to_rising' not in category_goods_info or len(category_goods_info['back_to_rising']) == 0:
                df_back_to_rising = get_goods_data_by_ids(table_name, sales_table_name, back_to_rising_goods, target_date, filter_mode=filter_mode)
                if len(df_back_to_rising) > 0:
                    category_goods_info['back_to_rising'] = get_goods_info_with_status(df_back_to_rising, table_name, sales_table_name)
        
        if len(declined_from_rising_goods) > 0:
            if 'declined_from_rising' not in category_goods_info or len(category_goods_info['declined_from_rising']) == 0:
                df_declined_from_rising = get_goods_data_by_ids(table_name, sales_table_name, declined_from_rising_goods, target_date, filter_mode=filter_mode)
                if len(df_declined_from_rising) > 0:
                    category_goods_info['declined_from_rising'] = get_goods_info_with_status(df_declined_from_rising, table_name, sales_table_name)
        
        # 获取上升期和非上升期的商品信息（如果没有获取过）
        if len(rising_goods_ids) > 0:
            if 'rising' not in category_goods_info or len(category_goods_info['rising']) == 0:
                df_rising_selected = get_goods_data_by_ids(table_name, sales_table_name, list(rising_goods_ids), target_date, filter_mode=filter_mode)
                if len(df_rising_selected) > 0:
                    category_goods_info['rising'] = get_goods_info_with_status(df_rising_selected, table_name, sales_table_name)
        
        if len(declined_goods_ids) > 0:
            if 'declined' not in category_goods_info or len(category_goods_info['declined']) == 0:
                df_declined_selected = get_goods_data_by_ids(table_name, sales_table_name, list(declined_goods_ids), target_date, filter_mode=filter_mode)
                if len(df_declined_selected) > 0:
                    category_goods_info['declined'] = get_goods_info_with_status(df_declined_selected, table_name, sales_table_name)
        
        # 基本信息统计（参考看图专用NL.ipynb的格式）
        rising_summary = {}
        if len(df_rising) > 0:
            min_date = df_rising['date'].min()
            max_date = df_rising['date'].max()
            date_range = (max_date - min_date).days + 1
            rising_summary = {
                'total_records': len(df_rising),
                'unique_goods': df_rising['goods_id'].nunique(),
                'min_date': min_date.strftime('%Y-%m-%d'),
                'max_date': max_date.strftime('%Y-%m-%d'),
                'date_range': date_range
            }
        
        declined_summary = {}
        if len(df_declined) > 0:
            min_date = df_declined['date'].min()
            max_date = df_declined['date'].max()
            date_range = (max_date - min_date).days + 1
            declined_summary = {
                'total_records': len(df_declined),
                'unique_goods': df_declined['goods_id'].nunique(),
                'min_date': min_date.strftime('%Y-%m-%d'),
                'max_date': max_date.strftime('%Y-%m-%d'),
                'date_range': date_range
            }
        
        # 计算汇总统计信息（上升期 + 非上升期）
        total_summary = {}
        if len(df_rising) > 0 or len(df_declined) > 0:
            # 合并两个DataFrame用于计算汇总统计
            if len(df_rising) > 0 and len(df_declined) > 0:
                df_combined = pd.concat([df_rising, df_declined], ignore_index=True)
            elif len(df_rising) > 0:
                df_combined = df_rising.copy()
            else:
                df_combined = df_declined.copy()
            
            min_date = df_combined['date'].min()
            max_date = df_combined['date'].max()
            date_range = (max_date - min_date).days + 1
            
            # 统计Reason类别数量（从当前页面显示的goods_info中统计）
            all_goods_info = []
            if rising_info:
                all_goods_info.extend(rising_info)
            if declined_info:
                all_goods_info.extend(declined_info)
            
            reason_counts = count_reason_categories(all_goods_info)
            
            # 生成Reason类别饼图
            reason_pie_chart = None
            if any(reason_counts.values()):  # 如果有任何类别的数量大于0
                from plot_utils import plot_reason_category_pie
                reason_pie_chart = plot_reason_category_pie(reason_counts)
            
            # 计算在售占比：(None + Normal) / 总去重商品ID数量
            unique_goods_count = df_combined['goods_id'].nunique()
            on_sale_ratio = 0.0
            if unique_goods_count > 0:
                on_sale_count = reason_counts['None'] + reason_counts['Normal']
                on_sale_ratio = (on_sale_count / unique_goods_count) * 100
            
            total_summary = {
                'total_records': len(df_combined),
                'unique_goods': unique_goods_count,
                'min_date': min_date.strftime('%Y-%m-%d'),
                'max_date': max_date.strftime('%Y-%m-%d'),
                'date_range': date_range,
                'out_of_stock_count': reason_counts['Out_of_stock'],
                'secondary_traffic_restricted_count': reason_counts['Secondary_traffic_restricted'],
                'blocked_count': reason_counts['Blocked'],
                'normal_count': reason_counts['Normal'],
                'none_count': reason_counts['None'],
                'on_sale_ratio': on_sale_ratio,  # 在售占比（百分数）
                'reason_pie_chart': reason_pie_chart  # 添加饼图
            }
        
        # 保存历史记录到txt文件
        save_dynamic_management_history(target_date, stats, rising_info, declined_info, table_name)
        
        # 计算分析时间
        end_time = time.time()
        analysis_time = end_time - start_time
        
        # 保存缓存（不包含图片）
        save_dynamic_management_cache(
            table_name, target_date, stats, rising_info, declined_info,
            rising_summary, declined_summary, analysis_time, total_summary
        )
        
        # 构建返回数据，包含所有类别的数据
        return {
            'success': True,
            'data': {
                'statistics': stats,
                'rising': {
                    'images': category_images.get('rising', []),
                    'goods_info': rising_info,
                    'summary': rising_summary
                },
                'declined': {
                    'images': category_images.get('declined', []),
                    'goods_info': declined_info,
                    'summary': declined_summary
                },
                'total_summary': total_summary,  # 添加汇总统计信息
                'categories': {
                    'new_rising': {
                        'images': category_images.get('new_rising', []),
                        'goods_info': category_goods_info.get('new_rising', [])
                    },
                    'new_declined': {
                        'images': category_images.get('new_declined', []),
                        'goods_info': category_goods_info.get('new_declined', [])
                    },
                    'updated_to_rising': {
                        'images': category_images.get('updated_to_rising', []),
                        'goods_info': category_goods_info.get('updated_to_rising', [])
                    },
                    'back_to_rising': {
                        'images': category_images.get('back_to_rising', []),
                        'goods_info': category_goods_info.get('back_to_rising', [])
                    },
                    'declined_from_rising': {
                        'images': category_images.get('declined_from_rising', []),
                        'goods_info': category_goods_info.get('declined_from_rising', [])
                    }
                }
            },
            'error': None,
            'analysis_time': round(analysis_time, 2),
            'from_cache': False
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        end_time = time.time()
        analysis_time = end_time - start_time
        return {
            'success': False,
            'data': None,
            'error': str(e),
            'analysis_time': round(analysis_time, 2),
            'from_cache': False
        }


def get_goods_all_history_data(table_name, sales_table_name, status, target_date):
    """
    获取指定状态商品的所有历史数据（不仅仅是目标日期）
    status: 1=上升期, 2=非上升期
    """
    from config import get_db_config
    import pymysql
    
    traffic_config, sales_config, pallet_config, product_config = get_db_config()
    conn = pymysql.connect(**traffic_config)
    conn_sales = pymysql.connect(**sales_config)
    
    try:
        cursor = conn.cursor()
        cursor_sales = conn_sales.cursor()
        
        # 先找到目标日期有指定Status的商品
        query_goods = f"""
        SELECT DISTINCT t.goods_id
        FROM `Vida_Traffic`.`{table_name}` t
        WHERE t.date_label = %s
          AND t.Status = %s
          AND EXISTS (
              SELECT 1
              FROM `Vida_Sales`.`{sales_table_name}` s
              WHERE s.goods_id = t.goods_id
          )
        """
        cursor.execute(query_goods, (target_date, status))
        goods_ids = [row[0] for row in cursor.fetchall()]
        
        if len(goods_ids) == 0:
            return pd.DataFrame()
        
        # 获取这些商品的所有历史数据
        placeholders = ','.join(['%s'] * len(goods_ids))
        query_history = f"""
        SELECT 
          t.*,
          s.Buyers
        FROM `Vida_Traffic`.`{table_name}` t
        LEFT JOIN `Vida_Sales`.`{sales_table_name}` s
          ON t.goods_id = s.goods_id
          AND t.date_label = s.date_label
        WHERE t.goods_id IN ({placeholders})
        ORDER BY t.goods_id, t.date_label;
        """
        cursor.execute(query_history, goods_ids)
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


def get_goods_data_by_ids(table_name, sales_table_name, goods_ids, target_date, filter_mode=None):
    """
    根据goods_id列表获取商品的历史数据
    参数:
        table_name: 表名
        sales_table_name: 销售表名
        goods_ids: goods_id列表
        target_date: 目标日期（数据截止日期）
        filter_mode: 过滤模式，None=不过滤, 2=总和>1, 3=总和>2
    返回: DataFrame
    """
    from config import get_db_config
    import pymysql
    
    if len(goods_ids) == 0:
        return pd.DataFrame()
    
    traffic_config, sales_config, pallet_config, product_config = get_db_config()
    conn = pymysql.connect(**traffic_config)
    conn_sales = pymysql.connect(**sales_config)
    
    try:
        cursor = conn.cursor()
        cursor_sales = conn_sales.cursor()
        
        # 获取这些商品的所有历史数据
        placeholders = ','.join(['%s'] * len(goods_ids))
        query_data = f"""
        SELECT
          t.*,
          s.Buyers
        FROM `Vida_Traffic`.`{table_name}` t
        LEFT JOIN `Vida_Sales`.`{sales_table_name}` s
          ON t.goods_id = s.goods_id
          AND t.date_label = s.date_label
        WHERE t.goods_id IN ({placeholders})
          AND t.date_label <= %s
        ORDER BY t.goods_id, t.date_label;
        """
        cursor.execute(query_data, goods_ids + [target_date])
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
        
        # 应用过滤模式
        if filter_mode is not None:
            min_val = filter_mode.get('min', 0)
            max_val = filter_mode.get('max')
            # 计算每个goods_id的历史Buyers总和
            goods_buyers_sum = df.groupby('goods_id')['Buyers'].sum()
            # 过滤出总和满足条件的goods_id
            if max_val is not None:
                valid_goods_ids = goods_buyers_sum[(goods_buyers_sum >= min_val) & (goods_buyers_sum <= max_val)].index.tolist()
            else:
                valid_goods_ids = goods_buyers_sum[goods_buyers_sum >= min_val].index.tolist()
            df = df[df['goods_id'].isin(valid_goods_ids)].copy()
        
        return df
    finally:
        cursor.close()
        cursor_sales.close()
        conn.close()
        conn_sales.close()


def get_declined_from_rising_goods_data(table_name, sales_table_name, target_date):
    """
    获取由上升期到非上升期的商品数据
    返回: DataFrame
    """
    from config import get_db_config
    import pymysql
    
    traffic_config, sales_config, pallet_config, product_config = get_db_config()
    conn = pymysql.connect(**traffic_config)
    conn_sales = pymysql.connect(**sales_config)
    
    try:
        cursor = conn.cursor()
        cursor_sales = conn_sales.cursor()
        
        # 获取前一天是Status=1，选定日期是Status=2的商品
        query = f"""
        SELECT DISTINCT t1.goods_id
        FROM `Vida_Traffic`.`{table_name}` t1
        INNER JOIN `Vida_Traffic`.`{table_name}` t2
          ON t1.goods_id = t2.goods_id
        WHERE t1.date_label = DATE_SUB(%s, INTERVAL 1 DAY)
          AND t1.Status = 1
          AND t2.date_label = %s
          AND t2.Status = 2
          AND EXISTS (
              SELECT 1
              FROM `Vida_Sales`.`{sales_table_name}` s
              WHERE s.goods_id = t1.goods_id
          )
        """
        cursor.execute(query, (target_date, target_date))
        declined_goods_ids = [row[0] for row in cursor.fetchall()]
        
        if len(declined_goods_ids) == 0:
            return pd.DataFrame()
        
        # 获取这些商品的所有历史数据
        placeholders = ','.join(['%s'] * len(declined_goods_ids))
        query_data = f"""
        SELECT
          t.*,
          s.Buyers
        FROM `Vida_Traffic`.`{table_name}` t
        LEFT JOIN `Vida_Sales`.`{sales_table_name}` s
          ON t.goods_id = s.goods_id
          AND t.date_label = s.date_label
        WHERE t.goods_id IN ({placeholders})
          AND t.date_label <= %s
        ORDER BY t.goods_id, t.date_label;
        """
        cursor.execute(query_data, declined_goods_ids + [target_date])
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


def get_latest_reason_for_goods_ids(cursor, table_name, goods_ids):
    """
    获取多个goods_id的历史最新非空Reason
    返回: dict {goods_id: reason}
    """
    if len(goods_ids) == 0:
        return {}
    
    placeholders = ','.join(['%s'] * len(goods_ids))
    # 使用子查询获取每个goods_id的最新Reason（按date_label降序，取第一条）
    # 如果同一个goods_id在同一天有多条记录，取任意一条（通常不会发生）
    query = f"""
    SELECT 
        t1.goods_id,
        t1.Reason
    FROM `{table_name}` t1
    INNER JOIN (
        SELECT goods_id, MAX(date_label) as max_date
        FROM `{table_name}`
        WHERE goods_id IN ({placeholders})
          AND Reason IS NOT NULL
          AND Reason != ''
        GROUP BY goods_id
    ) t2 ON t1.goods_id = t2.goods_id AND t1.date_label = t2.max_date
    WHERE t1.Reason IS NOT NULL
      AND t1.Reason != ''
    GROUP BY t1.goods_id
    """
    cursor.execute(query, goods_ids)
    results = cursor.fetchall()
    
    # 构建goods_id到最新Reason的映射
    reason_map = {}
    for goods_id, reason in results:
        reason_map[goods_id] = reason
    
    return reason_map


def export_dynamic_management_data(target_date=None, export_format='xlsx', status_filter='all', date_range='single', selected_fields=None):
    """
    导出动销品管理数据
    参数:
        target_date: 目标日期
        export_format: 'csv' 或 'xlsx'
        status_filter: '1' (上升期), '2' (非上升期), 'all' (全部), 'declined_from_rising' (由上升期到非上升期)
        date_range: 'single' (只导出选择日期) 或 'all' (导出goods_id的所有历史日期)
        selected_fields: 要导出的字段列表，如果为None则导出所有字段
    返回: (file_data, filename, mime_type)
    """
    import io
    from datetime import datetime
    from db_utils import get_dynamic_goods_data, get_yesterday_date
    from config import get_current_table
    
    try:
        if target_date is None:
            target_date = get_yesterday_date()
        
        table_name = get_current_table()
        sales_table_name = f"{table_name}_Sales"
        
        # 根据date_range决定获取数据的方式
        if status_filter == 'declined_from_rising':
            # 导出"由上升期到非上升期"的数据
            if date_range == 'all':
                df_declined_from_rising = get_declined_from_rising_goods_data(table_name, sales_table_name, target_date)
            else:
                # 只获取目标日期的数据
                df_declined_from_rising = get_declined_from_rising_goods_data(table_name, sales_table_name, target_date)
                if len(df_declined_from_rising) > 0 and 'date_label' in df_declined_from_rising.columns:
                    df_declined_from_rising['date_label'] = pd.to_datetime(df_declined_from_rising['date_label'], errors='coerce')
                    target_date_dt = pd.to_datetime(target_date)
                    df_declined_from_rising = df_declined_from_rising[df_declined_from_rising['date_label'].dt.date == target_date_dt.date()].copy()
            df_rising = pd.DataFrame()
            df_declined = df_declined_from_rising
        elif date_range == 'all':
            # 获取所有历史数据
            if status_filter == '1' or status_filter == 'all':
                df_rising = get_goods_all_history_data(table_name, sales_table_name, 1, target_date)
            else:
                df_rising = pd.DataFrame()
            
            if status_filter == '2' or status_filter == 'all':
                # 对于非上升期，使用包含下架缺货商品的函数
                df_declined = get_declined_goods_data_with_discontinued(table_name, sales_table_name, target_date)
            else:
                df_declined = pd.DataFrame()
        else:
            # 只获取目标日期的数据
            if status_filter == '1' or status_filter == 'all':
                df_rising = get_dynamic_goods_data(table_name, sales_table_name, 1, target_date)
            else:
                df_rising = pd.DataFrame()
            
            if status_filter == '2' or status_filter == 'all':
                # 对于非上升期，使用包含下架缺货商品的函数
                df_declined = get_declined_goods_data_with_discontinued(table_name, sales_table_name, target_date)
            else:
                df_declined = pd.DataFrame()
        
        # 如果是单日模式，过滤掉非目标日期的数据
        if date_range == 'single':
            if len(df_rising) > 0 and 'date_label' in df_rising.columns:
                # 确保date_label是字符串格式以便比较
                df_rising['date_label'] = pd.to_datetime(df_rising['date_label'], errors='coerce')
                target_date_dt = pd.to_datetime(target_date)
                df_rising = df_rising[df_rising['date_label'].dt.date == target_date_dt.date()].copy()
            
            if len(df_declined) > 0 and 'date_label' in df_declined.columns:
                # 确保date_label是字符串格式以便比较
                df_declined['date_label'] = pd.to_datetime(df_declined['date_label'], errors='coerce')
                target_date_dt = pd.to_datetime(target_date)
                df_declined = df_declined[df_declined['date_label'].dt.date == target_date_dt.date()].copy()
            
            # 如果是单日模式且需要Reason字段，使用历史最新Reason替换当日的Reason
            # 检查：1) 用户选择了Reason字段，或 2) DataFrame中本来就有Reason字段（导出所有字段时）
            needs_reason = False
            if selected_fields and 'Reason' in selected_fields:
                needs_reason = True
            elif (len(df_rising) > 0 and 'Reason' in df_rising.columns) or (len(df_declined) > 0 and 'Reason' in df_declined.columns):
                needs_reason = True
            
            if needs_reason:
                from config import get_db_config
                import pymysql
                
                traffic_config, _, _, _ = get_db_config()
                conn = pymysql.connect(**traffic_config)
                try:
                    cursor = conn.cursor()
                    
                    # 收集所有需要查询Reason的goods_id
                    all_goods_ids = []
                    if len(df_rising) > 0 and 'goods_id' in df_rising.columns:
                        all_goods_ids.extend(df_rising['goods_id'].unique().tolist())
                    if len(df_declined) > 0 and 'goods_id' in df_declined.columns:
                        all_goods_ids.extend(df_declined['goods_id'].unique().tolist())
                    
                    # 去重
                    all_goods_ids = list(set(all_goods_ids))
                    
                    if len(all_goods_ids) > 0:
                        # 获取所有goods_id的历史最新Reason
                        reason_map = get_latest_reason_for_goods_ids(cursor, table_name, all_goods_ids)
                        
                        # 更新df_rising中的Reason
                        if len(df_rising) > 0 and 'goods_id' in df_rising.columns:
                            if 'Reason' not in df_rising.columns:
                                df_rising['Reason'] = None
                            df_rising['Reason'] = df_rising['goods_id'].map(reason_map)
                        
                        # 更新df_declined中的Reason
                        if len(df_declined) > 0 and 'goods_id' in df_declined.columns:
                            if 'Reason' not in df_declined.columns:
                                df_declined['Reason'] = None
                            df_declined['Reason'] = df_declined['goods_id'].map(reason_map)
                    
                    cursor.close()
                finally:
                    conn.close()
        
        if len(df_rising) == 0 and len(df_declined) == 0:
            return None, None, None
        
        # 处理日期格式
        if len(df_rising) > 0 and 'date_label' in df_rising.columns:
            df_rising['date_label'] = pd.to_datetime(df_rising['date_label'], errors='coerce')
            df_rising['date_label'] = df_rising['date_label'].dt.strftime('%Y-%m-%d')
        
        if len(df_declined) > 0 and 'date_label' in df_declined.columns:
            df_declined['date_label'] = pd.to_datetime(df_declined['date_label'], errors='coerce')
            df_declined['date_label'] = df_declined['date_label'].dt.strftime('%Y-%m-%d')
        
        # 如果指定了字段选择，只保留选中的字段
        if selected_fields and len(selected_fields) > 0:
            # 确保选中的字段在DataFrame中存在
            if len(df_rising) > 0:
                available_fields = [f for f in selected_fields if f in df_rising.columns]
                if len(available_fields) > 0:
                    df_rising = df_rising[available_fields].copy()
                else:
                    df_rising = pd.DataFrame()
            
            if len(df_declined) > 0:
                available_fields = [f for f in selected_fields if f in df_declined.columns]
                if len(available_fields) > 0:
                    df_declined = df_declined[available_fields].copy()
                else:
                    df_declined = pd.DataFrame()
        
        # 字段选择后再次检查数据是否为空
        if len(df_rising) == 0 and len(df_declined) == 0:
            return None, None, None
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        table_suffix = table_name.replace('ROA1_', '')
        status_suffix = {
            'declined_from_rising': '由上升期到非上升期',
            '1': '上升期',
            '2': '非上升期',
            'all': '全部'
        }.get(status_filter, '全部')
        range_suffix = '单日' if date_range == 'single' else '全历史'
        ext = 'xlsx' if export_format == 'xlsx' else 'csv'
        filename = f'动销品管理_{table_suffix}_{target_date}_{status_suffix}_{range_suffix}_{timestamp}.{ext}'
        
        # 导出数据
        if export_format == 'xlsx':
            # 导出为Excel（使用多个工作表）
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if len(df_rising) > 0:
                    df_rising.to_excel(writer, index=False, sheet_name='上升期')
                if len(df_declined) > 0:
                    df_declined.to_excel(writer, index=False, sheet_name='非上升期')
            
            file_data = output.getvalue()
            mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            # 导出为CSV
            if len(df_rising) > 0 and len(df_declined) > 0:
                # 如果两个都有数据，合并到一个CSV（添加状态列）
                df_rising_copy = df_rising.copy()
                df_rising_copy['状态'] = '上升期'
                df_declined_copy = df_declined.copy()
                df_declined_copy['状态'] = '非上升期'
                df_combined = pd.concat([df_rising_copy, df_declined_copy], ignore_index=True)
                output = io.StringIO()
                df_combined.to_csv(output, index=False, encoding='utf-8-sig')
                file_data = output.getvalue().encode('utf-8-sig')
            elif len(df_rising) > 0:
                output = io.StringIO()
                df_rising.to_csv(output, index=False, encoding='utf-8-sig')
                file_data = output.getvalue().encode('utf-8-sig')
            else:
                output = io.StringIO()
                df_declined.to_csv(output, index=False, encoding='utf-8-sig')
                file_data = output.getvalue().encode('utf-8-sig')
            
            mime_type = 'text/csv; charset=utf-8'
        
        return file_data, filename, mime_type
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e


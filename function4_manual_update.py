# -*- coding: utf-8 -*-
"""
功能4：手动更新记录 + 自动更新Reason
"""

import os
import re
import pandas as pd
import pymysql
from datetime import datetime, timedelta
from db_utils import (
    update_reason, update_video, update_price,
    check_date_exists, get_latest_date_label, get_yesterday_date,
    get_db_connection
)
from config import (
    get_current_table, get_db_config,
    load_auto_reason_config, save_auto_reason_config, get_auto_reason_restricted_dir
)


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


# ===== 自动更新Reason功能 =====

def validate_auto_reason_config(restricted_dir):
    """
    验证自动更新Reason的配置目录
    返回: (is_valid, error_message, file_counts)
    """
    try:
        current_table = get_current_table()
        site_name = current_table  # 如 ROA1_CZ
        
        # 检查限流数据目录
        restricted_site_dir = os.path.join(restricted_dir, site_name)
        if not os.path.exists(restricted_site_dir):
            return False, f"限流数据目录不存在: {restricted_site_dir}", None
        
        restricted_files = [f for f in os.listdir(restricted_site_dir) if f.endswith('.xlsx')]
        if len(restricted_files) == 0:
            return False, f"限流数据目录中没有xlsx文件: {restricted_site_dir}", None
        
        file_counts = {
            'restricted_files': len(restricted_files)
        }
        
        return True, "验证成功", file_counts
    
    except Exception as e:
        return False, f"验证过程中出错: {str(e)}", None


def configure_auto_reason_directory(restricted_dir):
    """
    配置自动更新Reason的限流数据目录
    """
    try:
        if not restricted_dir:
            return {
                'success': False,
                'error': '限流数据目录不能为空'
            }
        
        # 验证目录
        is_valid, error_msg, file_counts = validate_auto_reason_config(restricted_dir)
        
        if not is_valid:
            return {
                'success': False,
                'error': error_msg
            }
        
        # 保存配置
        config_data = {
            'traffic_restricted_data_dir': restricted_dir
        }
        
        if save_auto_reason_config(config_data):
            return {
                'success': True,
                'message': '配置成功',
                'file_counts': file_counts
            }
        else:
            return {
                'success': False,
                'error': '保存配置失败'
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': f'配置过程中出错: {str(e)}'
        }


def get_auto_reason_config():
    """
    获取自动更新Reason的当前配置
    """
    try:
        config = load_auto_reason_config()
        return {
            'success': True,
            'data': config
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'获取配置时出错: {str(e)}'
        }


def normalize_goods_id(goods_id_val):
    """
    标准化goods_id格式
    处理浮点数（如12345.0）、科学计数法、字符串等各种格式
    返回: 标准化的字符串格式goods_id（只保留数字字符），如果无效则返回None
    """
    if goods_id_val is None or pd.isna(goods_id_val):
        return None
    
    goods_id_str = str(goods_id_val).strip()
    
    # 过滤无效值
    if not goods_id_str or goods_id_str.lower() in ['nan', 'none', '']:
        return None
    
    # 去除所有非数字字符，只保留数字
    digits_only = ''.join(c for c in goods_id_str if c.isdigit())
    
    if not digits_only:
        return None
    
    return digits_only


def read_restricted_goods_ids_from_xlsx(restricted_dir, site_name):
    """
    从限流数据xlsx文件中读取goods_id
    从第3列（列名Goods ID）第3行开始读取
    返回: set of goods_id
    """
    restricted_goods_ids = set()
    
    try:
        restricted_site_dir = os.path.join(restricted_dir, site_name)
        if not os.path.exists(restricted_site_dir):
            return restricted_goods_ids
        
        restricted_files = [f for f in os.listdir(restricted_site_dir) if f.endswith('.xlsx')]
        
        for file in restricted_files:
            file_path = os.path.join(restricted_site_dir, file)
            try:
                # 尝试读取Template sheet，如果不存在则读取第一个sheet
                try:
                    df = pd.read_excel(file_path, sheet_name='Template', header=None)
                except:
                    df = pd.read_excel(file_path, header=None)
                
                if len(df) > 2 and len(df.columns) > 2:
                    # 从第3行（索引2）开始，读取第3列（索引2）的所有数据
                    goods_id_column = df.iloc[2:, 2]
                    for goods_id_val in goods_id_column:
                        if pd.notna(goods_id_val):
                            goods_id_str = str(goods_id_val).strip()
                            if goods_id_str and goods_id_str.lower() not in ['nan', 'none', '']:
                                # 处理可能的换行符、制表符等
                                goods_id_str = goods_id_str.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                                ids = goods_id_str.split()
                                for goods_id in ids:
                                    normalized_id = normalize_goods_id(goods_id)
                                    if normalized_id:
                                        restricted_goods_ids.add(normalized_id)
            except Exception as e:
                print(f"读取限流文件 {file} 出错: {e}")
                continue
        
        return restricted_goods_ids
    
    except Exception as e:
        print(f"读取限流数据出错: {e}")
        return set()


def get_product_status_goods(table_name, status_value):
    """
    从商品表获取指定detail_status的goods_id列表
    status_value: 'Out of stock', 'Blocked', 'At Risk', 'Active'
    返回: set of goods_id
    """
    _, _, _, product_config = get_db_config()
    
    try:
        conn = get_db_connection(product_config)
        cursor = conn.cursor()
        
        query = f"""
        SELECT DISTINCT goods_id
        FROM `{table_name}`
        WHERE detail_status = %s
        """
        cursor.execute(query, (status_value,))
        results = cursor.fetchall()
        
        goods_ids = set()
        for row in results:
            normalized_id = normalize_goods_id(row[0])
            if normalized_id:
                goods_ids.add(normalized_id)
        
        cursor.close()
        conn.close()
        
        return goods_ids
    
    except Exception as e:
        print(f"获取商品状态数据出错: {e}")
        return set()


def get_dynamic_goods_with_yesterday_data(table_name, sales_table_name, target_date):
    """
    获取在流量表中target_date有数据，且在销售表中历史Buyers > 1的动销品goods_id
    返回: set of goods_id
    """
    traffic_config, sales_config, _, _ = get_db_config()
    
    try:
        conn_traffic = get_db_connection(traffic_config)
        conn_sales = get_db_connection(sales_config)
        cursor_traffic = conn_traffic.cursor()
        cursor_sales = conn_sales.cursor()
        
        # 获取在target_date有数据的goods_id
        query_traffic = f"""
        SELECT DISTINCT goods_id
        FROM `{table_name}`
        WHERE date_label = %s
        """
        cursor_traffic.execute(query_traffic, (target_date,))
        traffic_goods = set()
        for row in cursor_traffic.fetchall():
            normalized_id = normalize_goods_id(row[0])
            if normalized_id:
                traffic_goods.add(normalized_id)
        
        # 获取销售表中历史Buyers > 1的动销品
        query_sales = f"""
        SELECT goods_id, SUM(COALESCE(Buyers, 0)) as total_buyers
        FROM `{sales_table_name}`
        GROUP BY goods_id
        HAVING total_buyers > 1
        """
        cursor_sales.execute(query_sales)
        sales_goods = set()
        for row in cursor_sales.fetchall():
            normalized_id = normalize_goods_id(row[0])
            if normalized_id:
                sales_goods.add(normalized_id)
        
        # 取交集
        result = traffic_goods.intersection(sales_goods)
        
        cursor_traffic.close()
        cursor_sales.close()
        conn_traffic.close()
        conn_sales.close()
        
        return result
    
    except Exception as e:
        print(f"获取动销品数据出错: {e}")
        import traceback
        traceback.print_exc()
        return set()


def check_has_yesterday_data(table_name, target_date):
    """
    检查流量表中是否有target_date的数据
    返回: (has_data, count)
    """
    traffic_config, _, _, _ = get_db_config()
    
    try:
        conn = get_db_connection(traffic_config)
        cursor = conn.cursor()
        
        query = f"""
        SELECT COUNT(*) FROM `{table_name}` WHERE date_label = %s
        """
        cursor.execute(query, (target_date,))
        result = cursor.fetchone()
        count = result[0] if result else 0
        
        cursor.close()
        conn.close()
        
        return count > 0, count
    
    except Exception as e:
        print(f"检查昨日数据出错: {e}")
        return False, 0


def get_goods_reason_history(table_name, goods_id):
    """
    获取指定goods_id的Reason历史记录
    返回: list of (date_label, reason)，按日期降序
    """
    traffic_config, _, _, _ = get_db_config()
    
    try:
        conn = get_db_connection(traffic_config)
        cursor = conn.cursor()
        
        query = f"""
        SELECT date_label, Reason
        FROM `{table_name}`
        WHERE goods_id = %s AND Reason IS NOT NULL AND Reason != ''
        ORDER BY date_label DESC
        """
        cursor.execute(query, (goods_id,))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return results
    
    except Exception as e:
        print(f"获取Reason历史出错: {e}")
        return []


def parse_reason_type(reason_str):
    """
    解析Reason字符串，获取括号外的类型
    如: "Blocked (Secondary_traffic_restricted_0125)" -> "Blocked"
    如: "Normal (Blocking_0125)" -> "Normal"
    如: "Out_of_stock (0125)" -> "Out_of_stock"
    返回: 括号外的类型字符串
    """
    if not reason_str:
        return None
    
    # 获取括号前的部分
    match = re.match(r'^([A-Za-z_]+)', reason_str.strip())
    if match:
        return match.group(1)
    return None


def has_previous_status_record(table_name, goods_id, status_types):
    """
    检查goods_id是否有之前的指定状态记录
    status_types: list of status type strings, e.g., ['Out_of_stock', 'Blocked', 'Secondary_traffic_restricted']
    返回: (has_record, last_status_type)
    """
    history = get_goods_reason_history(table_name, goods_id)
    
    for date_label, reason in history:
        reason_type = parse_reason_type(reason)
        if reason_type in status_types:
            return True, reason_type
    
    return False, None


def get_previous_abnormal_status(table_name, goods_id):
    """
    获取goods_id之前的异常状态记录（用于Normal (Xxx_0000)）
    返回: 最近的异常状态类型，如果没有返回None
    """
    abnormal_types = ['Out_of_stock', 'Blocked', 'Secondary_traffic_restricted']
    history = get_goods_reason_history(table_name, goods_id)
    
    for date_label, reason in history:
        reason_type = parse_reason_type(reason)
        if reason_type in abnormal_types:
            return reason_type
    
    return None


def batch_update_reason(table_name, goods_reason_dict, target_date):
    """
    批量更新Reason字段
    goods_reason_dict: {goods_id: reason_string}
    返回: (success_count, fail_count, errors)
    """
    traffic_config, _, _, _ = get_db_config()
    
    success_count = 0
    fail_count = 0
    errors = []
    
    try:
        conn = get_db_connection(traffic_config)
        cursor = conn.cursor()
        
        for goods_id, reason in goods_reason_dict.items():
            try:
                query = f"""
                UPDATE `{table_name}` 
                SET Reason = %s 
                WHERE goods_id = %s AND date_label = %s
                """
                cursor.execute(query, (reason, goods_id, target_date))
                if cursor.rowcount > 0:
                    success_count += 1
                else:
                    fail_count += 1
                    errors.append(f"goods_id {goods_id}: 未找到记录")
            except Exception as e:
                fail_count += 1
                errors.append(f"goods_id {goods_id}: {str(e)}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return success_count, fail_count, errors
    
    except Exception as e:
        print(f"批量更新Reason出错: {e}")
        return 0, len(goods_reason_dict), [str(e)]


def auto_update_reason():
    """
    自动更新Reason主函数
    只能更新昨天的数据
    """
    try:
        # 获取当前表名和昨天日期
        table_name = get_current_table()
        sales_table_name = f"{table_name}_Sales"
        yesterday = get_yesterday_date()
        
        # 生成日期后缀，如 0125
        yesterday_dt = datetime.strptime(yesterday, '%Y-%m-%d')
        date_suffix = yesterday_dt.strftime('%m%d')
        
        # 检查配置
        restricted_dir = get_auto_reason_restricted_dir()
        if not restricted_dir:
            return {
                'success': False,
                'error': '请先配置限流数据目录'
            }
        
        # 验证配置
        is_valid, error_msg, _ = validate_auto_reason_config(restricted_dir)
        if not is_valid:
            return {
                'success': False,
                'error': error_msg
            }
        
        # 检查昨天是否有数据
        has_data, data_count = check_has_yesterday_data(table_name, yesterday)
        if not has_data:
            return {
                'success': False,
                'error': f'昨日 ({yesterday}) 在流量表 {table_name} 中没有数据'
            }
        
        # 获取基础数据：昨天有数据且为动销品的goods_id
        base_goods_ids = get_dynamic_goods_with_yesterday_data(table_name, sales_table_name, yesterday)
        if len(base_goods_ids) == 0:
            return {
                'success': False,
                'error': f'昨日 ({yesterday}) 没有找到符合条件的动销品'
            }
        
        # 从商品表获取各状态的goods_id
        out_of_stock_goods = get_product_status_goods(table_name, 'Out of stock')
        blocked_goods = get_product_status_goods(table_name, 'Blocked')
        at_risk_goods = get_product_status_goods(table_name, 'At Risk')
        
        # 从xlsx文件读取限流数据
        restricted_goods = read_restricted_goods_ids_from_xlsx(restricted_dir, table_name)
        
        # 计算各类别的goods_id交集
        # 缺货
        out_of_stock_set = base_goods_ids.intersection(out_of_stock_goods)
        # 封禁
        blocked_set = base_goods_ids.intersection(blocked_goods)
        # 二次限流
        restricted_set = base_goods_ids.intersection(restricted_goods)
        # 二次限流+封禁（优先于单纯封禁）
        blocked_restricted_set = blocked_set.intersection(restricted_set)
        # 纯封禁（去除同时限流的）
        pure_blocked_set = blocked_set - blocked_restricted_set
        
        # 正常品 = 基础集合 - 缺货 - 二次限流 - 封禁
        abnormal_all = out_of_stock_set.union(restricted_set).union(blocked_set)
        normal_set = base_goods_ids - abnormal_all
        
        # 有风险的正常品
        normal_at_risk_set = normal_set.intersection(at_risk_goods)
        
        # 准备更新字典
        goods_reason_dict = {}
        stats = {
            'out_of_stock': 0,
            'blocked': 0,
            'secondary_traffic_restricted': 0,
            'blocked_secondary_traffic_restricted': 0,
            'normal': 0,
            'normal_recovered': 0,
            'normal_blocking': 0,
            'skipped': 0
        }
        
        # 异常状态类型列表（用于检查是否已有记录）
        abnormal_status_types = ['Out_of_stock', 'Blocked', 'Secondary_traffic_restricted']
        
        # 1. 处理缺货
        for goods_id in out_of_stock_set:
            has_record, _ = has_previous_status_record(table_name, goods_id, abnormal_status_types)
            if has_record:
                stats['skipped'] += 1
                continue
            goods_reason_dict[goods_id] = f"Out_of_stock ({date_suffix})"
            stats['out_of_stock'] += 1
        
        # 2. 处理二次限流+封禁（优先于单纯封禁）
        for goods_id in blocked_restricted_set:
            has_record, _ = has_previous_status_record(table_name, goods_id, abnormal_status_types)
            if has_record:
                stats['skipped'] += 1
                continue
            goods_reason_dict[goods_id] = f"Blocked (Secondary_traffic_restricted_{date_suffix})"
            stats['blocked_secondary_traffic_restricted'] += 1
        
        # 3. 处理纯封禁
        for goods_id in pure_blocked_set:
            has_record, _ = has_previous_status_record(table_name, goods_id, abnormal_status_types)
            if has_record:
                stats['skipped'] += 1
                continue
            goods_reason_dict[goods_id] = f"Blocked ({date_suffix})"
            stats['blocked'] += 1
        
        # 4. 处理纯二次限流（去除封禁的）
        pure_restricted_set = restricted_set - blocked_set
        for goods_id in pure_restricted_set:
            has_record, _ = has_previous_status_record(table_name, goods_id, abnormal_status_types)
            if has_record:
                stats['skipped'] += 1
                continue
            goods_reason_dict[goods_id] = f"Secondary_traffic_restricted ({date_suffix})"
            stats['secondary_traffic_restricted'] += 1
        
        # 5. 处理正常品
        for goods_id in normal_set:
            # 检查是否是有风险的正常品（优先级最高）
            if goods_id in normal_at_risk_set:
                goods_reason_dict[goods_id] = f"Normal (Blocking_{date_suffix})"
                stats['normal_blocking'] += 1
                continue
            
            # 检查是否有之前的异常状态记录（恢复正常）
            prev_status = get_previous_abnormal_status(table_name, goods_id)
            if prev_status:
                goods_reason_dict[goods_id] = f"Normal ({prev_status}_{date_suffix})"
                stats['normal_recovered'] += 1
                continue
            
            # 普通正常
            goods_reason_dict[goods_id] = f"Normal ({date_suffix})"
            stats['normal'] += 1
        
        # 执行批量更新
        success_count, fail_count, errors = batch_update_reason(table_name, goods_reason_dict, yesterday)
        
        # 构建返回结果
        result = {
            'success': True,
            'message': f'自动更新Reason完成',
            'target_date': yesterday,
            'date_suffix': date_suffix,
            'table_name': table_name,
            'stats': {
                'base_goods_count': len(base_goods_ids),
                'out_of_stock': stats['out_of_stock'],
                'blocked': stats['blocked'],
                'secondary_traffic_restricted': stats['secondary_traffic_restricted'],
                'blocked_secondary_traffic_restricted': stats['blocked_secondary_traffic_restricted'],
                'normal': stats['normal'],
                'normal_recovered': stats['normal_recovered'],
                'normal_blocking': stats['normal_blocking'],
                'skipped': stats['skipped'],
                'total_updated': success_count,
                'total_failed': fail_count
            },
            'data_sources': {
                'out_of_stock_goods_count': len(out_of_stock_goods),
                'blocked_goods_count': len(blocked_goods),
                'at_risk_goods_count': len(at_risk_goods),
                'restricted_goods_count': len(restricted_goods)
            }
        }
        
        if errors:
            result['errors'] = errors[:10]  # 只返回前10个错误
        
        return result
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f'自动更新Reason时出错: {str(e)}'
        }


def auto_update_reason_for_table(table_name):
    """
    针对指定表名自动更新Reason（用于批量操作）
    只能更新昨天的数据
    参数:
        table_name: 要更新的表名，如 ROA1_CZ
    返回: 与 auto_update_reason 相同的结果格式
    """
    try:
        sales_table_name = f"{table_name}_Sales"
        yesterday = get_yesterday_date()
        
        # 生成日期后缀，如 0125
        yesterday_dt = datetime.strptime(yesterday, '%Y-%m-%d')
        date_suffix = yesterday_dt.strftime('%m%d')
        
        # 检查配置
        restricted_dir = get_auto_reason_restricted_dir()
        if not restricted_dir:
            return {
                'success': False,
                'error': '请先配置限流数据目录'
            }
        
        # 验证配置（针对指定表名）
        restricted_site_dir = os.path.join(restricted_dir, table_name)
        if not os.path.exists(restricted_site_dir):
            return {
                'success': False,
                'error': f'限流数据目录不存在: {restricted_site_dir}'
            }
        
        restricted_files = [f for f in os.listdir(restricted_site_dir) if f.endswith('.xlsx')]
        if len(restricted_files) == 0:
            return {
                'success': False,
                'error': f'限流数据目录中没有xlsx文件: {restricted_site_dir}'
            }
        
        # 检查昨天是否有数据
        has_data, data_count = check_has_yesterday_data(table_name, yesterday)
        if not has_data:
            return {
                'success': False,
                'error': f'昨日 ({yesterday}) 在流量表 {table_name} 中没有数据'
            }
        
        # 获取基础数据：昨天有数据且为动销品的goods_id
        base_goods_ids = get_dynamic_goods_with_yesterday_data(table_name, sales_table_name, yesterday)
        if len(base_goods_ids) == 0:
            return {
                'success': False,
                'error': f'昨日 ({yesterday}) 没有找到符合条件的动销品'
            }
        
        # 从商品表获取各状态的goods_id
        out_of_stock_goods = get_product_status_goods(table_name, 'Out of stock')
        blocked_goods = get_product_status_goods(table_name, 'Blocked')
        at_risk_goods = get_product_status_goods(table_name, 'At Risk')
        
        # 从xlsx文件读取限流数据
        restricted_goods = read_restricted_goods_ids_from_xlsx(restricted_dir, table_name)
        
        # 计算各类别的goods_id交集
        # 缺货
        out_of_stock_set = base_goods_ids.intersection(out_of_stock_goods)
        # 封禁
        blocked_set = base_goods_ids.intersection(blocked_goods)
        # 二次限流
        restricted_set = base_goods_ids.intersection(restricted_goods)
        # 二次限流+封禁（优先于单纯封禁）
        blocked_restricted_set = blocked_set.intersection(restricted_set)
        # 纯封禁（去除同时限流的）
        pure_blocked_set = blocked_set - blocked_restricted_set
        
        # 正常品 = 基础集合 - 缺货 - 二次限流 - 封禁
        abnormal_all = out_of_stock_set.union(restricted_set).union(blocked_set)
        normal_set = base_goods_ids - abnormal_all
        
        # 有风险的正常品
        normal_at_risk_set = normal_set.intersection(at_risk_goods)
        
        # 准备更新字典
        goods_reason_dict = {}
        stats = {
            'out_of_stock': 0,
            'blocked': 0,
            'secondary_traffic_restricted': 0,
            'blocked_secondary_traffic_restricted': 0,
            'normal': 0,
            'normal_recovered': 0,
            'normal_blocking': 0,
            'skipped': 0
        }
        
        # 异常状态类型列表（用于检查是否已有记录）
        abnormal_status_types = ['Out_of_stock', 'Blocked', 'Secondary_traffic_restricted']
        
        # 1. 处理缺货
        for goods_id in out_of_stock_set:
            has_record, _ = has_previous_status_record(table_name, goods_id, abnormal_status_types)
            if has_record:
                stats['skipped'] += 1
                continue
            goods_reason_dict[goods_id] = f"Out_of_stock ({date_suffix})"
            stats['out_of_stock'] += 1
        
        # 2. 处理二次限流+封禁（优先于单纯封禁）
        for goods_id in blocked_restricted_set:
            has_record, _ = has_previous_status_record(table_name, goods_id, abnormal_status_types)
            if has_record:
                stats['skipped'] += 1
                continue
            goods_reason_dict[goods_id] = f"Blocked (Secondary_traffic_restricted_{date_suffix})"
            stats['blocked_secondary_traffic_restricted'] += 1
        
        # 3. 处理纯封禁
        for goods_id in pure_blocked_set:
            has_record, _ = has_previous_status_record(table_name, goods_id, abnormal_status_types)
            if has_record:
                stats['skipped'] += 1
                continue
            goods_reason_dict[goods_id] = f"Blocked ({date_suffix})"
            stats['blocked'] += 1
        
        # 4. 处理纯二次限流（去除封禁的）
        pure_restricted_set = restricted_set - blocked_set
        for goods_id in pure_restricted_set:
            has_record, _ = has_previous_status_record(table_name, goods_id, abnormal_status_types)
            if has_record:
                stats['skipped'] += 1
                continue
            goods_reason_dict[goods_id] = f"Secondary_traffic_restricted ({date_suffix})"
            stats['secondary_traffic_restricted'] += 1
        
        # 5. 处理正常品
        for goods_id in normal_set:
            # 检查是否是有风险的正常品（优先级最高）
            if goods_id in normal_at_risk_set:
                goods_reason_dict[goods_id] = f"Normal (Blocking_{date_suffix})"
                stats['normal_blocking'] += 1
                continue
            
            # 检查是否有之前的异常状态记录（恢复正常）
            prev_status = get_previous_abnormal_status(table_name, goods_id)
            if prev_status:
                goods_reason_dict[goods_id] = f"Normal ({prev_status}_{date_suffix})"
                stats['normal_recovered'] += 1
                continue
            
            # 普通正常
            goods_reason_dict[goods_id] = f"Normal ({date_suffix})"
            stats['normal'] += 1
        
        # 执行批量更新
        success_count, fail_count, errors = batch_update_reason(table_name, goods_reason_dict, yesterday)
        
        # 构建返回结果
        result = {
            'success': True,
            'message': f'自动更新Reason完成',
            'target_date': yesterday,
            'date_suffix': date_suffix,
            'table_name': table_name,
            'stats': {
                'base_goods_count': len(base_goods_ids),
                'out_of_stock': stats['out_of_stock'],
                'blocked': stats['blocked'],
                'secondary_traffic_restricted': stats['secondary_traffic_restricted'],
                'blocked_secondary_traffic_restricted': stats['blocked_secondary_traffic_restricted'],
                'normal': stats['normal'],
                'normal_recovered': stats['normal_recovered'],
                'normal_blocking': stats['normal_blocking'],
                'skipped': stats['skipped'],
                'total_updated': success_count,
                'total_failed': fail_count
            },
            'data_sources': {
                'out_of_stock_goods_count': len(out_of_stock_goods),
                'blocked_goods_count': len(blocked_goods),
                'at_risk_goods_count': len(at_risk_goods),
                'restricted_goods_count': len(restricted_goods)
            }
        }
        
        if errors:
            result['errors'] = errors[:10]  # 只返回前10个错误
        
        return result
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f'自动更新Reason时出错: {str(e)}'
        }


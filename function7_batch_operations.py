# -*- coding: utf-8 -*-
"""
功能7：批量国家站点运行
对多个国家数据表同时执行刷新、快速刷新、自动更新Reason、保存指标数据等操作
"""

import os
import json
from datetime import datetime, timedelta
from db_utils import get_db_connection
from config import (
    load_config, save_config, get_db_config,
    load_auto_reason_config
)


# ===== 配置管理 =====

def load_batch_countries_config():
    """
    加载批量国家站点配置
    返回: {
        'available_tables': ['ROA1_CZ', 'ROA1_DE', ...],  # 可用的国家表列表
        'selected_tables': ['ROA1_CZ', 'ROA1_DE', ...]    # 已选中的国家表列表
    }
    """
    config = load_config()
    return config.get('batch_countries_config', {
        'available_tables': [],
        'selected_tables': []
    })


def save_batch_countries_config(config_data):
    """保存批量国家站点配置"""
    config = load_config()
    config['batch_countries_config'] = config_data
    return save_config(config)


def add_country_table(table_name):
    """
    添加国家数据表到可用列表
    返回: (success, message)
    """
    if not table_name or not table_name.strip():
        return False, '表名不能为空'
    
    table_name = table_name.strip()
    
    # 验证表名格式（应以国家代称结尾，如ROA1_CZ）
    if len(table_name) < 3:
        return False, '表名格式不正确，应类似ROA1_CZ'
    
    config = load_batch_countries_config()
    available_tables = config.get('available_tables', [])
    
    if table_name in available_tables:
        return False, f'表 {table_name} 已存在于列表中'
    
    available_tables.append(table_name)
    config['available_tables'] = available_tables
    
    if save_batch_countries_config(config):
        return True, f'成功添加表: {table_name}'
    else:
        return False, '保存配置失败'


def remove_country_table(table_name):
    """
    从可用列表中移除国家数据表
    返回: (success, message)
    """
    config = load_batch_countries_config()
    available_tables = config.get('available_tables', [])
    selected_tables = config.get('selected_tables', [])
    
    if table_name not in available_tables:
        return False, f'表 {table_name} 不在列表中'
    
    available_tables.remove(table_name)
    if table_name in selected_tables:
        selected_tables.remove(table_name)
    
    config['available_tables'] = available_tables
    config['selected_tables'] = selected_tables
    
    if save_batch_countries_config(config):
        return True, f'成功移除表: {table_name}'
    else:
        return False, '保存配置失败'


def update_selected_tables(selected_tables):
    """
    更新已选中的国家表列表
    返回: (success, message)
    """
    config = load_batch_countries_config()
    available_tables = config.get('available_tables', [])
    
    # 验证选中的表都在可用列表中
    for table in selected_tables:
        if table not in available_tables:
            return False, f'表 {table} 不在可用列表中'
    
    config['selected_tables'] = selected_tables
    
    if save_batch_countries_config(config):
        return True, '已更新选中的国家表'
    else:
        return False, '保存配置失败'


# ===== 表存在性检查 =====

def get_country_code(table_name):
    """
    从表名中提取国家代称
    例如: ROA1_CZ -> CZ
    """
    if '_' in table_name:
        return table_name.split('_')[-1]
    return table_name[-2:] if len(table_name) >= 2 else table_name


def check_table_exists(db_config, table_name):
    """
    检查表是否存在于指定数据库中
    返回: (exists, error_message)
    """
    try:
        conn = get_db_connection(db_config)
        cursor = conn.cursor()
        
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return result is not None, None
    except Exception as e:
        return False, str(e)


def validate_country_tables(table_name):
    """
    验证国家数据表在所有相关数据库中是否存在
    返回: {
        'success': bool,
        'errors': [],
        'checks': {
            'traffic': {'exists': bool, 'table': str, 'error': str},
            'sales': {'exists': bool, 'table': str, 'error': str},
            'pallet': {'exists': bool, 'table': str, 'error': str},
            'product': {'exists': bool, 'table': str, 'error': str}
        }
    }
    """
    traffic_config, sales_config, pallet_config, product_config = get_db_config()
    country_code = get_country_code(table_name)
    
    checks = {
        'traffic': {'exists': False, 'table': table_name, 'error': None},
        'sales': {'exists': False, 'table': f'{table_name}_Sales', 'error': None},
        'pallet': {'exists': False, 'table': f'vidaxl_{country_code}', 'error': None},
        'product': {'exists': False, 'table': table_name, 'error': None}
    }
    errors = []
    
    # 检查Traffic数据库
    exists, error = check_table_exists(traffic_config, table_name)
    checks['traffic']['exists'] = exists
    checks['traffic']['error'] = error
    if not exists:
        errors.append(f"Traffic数据库中不存在表 {table_name}" + (f": {error}" if error else ""))
    
    # 检查Sales数据库
    sales_table = f'{table_name}_Sales'
    exists, error = check_table_exists(sales_config, sales_table)
    checks['sales']['exists'] = exists
    checks['sales']['error'] = error
    if not exists:
        errors.append(f"Sales数据库中不存在表 {sales_table}" + (f": {error}" if error else ""))
    
    # 检查货盘数据库（表名格式：vidaxl_XX，XX为国家代称小写）
    pallet_table = f'vidaxl_{country_code.lower()}'
    checks['pallet']['table'] = pallet_table
    exists, error = check_table_exists(pallet_config, pallet_table)
    checks['pallet']['exists'] = exists
    checks['pallet']['error'] = error
    if not exists:
        errors.append(f"货盘数据库中不存在表 {pallet_table}" + (f": {error}" if error else ""))
    
    # 检查平台商品表数据库
    exists, error = check_table_exists(product_config, table_name)
    checks['product']['exists'] = exists
    checks['product']['error'] = error
    if not exists:
        errors.append(f"平台商品表数据库中不存在表 {table_name}" + (f": {error}" if error else ""))
    
    return {
        'success': len(errors) == 0,
        'errors': errors,
        'checks': checks
    }


def validate_all_selected_tables():
    """
    验证所有已选中的国家表
    返回: {
        'success': bool,
        'total': int,
        'valid': int,
        'invalid': int,
        'results': {
            'ROA1_CZ': {...},
            ...
        }
    }
    """
    config = load_batch_countries_config()
    selected_tables = config.get('selected_tables', [])
    
    if not selected_tables:
        return {
            'success': False,
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'results': {},
            'error': '没有选中任何国家表'
        }
    
    results = {}
    valid_count = 0
    invalid_count = 0
    
    for table_name in selected_tables:
        validation = validate_country_tables(table_name)
        results[table_name] = validation
        if validation['success']:
            valid_count += 1
        else:
            invalid_count += 1
    
    return {
        'success': invalid_count == 0,
        'total': len(selected_tables),
        'valid': valid_count,
        'invalid': invalid_count,
        'results': results
    }


# ===== 批量操作：功能2 =====

def batch_refresh_status(selected_tables=None):
    """
    批量刷新Status数据（功能2的刷新功能）
    参数:
        selected_tables: 要处理的表列表，如果为None则使用配置中的已选表
    返回: {
        'success': bool,
        'total': int,
        'processed': int,
        'failed': int,
        'results': {
            'ROA1_CZ': {'success': bool, 'message': str, ...},
            ...
        }
    }
    """
    from function2_dynamic_management import refresh_status_data
    
    if selected_tables is None:
        config = load_batch_countries_config()
        selected_tables = config.get('selected_tables', [])
    
    if not selected_tables:
        return {
            'success': False,
            'error': '没有选中任何国家表',
            'total': 0,
            'processed': 0,
            'failed': 0,
            'results': {}
        }
    
    results = {}
    processed_count = 0
    failed_count = 0
    
    for table_name in selected_tables:
        try:
            sales_table_name = f"{table_name}_Sales"
            success, message, updated_count, missing_dates_info = refresh_status_data(table_name, sales_table_name)
            
            results[table_name] = {
                'success': success,
                'message': message,
                'updated_count': updated_count,
                'missing_dates_info': missing_dates_info
            }
            
            if success:
                processed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            results[table_name] = {
                'success': False,
                'message': f'刷新失败: {str(e)}',
                'updated_count': 0,
                'missing_dates_info': []
            }
            failed_count += 1
    
    return {
        'success': failed_count == 0,
        'total': len(selected_tables),
        'processed': processed_count,
        'failed': failed_count,
        'results': results
    }


def batch_quick_refresh_status(selected_tables=None):
    """
    批量快速刷新Status数据（功能2的快速刷新功能）
    参数:
        selected_tables: 要处理的表列表，如果为None则使用配置中的已选表
    返回: {
        'success': bool,
        'total': int,
        'processed': int,
        'failed': int,
        'results': {
            'ROA1_CZ': {'success': bool, 'message': str, ...},
            ...
        }
    }
    """
    from function2_dynamic_management import quick_refresh_status_data
    
    if selected_tables is None:
        config = load_batch_countries_config()
        selected_tables = config.get('selected_tables', [])
    
    if not selected_tables:
        return {
            'success': False,
            'error': '没有选中任何国家表',
            'total': 0,
            'processed': 0,
            'failed': 0,
            'results': {}
        }
    
    results = {}
    processed_count = 0
    failed_count = 0
    
    for table_name in selected_tables:
        try:
            sales_table_name = f"{table_name}_Sales"
            success, message, updated_count, missing_dates_info = quick_refresh_status_data(table_name, sales_table_name)
            
            results[table_name] = {
                'success': success,
                'message': message,
                'updated_count': updated_count,
                'missing_dates_info': missing_dates_info
            }
            
            if success:
                processed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            results[table_name] = {
                'success': False,
                'message': f'快速刷新失败: {str(e)}',
                'updated_count': 0,
                'missing_dates_info': []
            }
            failed_count += 1
    
    return {
        'success': failed_count == 0,
        'total': len(selected_tables),
        'processed': processed_count,
        'failed': failed_count,
        'results': results
    }


# ===== 批量操作：功能4 =====

def check_restricted_data_dir_for_country(restricted_dir, table_name):
    """
    检查限流数据目录中是否存在指定国家的数据
    返回: (exists, error_message)
    """
    if not restricted_dir:
        return False, '限流数据目录未配置'
    
    country_dir = os.path.join(restricted_dir, table_name)
    if not os.path.exists(country_dir):
        return False, f'限流数据目录中不存在 {table_name} 子目录'
    
    xlsx_files = [f for f in os.listdir(country_dir) if f.endswith('.xlsx')]
    if not xlsx_files:
        return False, f'{table_name} 目录中没有xlsx文件'
    
    return True, None


def batch_auto_update_reason(selected_tables=None):
    """
    批量自动更新Reason（功能4的自动更新Reason功能）
    参数:
        selected_tables: 要处理的表列表，如果为None则使用配置中的已选表
    返回: {
        'success': bool,
        'total': int,
        'processed': int,
        'failed': int,
        'skipped': int,
        'results': {
            'ROA1_CZ': {'success': bool, 'message': str, ...},
            ...
        }
    }
    """
    from function4_manual_update import auto_update_reason_for_table
    
    if selected_tables is None:
        config = load_batch_countries_config()
        selected_tables = config.get('selected_tables', [])
    
    if not selected_tables:
        return {
            'success': False,
            'error': '没有选中任何国家表',
            'total': 0,
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'results': {}
        }
    
    # 获取限流数据目录配置
    auto_reason_config = load_auto_reason_config()
    restricted_dir = auto_reason_config.get('traffic_restricted_data_dir', '')
    
    if not restricted_dir:
        return {
            'success': False,
            'error': '请先配置限流数据目录',
            'total': len(selected_tables),
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'results': {}
        }
    
    results = {}
    processed_count = 0
    failed_count = 0
    skipped_count = 0
    
    for table_name in selected_tables:
        # 先检查限流数据目录中是否存在该国家的数据
        exists, error = check_restricted_data_dir_for_country(restricted_dir, table_name)
        if not exists:
            results[table_name] = {
                'success': False,
                'message': error,
                'skipped': True
            }
            skipped_count += 1
            continue
        
        try:
            result = auto_update_reason_for_table(table_name)
            
            results[table_name] = result
            
            if result.get('success'):
                processed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            results[table_name] = {
                'success': False,
                'message': f'自动更新Reason失败: {str(e)}'
            }
            failed_count += 1
    
    return {
        'success': failed_count == 0 and skipped_count == 0,
        'total': len(selected_tables),
        'processed': processed_count,
        'failed': failed_count,
        'skipped': skipped_count,
        'results': results
    }


# ===== 批量操作：功能6 =====

def check_indicator_data_dir_for_country(unpriced_dir, restricted_dir, table_name):
    """
    检查指标计算数据目录中是否存在指定国家的数据
    返回: (exists, error_message)
    """
    errors = []
    
    # 检查未核价数据目录
    if unpriced_dir:
        unpriced_country_dir = os.path.join(unpriced_dir, table_name)
        if not os.path.exists(unpriced_country_dir):
            errors.append(f'未核价数据目录中不存在 {table_name} 子目录')
        else:
            xlsx_files = [f for f in os.listdir(unpriced_country_dir) if f.endswith('.xlsx')]
            if not xlsx_files:
                errors.append(f'未核价数据 {table_name} 目录中没有xlsx文件')
    else:
        errors.append('未核价数据目录未配置')
    
    # 检查限流数据目录
    if restricted_dir:
        restricted_country_dir = os.path.join(restricted_dir, table_name)
        if not os.path.exists(restricted_country_dir):
            errors.append(f'限流数据目录中不存在 {table_name} 子目录')
        else:
            xlsx_files = [f for f in os.listdir(restricted_country_dir) if f.endswith('.xlsx')]
            if not xlsx_files:
                errors.append(f'限流数据 {table_name} 目录中没有xlsx文件')
    else:
        errors.append('限流数据目录未配置')
    
    if errors:
        return False, '; '.join(errors)
    
    return True, None


def batch_save_indicator_data(selected_tables=None, target_date=None):
    """
    批量保存指标数据（功能6的保存指标数据功能）
    会先计算指标到缓存，再保存到对应xlsx文件
    参数:
        selected_tables: 要处理的表列表，如果为None则使用配置中的已选表
        target_date: 目标日期，如果为None则使用昨天
    返回: {
        'success': bool,
        'total': int,
        'processed': int,
        'failed': int,
        'skipped': int,
        'results': {
            'ROA1_CZ': {'success': bool, 'message': str, ...},
            ...
        }
    }
    """
    from function6_indicator_calculation import (
        indicator_calculation_for_table,
        save_indicator_data_to_excel_for_table,
        load_indicator_config
    )
    
    if selected_tables is None:
        config = load_batch_countries_config()
        selected_tables = config.get('selected_tables', [])
    
    if not selected_tables:
        return {
            'success': False,
            'error': '没有选中任何国家表',
            'total': 0,
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'results': {}
        }
    
    # 获取指标数据目录配置
    indicator_config = load_indicator_config()
    unpriced_dir = indicator_config.get('unpriced_data_dir', '')
    restricted_dir = indicator_config.get('traffic_restricted_data_dir', '')
    
    if not unpriced_dir or not restricted_dir:
        return {
            'success': False,
            'error': '请先配置数据目录（未核价数据目录和限流数据目录）',
            'total': len(selected_tables),
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'results': {}
        }
    
    results = {}
    processed_count = 0
    failed_count = 0
    skipped_count = 0
    
    for table_name in selected_tables:
        # 先检查数据目录中是否存在该国家的数据
        exists, error = check_indicator_data_dir_for_country(unpriced_dir, restricted_dir, table_name)
        if not exists:
            results[table_name] = {
                'success': False,
                'message': error,
                'skipped': True
            }
            skipped_count += 1
            continue
        
        try:
            # 1. 先计算指标（不使用缓存，确保数据是最新的）
            calc_result = indicator_calculation_for_table(table_name, target_date=target_date, use_cache=False)
            
            if not calc_result.get('success'):
                results[table_name] = {
                    'success': False,
                    'message': f'计算指标失败: {calc_result.get("error", "未知错误")}'
                }
                failed_count += 1
                continue
            
            # 2. 保存指标数据到Excel
            save_result = save_indicator_data_to_excel_for_table(table_name, target_date=target_date)
            
            if save_result.get('success'):
                results[table_name] = {
                    'success': True,
                    'message': '计算并保存指标数据成功',
                    'calc_time': calc_result.get('analysis_time', 0)
                }
                processed_count += 1
            else:
                results[table_name] = {
                    'success': False,
                    'message': f'保存指标数据失败: {save_result.get("error", "未知错误")}'
                }
                failed_count += 1
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            results[table_name] = {
                'success': False,
                'message': f'处理失败: {str(e)}'
            }
            failed_count += 1
    
    return {
        'success': failed_count == 0 and skipped_count == 0,
        'total': len(selected_tables),
        'processed': processed_count,
        'failed': failed_count,
        'skipped': skipped_count,
        'results': results
    }


# ===== API辅助函数 =====

def get_batch_config():
    """
    获取批量操作的完整配置信息
    """
    config = load_batch_countries_config()
    return {
        'success': True,
        'data': config
    }

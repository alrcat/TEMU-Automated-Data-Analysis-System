# -*- coding: utf-8 -*-
"""
功能5：数据筛选
"""

import pandas as pd
import io
from datetime import datetime
from db_utils import get_filtered_data, get_db_connection, get_db_config
from config import get_current_table


def calculate_mean_by_goods_id(df, sort_field=None, sort_order='asc', table_name=None):
    """
    按goods_id分组计算均值
    返回处理后的DataFrame，每个goods_id只有一条记录（均值）
    table_name: 表名，用于从数据库查询Video、Price、Reason字段的最新值（如果筛选后的数据中没有）
    """
    if 'goods_id' not in df.columns:
        return df
    
    # 数值字段列表（需要计算均值）
    numeric_columns = [
        'Product impressions',
        'Number of visitor impressions of the product',
        'Product clicks',
        'Number of visitor clicks on the product',
        'CTR'
    ]
    
    # 只保留存在的数值列
    numeric_columns = [col for col in numeric_columns if col in df.columns]
    
    # 分组聚合
    agg_dict = {}
    
    # 数值字段计算均值
    for col in numeric_columns:
        agg_dict[col] = 'mean'
    
    # goods_id保留（用于分组）
    # date_label显示日期范围
    if 'date_label' in df.columns:
        def format_date_range(x):
            if len(x) == 0:
                return None
            elif len(x) == 1:
                date_val = x.iloc[0]
                if pd.isna(date_val):
                    return None
                if isinstance(date_val, pd.Timestamp):
                    return date_val.strftime('%Y-%m-%d')
                return str(date_val)
            else:
                min_date = x.min()
                max_date = x.max()
                if pd.isna(min_date) or pd.isna(max_date):
                    return None
                if isinstance(min_date, pd.Timestamp):
                    min_str = min_date.strftime('%Y-%m-%d')
                else:
                    min_str = str(min_date)
                if isinstance(max_date, pd.Timestamp):
                    max_str = max_date.strftime('%Y-%m-%d')
                else:
                    max_str = str(max_date)
                return f"{min_str} 至 {max_str}"
        agg_dict['date_label'] = format_date_range
    
    # Status字段：如果有多个值，显示范围或第一个值
    if 'Status' in df.columns:
        agg_dict['Status'] = lambda x: x.iloc[0] if len(x) > 0 else None
    
    # 执行分组聚合（先不处理Reason、Video、Price）
    df_mean = df.groupby('goods_id').agg(agg_dict).reset_index()
    
    # 对于Reason、Video、Price字段，需要按最新日期选取
    # 先按goods_id和date_label排序（date_label降序，最新的在前）
    if 'date_label' in df.columns:
        df_sorted = df.sort_values(['goods_id', 'date_label'], ascending=[True, False])
    else:
        df_sorted = df.sort_values('goods_id')
    
    # 对于每个goods_id，取最新日期的值
    for field in ['Reason', 'Video', 'Price']:
        if field in df.columns:
            # 初始化字段列
            if field not in df_mean.columns:
                df_mean[field] = None
            
            # 对于每个goods_id，取最新日期的值
            for goods_id in df_mean['goods_id']:
                goods_data = df_sorted[df_sorted['goods_id'] == goods_id]
                
                if len(goods_data) == 0:
                    # 没有数据，设置为None
                    df_mean.loc[df_mean['goods_id'] == goods_id, field] = None
                    continue
                
                # 取最新日期的值（第一条记录，因为已经按date_label降序排序）
                latest_val = goods_data.iloc[0][field]
                
                # 如果最新日期的值是空值，查找是否有其他非空值
                if pd.isna(latest_val):
                    # 查找该goods_id的所有非空值
                    non_null_data = goods_data[goods_data[field].notna()]
                    if len(non_null_data) > 0:
                        # 有非空值，取最新日期的非空值
                        latest_val = non_null_data.iloc[0][field]
                    else:
                        # 筛选后的数据中全部都是空值，如果提供了table_name，从数据库中查询该goods_id的所有数据
                        if table_name and field in ['Reason', 'Video', 'Price']:
                            try:
                                traffic_config, _, _, _ = get_db_config()
                                conn = get_db_connection(traffic_config)
                                try:
                                    cursor = conn.cursor()
                                    # 使用反引号包裹字段名，确保安全
                                    query = f"""
                                    SELECT `{field}`, date_label
                                    FROM `Vida_Traffic`.`{table_name}`
                                    WHERE goods_id = %s
                                      AND `{field}` IS NOT NULL
                                    ORDER BY date_label DESC
                                    LIMIT 1
                                    """
                                    cursor.execute(query, (goods_id,))
                                    result = cursor.fetchone()
                                    if result:
                                        latest_val = result[0]
                                    else:
                                        latest_val = None
                                finally:
                                    cursor.close()
                                    conn.close()
                            except Exception as e:
                                # 如果查询失败，保持为None
                                latest_val = None
                        else:
                            # 全部都是空值，返回None
                            latest_val = None
                
                # 更新df_mean中对应goods_id的值
                df_mean.loc[df_mean['goods_id'] == goods_id, field] = latest_val
    
    # 对数值字段保留适当的小数位数
    for col in numeric_columns:
        if col in df_mean.columns:
            df_mean[col] = df_mean[col].round(2)
    
    # 如果有排序字段，进行排序
    if sort_field and sort_field in df_mean.columns:
        ascending = (sort_order.lower() == 'asc')
        df_mean = df_mean.sort_values(by=sort_field, ascending=ascending)
    
    return df_mean


def data_filter(filters, sort_field=None, sort_order='asc', page=1, per_page=100, mean_mode=False, on_shelf_filter_mode=False):
    """
    数据筛选功能
    filters: dict，包含筛选条件
    sort_field: 排序字段
    sort_order: 'asc' 或 'desc'
    page: 页码
    per_page: 每页记录数
    mean_mode: 是否启用均值模式（按goods_id取均值）
    返回: {
        'success': bool,
        'data': dict or None,
        'error': str or None
    }
    """
    try:
        table_name = get_current_table()
        
        # 获取筛选后的数据（传递上架时间筛选模式参数）
        df = get_filtered_data(table_name, filters, sort_field, sort_order, on_shelf_filter_mode)
        
        # 如果启用均值模式，按goods_id分组计算均值
        if mean_mode and len(df) > 0:
            df = calculate_mean_by_goods_id(df, sort_field, sort_order, table_name)
        
        # 分页处理
        total = len(df)
        start = (page - 1) * per_page
        end = start + per_page
        df_page = df.iloc[start:end]
        
        # 转换为字典列表
        records = df_page.to_dict('records')
        
        # 处理NaN值、日期格式和其他特殊类型，确保JSON可序列化
        for record in records:
            for key, value in record.items():
                # 首先处理NaN值（使用pd.isna可以检测所有类型的NaN）
                if pd.isna(value):
                    record[key] = None
                # 处理日期格式
                elif key == 'date_label' and value is not None:
                    if isinstance(value, pd.Timestamp):
                        record[key] = value.strftime('%Y-%m-%d')
                    elif hasattr(value, 'strftime'):
                        try:
                            record[key] = value.strftime('%Y-%m-%d')
                        except:
                            record[key] = None
                # 处理numpy标量类型（转换为Python原生类型）
                elif hasattr(value, 'item') and not isinstance(value, (str, int, float, bool, type(None))):
                    try:
                        item_val = value.item()
                        # 再次检查是否为NaN
                        if pd.isna(item_val):
                            record[key] = None
                        else:
                            record[key] = item_val
                    except:
                        # 如果item()失败，尝试直接转换
                        try:
                            if pd.isna(value):
                                record[key] = None
                        except:
                            record[key] = None
        
        return {
            'success': True,
            'data': {
                'records': records,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
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


def export_filtered_data(filters, sort_field=None, sort_order='asc', export_format='csv', mean_mode=False, on_shelf_filter_mode=False):
    """
    导出筛选后的数据
    filters: dict，包含筛选条件
    sort_field: 排序字段
    sort_order: 'asc' 或 'desc'
    export_format: 'csv' 或 'excel'
    mean_mode: 是否启用均值模式（按goods_id取均值）
    返回: (file_data, filename, mime_type)
    """
    try:
        table_name = get_current_table()
        
        # 获取筛选后的数据（不分页，获取全部数据，传递上架时间筛选模式参数）
        df = get_filtered_data(table_name, filters, sort_field, sort_order, on_shelf_filter_mode)
        
        if len(df) == 0:
            return None, None, None
        
        # 如果启用均值模式，按goods_id分组计算均值
        if mean_mode:
            df = calculate_mean_by_goods_id(df, sort_field, sort_order, table_name)
        
        # 处理日期格式
        if 'date_label' in df.columns:
            df['date_label'] = pd.to_datetime(df['date_label'], errors='coerce')
            df['date_label'] = df['date_label'].dt.strftime('%Y-%m-%d')
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        table_suffix = table_name.replace('ROA1_', '')
        mode_suffix = ''
        if mean_mode and on_shelf_filter_mode:
            mode_suffix = '_均值_上架筛选'
        elif mean_mode:
            mode_suffix = '_均值'
        elif on_shelf_filter_mode:
            mode_suffix = '_上架筛选'
        
        if export_format == 'csv':
            # 导出为CSV
            output = io.StringIO()
            df.to_csv(output, index=False, encoding='utf-8-sig')  # utf-8-sig支持Excel正确显示中文
            file_data = output.getvalue().encode('utf-8-sig')
            filename = f'筛选数据{mode_suffix}_{table_suffix}_{timestamp}.csv'
            mime_type = 'text/csv; charset=utf-8'
            
        elif export_format == 'excel':
            # 导出为Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if mean_mode and on_shelf_filter_mode:
                    sheet_name = '筛选数据（均值+上架筛选）'
                elif mean_mode:
                    sheet_name = '筛选数据（均值）'
                elif on_shelf_filter_mode:
                    sheet_name = '筛选数据（上架筛选）'
                else:
                    sheet_name = '筛选数据'
                df.to_excel(writer, index=False, sheet_name=sheet_name)
            file_data = output.getvalue()
            filename = f'筛选数据{mode_suffix}_{table_suffix}_{timestamp}.xlsx'
            mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            raise ValueError(f'不支持的导出格式: {export_format}')
        
        return file_data, filename, mime_type
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e


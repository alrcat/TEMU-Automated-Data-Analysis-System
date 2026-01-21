# -*- coding: utf-8 -*-
"""
Flask主应用
"""

from flask import Flask, render_template, request, jsonify, session, send_file
from io import BytesIO
from config import (
    load_config, save_config, get_current_table, set_current_table,
    update_db_config, get_db_config
)
from db_utils import get_available_tables, get_db_connection
from function1_quick_search import quick_search
from function2_dynamic_management import dynamic_management
from function3_optimization import optimization_effect
from function4_manual_update import (
    manual_update_reason, manual_update_video, manual_update_price,
    get_available_dates
)
from function5_data_filter import data_filter
from function6_indicator_calculation import (
    indicator_calculation, configure_directories, get_indicator_config,
    save_indicator_data_to_excel
)
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 用于session


@app.route('/')
def index():
    """主页面"""
    current_table = get_current_table()
    return render_template('index.html', current_table=current_table)


@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """配置API"""
    if request.method == 'GET':
        config = load_config()
        return jsonify({
            'success': True,
            'data': config
        })
    else:
        # POST: 更新配置
        data = request.json
        traffic_db = data.get('traffic_db')
        sales_db = data.get('sales_db')
        pallet_db = data.get('pallet_db')
        product_db = data.get('product_db')

        if update_db_config(traffic_db, sales_db, pallet_db, product_db):
            return jsonify({
                'success': True,
                'message': '配置已保存'
            })
        else:
            return jsonify({
                'success': False,
                'error': '保存配置失败'
            }), 500


@app.route('/api/table', methods=['GET', 'POST'])
def api_table():
    """表选择API"""
    if request.method == 'GET':
        current_table = get_current_table()
        return jsonify({
            'success': True,
            'data': {
                'current_table': current_table
            }
        })
    else:
        # POST: 设置当前表
        data = request.json
        table_name = data.get('table_name', '').strip()
        
        if table_name:
            set_current_table(table_name)
            return jsonify({
                'success': True,
                'message': f'已切换到表: {table_name}'
            })
        else:
            return jsonify({
                'success': False,
                'error': '表名不能为空'
            }), 400


@app.route('/api/tables', methods=['GET'])
def api_tables():
    """获取可用表列表"""
    try:
        traffic_config, _, _, _ = get_db_config()
        conn = get_db_connection(traffic_config)
        cursor = conn.cursor()
        tables = get_available_tables(cursor)
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'tables': tables
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/function1/quick_search', methods=['POST'])
def api_function1():
    """功能1：快速查找"""
    data = request.json
    goods_id = data.get('goods_id', '').strip()
    
    if not goods_id:
        return jsonify({
            'success': False,
            'error': 'goods_id不能为空'
        }), 400
    
    try:
        goods_id = int(goods_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'goods_id必须是数字'
        }), 400
    
    result = quick_search(goods_id)
    return jsonify(result)


@app.route('/api/function2/dynamic_management', methods=['POST'])
def api_function2():
    """功能2：动销品管理"""
    data = request.json
    target_date = data.get('target_date')
    use_cache = data.get('use_cache', True)  # 默认使用缓存
    half_image_mode = data.get('half_image_mode', None)  # 图片渲染模式，默认为None（空列表）
    filter_mode = data.get('filter_mode', None)  # 过滤模式：None=不过滤, 字典格式：{'min': 最小值, 'max': 最大值或None}
    # 如果 filter_mode 是字典，验证格式
    if filter_mode is not None:
        if not isinstance(filter_mode, dict):
            filter_mode = None
        else:
            # 确保min和max是整数或None
            if 'min' in filter_mode:
                try:
                    filter_mode['min'] = int(filter_mode['min']) if filter_mode['min'] is not None else 0
                except (ValueError, TypeError):
                    filter_mode['min'] = 0
            else:
                filter_mode['min'] = 0
            
            if 'max' in filter_mode:
                try:
                    filter_mode['max'] = int(filter_mode['max']) if filter_mode['max'] is not None else None
                except (ValueError, TypeError):
                    filter_mode['max'] = None
            else:
                filter_mode['max'] = None
    
    result = dynamic_management(target_date, use_cache=use_cache, half_image_mode=half_image_mode, filter_mode=filter_mode)
    return jsonify(result)


@app.route('/api/function2/refresh_status', methods=['POST'])
def api_function2_refresh():
    """功能2：刷新status数据"""
    try:
        from config import get_current_table
        from function2_dynamic_management import refresh_status_data
        
        table_name = get_current_table()
        sales_table_name = f"{table_name}_Sales"
        
        success, message, updated_count, missing_dates_info = refresh_status_data(table_name, sales_table_name)
        
        return jsonify({
            'success': success,
            'message': message,
            'updated_count': updated_count,
            'missing_dates_info': missing_dates_info
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'刷新失败: {str(e)}',
            'updated_count': 0,
            'missing_dates_info': []
        }), 500


@app.route('/api/function2/quick_refresh_status', methods=['POST'])
def api_function2_quick_refresh():
    """功能2：快速刷新status数据（刷新所有动销品在昨天的数据）"""
    try:
        from config import get_current_table
        from function2_dynamic_management import quick_refresh_status_data
        
        table_name = get_current_table()
        sales_table_name = f"{table_name}_Sales"
        
        success, message, updated_count, missing_dates_info = quick_refresh_status_data(table_name, sales_table_name)
        
        return jsonify({
            'success': success,
            'message': message,
            'updated_count': updated_count,
            'missing_dates_info': missing_dates_info
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'快速刷新失败: {str(e)}',
            'updated_count': 0,
            'missing_dates_info': []
        }), 500


@app.route('/api/function2/export', methods=['POST'])
def api_function2_export():
    """功能2：导出动销品管理数据"""
    from flask import send_file
    from io import BytesIO
    
    data = request.json
    target_date = data.get('target_date')
    export_format = data.get('export_format', 'xlsx')  # 'csv' 或 'xlsx'
    status_filter = data.get('status_filter', 'all')  # '1', '2', 'all'
    date_range = data.get('date_range', 'single')  # 'single' 或 'all'
    selected_fields = data.get('selected_fields', None)  # 选中的字段列表
    
    try:
        from function2_dynamic_management import export_dynamic_management_data
        
        file_data, filename, mime_type = export_dynamic_management_data(
            target_date=target_date,
            export_format=export_format,
            status_filter=status_filter,
            date_range=date_range,
            selected_fields=selected_fields
        )
        
        if file_data is None:
            return jsonify({
                'success': False,
                'error': '没有数据可导出'
            }), 400
        
        file_buffer = BytesIO(file_data)
        return send_file(
            file_buffer,
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/function3/optimization', methods=['POST'])
def api_function3():
    """功能3：优化效果数据"""
    data = request.json
    field_name = data.get('field_name', 'Video')  # 'Video' 或 'Price'
    
    if field_name not in ['Video', 'Price']:
        return jsonify({
            'success': False,
            'error': 'field_name必须是Video或Price'
        }), 400
    
    result = optimization_effect(field_name)
    return jsonify(result)


@app.route('/api/function4/update_reason', methods=['POST'])
def api_function4_reason():
    """功能4：更新Reason"""
    data = request.json
    goods_id = data.get('goods_id')
    date_label = data.get('date_label')
    reason = data.get('reason', '').strip()
    
    if not goods_id or not date_label or not reason:
        return jsonify({
            'success': False,
            'error': 'goods_id、date_label和reason不能为空'
        }), 400
    
    try:
        goods_id = int(goods_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'goods_id必须是数字'
        }), 400
    
    result = manual_update_reason(goods_id, date_label, reason)
    return jsonify(result)


@app.route('/api/function4/update_video', methods=['POST'])
def api_function4_video():
    """功能4：更新Video"""
    data = request.json
    goods_id = data.get('goods_id')
    date_label = data.get('date_label')
    
    if not goods_id or not date_label:
        return jsonify({
            'success': False,
            'error': 'goods_id和date_label不能为空'
        }), 400
    
    try:
        goods_id = int(goods_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'goods_id必须是数字'
        }), 400
    
    result = manual_update_video(goods_id, date_label)
    return jsonify(result)


@app.route('/api/function4/update_price', methods=['POST'])
def api_function4_price():
    """功能4：更新Price"""
    data = request.json
    goods_id = data.get('goods_id')
    date_label = data.get('date_label')
    
    if not goods_id or not date_label:
        return jsonify({
            'success': False,
            'error': 'goods_id和date_label不能为空'
        }), 400
    
    try:
        goods_id = int(goods_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'goods_id必须是数字'
        }), 400
    
    result = manual_update_price(goods_id, date_label)
    return jsonify(result)


@app.route('/api/function4/available_dates', methods=['GET'])
def api_function4_dates():
    """功能4：获取可用日期列表"""
    goods_id = request.args.get('goods_id')
    
    if not goods_id:
        return jsonify({
            'success': False,
            'error': 'goods_id不能为空'
        }), 400
    
    try:
        goods_id = int(goods_id)
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'goods_id必须是数字'
        }), 400
    
    result = get_available_dates(goods_id)
    return jsonify(result)


@app.route('/api/function5/filter', methods=['POST'])
def api_function5():
    """功能5：数据筛选"""
    data = request.json
    filters = data.get('filters', {})
    sort_field = data.get('sort_field')
    sort_order = data.get('sort_order', 'asc')
    page = data.get('page', 1)
    per_page = data.get('per_page', 100)
    mean_mode = data.get('mean_mode', False)
    on_shelf_filter_mode = data.get('on_shelf_filter_mode', False)
    
    result = data_filter(filters, sort_field, sort_order, page, per_page, mean_mode, on_shelf_filter_mode)
    return jsonify(result)


@app.route('/api/function5/export', methods=['POST'])
def api_function5_export():
    """功能5：导出筛选数据"""
    try:
        data = request.json
        filters = data.get('filters', {})
        sort_field = data.get('sort_field')
        sort_order = data.get('sort_order', 'asc')
        export_format = data.get('export_format', 'csv')  # 'csv' 或 'excel'
        mean_mode = data.get('mean_mode', False)
        on_shelf_filter_mode = data.get('on_shelf_filter_mode', False)
        
        if export_format not in ['csv', 'excel']:
            return jsonify({
                'success': False,
                'error': '不支持的导出格式，请选择csv或excel'
            }), 400
        
        from function5_data_filter import export_filtered_data
        
        file_data, filename, mime_type = export_filtered_data(
            filters, sort_field, sort_order, export_format, mean_mode, on_shelf_filter_mode
        )
        
        if file_data is None:
            return jsonify({
                'success': False,
                'error': '没有数据可导出'
            }), 400
        
        # 返回文件
        return send_file(
            BytesIO(file_data),
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== 功能6：指标计算 =====

@app.route('/api/function6/indicators', methods=['GET', 'POST'])
def api_function6_indicators():
    """获取所有指标计算结果"""
    from flask import request
    target_date = None
    if request.method == 'POST':
        data = request.get_json() or {}
        target_date = data.get('target_date')
    return indicator_calculation(target_date=target_date)


@app.route('/api/function6/config', methods=['GET', 'POST'])
def api_function6_config():
    """指标计算配置管理"""
    if request.method == 'GET':
        return get_indicator_config()
    else:
        return configure_directories()


@app.route('/api/function6/save', methods=['POST'])
def api_function6_save():
    """保存指标数据到Excel"""
    from flask import request
    data = request.get_json() or {}
    target_date = data.get('target_date')
    return save_indicator_data_to_excel(target_date=target_date)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)


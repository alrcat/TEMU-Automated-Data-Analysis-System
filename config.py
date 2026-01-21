# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import json
import os

# 默认配置
DEFAULT_DB_CONFIG = {
    'host': '127.0.0.1',
    "port": 3306,
    'user': 'root',
    'password': 'txw@123',
    'database': 'Vida_Traffic',
    'charset': 'utf8mb4'
}

DEFAULT_SALES_DB_CONFIG = {
    'host': '127.0.0.1',
    "port": 3306,
    'user': 'root',
    'password': 'txw@123',
    'database': 'Vida_Sales',
    'charset': 'utf8mb4'
}

# 货盘数据库配置
DEFAULT_PALLET_DB_CONFIG = {
    'host': '192.168.31.101',
    'user': 'abc',
    'password': 'abc',
    'database': 'vidaxl',
    'charset': 'utf8mb4'
}

# 平台商品表数据库配置
DEFAULT_PRODUCT_DB_CONFIG = {
    'host': '192.168.31.101',
    'user': 'abc',
    'password': 'abc',
    'database': 'slkw',
    'charset': 'utf8mb4'
}



CONFIG_FILE = 'app_config.json'


def load_config():
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return get_default_config()
    else:
        return get_default_config()


def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False


def get_default_config():
    """获取默认配置"""
    return {
        'traffic_db': DEFAULT_DB_CONFIG.copy(),
        'sales_db': DEFAULT_SALES_DB_CONFIG.copy(),
        'pallet_db': DEFAULT_PALLET_DB_CONFIG.copy(),
        'product_db': DEFAULT_PRODUCT_DB_CONFIG.copy(),
        'current_table': 'ROA1_NL'
    }


def get_db_config():
    """获取数据库配置"""
    config = load_config()
    return (config.get('traffic_db', DEFAULT_DB_CONFIG),
            config.get('sales_db', DEFAULT_SALES_DB_CONFIG),
            config.get('pallet_db', DEFAULT_PALLET_DB_CONFIG),
            config.get('product_db', DEFAULT_PRODUCT_DB_CONFIG))


def get_current_table():
    """获取当前选择的表"""
    config = load_config()
    return config.get('current_table', 'ROA1_NL')


def set_current_table(table_name):
    """设置当前选择的表"""
    config = load_config()
    config['current_table'] = table_name
    save_config(config)


def update_db_config(traffic_db, sales_db, pallet_db=None, product_db=None):
    """更新数据库配置"""
    config = load_config()
    config['traffic_db'] = traffic_db
    config['sales_db'] = sales_db
    if pallet_db is not None:
        config['pallet_db'] = pallet_db
    if product_db is not None:
        config['product_db'] = product_db
    return save_config(config)


"""根据历史文件获取日期范围"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# 添加父目录到路径，以便导入父目录的模块
import sys
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from config import DOWNLOAD_PATHS

# 默认起始日期（当目录不存在或没有文件时使用）
DEFAULT_START_DATE = datetime(2025, 10, 1)


def get_europe_date_now() -> datetime:
    """
    获取欧洲时间的当前日期（北京时间减去7小时）
    
    Returns:
        欧洲时间的当前日期（时间部分为00:00:00）
    """
    # 获取当前北京时间，减去7小时得到欧洲时间
    europe_time = datetime.now() - timedelta(hours=7)
    # 只返回日期部分（时间设为00:00:00）
    return datetime(europe_time.year, europe_time.month, europe_time.day)


def get_date_range_from_history(country_code: str, base_path: Optional[str] = None, folder_suffix: str = "") -> List[datetime]:
    """
    根据国家代码查找历史导入目录，找到最新的Excel文件，生成日期范围列表
    
    Args:
        country_code: 国家代码（如"IT", "DE"等）
        base_path: 完整路径（精确到国家文件夹），如果为None则使用config中该国家的traffic路径
        folder_suffix: 已废弃，保留用于向后兼容
        
    Returns:
        日期范围列表，从最新文件日期的下一天到今天的前一天
        如果目录中没有文件，默认从2025.10.01开始
    """
    # 构建历史导入目录路径（路径已精确到国家文件夹）
    if base_path is None:
        # 使用traffic路径
        if country_code not in DOWNLOAD_PATHS:
            raise ValueError(f"国家代码 {country_code} 在 DOWNLOAD_PATHS 中未配置")
        base_path = Path(DOWNLOAD_PATHS[country_code]["traffic"])
    else:
        # base_path 已经是完整路径，直接使用
        base_path = Path(base_path)
    
    history_dir = base_path / "历史导入"
    
    print(f"\n正在查找历史导入目录: {history_dir}")
    
    # 检查目录是否存在
    if not history_dir.exists():
        print(f"⚠ 目录不存在: {history_dir}")
        # 使用默认起始日期
        start_date = DEFAULT_START_DATE
        end_date = get_europe_date_now() - timedelta(days=1)
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        print(f"✓ 使用默认起始日期 {DEFAULT_START_DATE.strftime('%Y-%m-%d')}，生成日期范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        return date_list
    
    # 查找所有Excel文件
    excel_files = list(history_dir.glob("*.xlsx"))
    
    if not excel_files:
        print(f"⚠ 历史导入目录中没有Excel文件")
        # 使用默认起始日期
        start_date = DEFAULT_START_DATE
        end_date = get_europe_date_now() - timedelta(days=1)
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        print(f"✓ 使用默认起始日期 {DEFAULT_START_DATE.strftime('%Y-%m-%d')}，生成日期范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}")
        return date_list
    
    # 从文件名中提取日期，找到最新的日期
    latest_date = None
    # 格式1: YYYY-MM-DD~YYYY-MM-DD (日期范围格式)
    date_range_pattern = re.compile(r'(\d{4})-(\d{2})-(\d{2})~(\d{4})-(\d{2})-(\d{2})')
    # 格式2: 国家代码_类型_YYYY-MM-DD (例如: IT_traffic_2025-12-04)
    single_date_pattern = re.compile(r'_(\d{4})-(\d{2})-(\d{2})(?:\.xlsx)?$')
    
    for file in excel_files:
        file_date = None
        
        # 先尝试匹配日期范围格式
        match_range = date_range_pattern.search(file.stem)
        if match_range:
            # 提取结束日期（第二个日期）
            year, month, day = int(match_range.group(4)), int(match_range.group(5)), int(match_range.group(6))
            file_date = datetime(year, month, day)
        else:
            # 尝试匹配单日期格式 (国家代码_类型_YYYY-MM-DD)
            match_single = single_date_pattern.search(file.stem)
            if match_single:
                year, month, day = int(match_single.group(1)), int(match_single.group(2)), int(match_single.group(3))
                file_date = datetime(year, month, day)
        
        # 更新最新日期
        if file_date and (latest_date is None or file_date > latest_date):
            latest_date = file_date
    
    if latest_date is None:
        print(f"⚠ 无法从文件名中提取日期")
        # 使用默认起始日期
        start_date = DEFAULT_START_DATE
    else:
        # 最新文件日期的下一天作为起始日期
        start_date = latest_date + timedelta(days=1)
        print(f"✓ 找到最新文件日期: {latest_date.strftime('%Y-%m-%d')}")
        print(f"✓ 起始日期（最早没有数据的日期）: {start_date.strftime('%Y-%m-%d')}")
    
    # 结束日期：今天的前一天（使用欧洲时间）
    end_date = get_europe_date_now() - timedelta(days=1)
    
    # 生成日期范围列表
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    
    print(f"✓ 生成日期范围: {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}，共 {len(date_list)} 天")
    
    return date_list

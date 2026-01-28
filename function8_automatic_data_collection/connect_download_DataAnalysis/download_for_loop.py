"""循环下载数据 - 根据日期范围循环下载 Traffic 或 Sales 数据"""

import random
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# 添加父目录到路径，以便导入父目录的模块
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from playwright.sync_api import Page

from config import DOWNLOAD_PATHS
from get_date_range_from_history import get_date_range_from_history


def click_today_button(page: Page) -> bool:
    """点击 Today 按钮"""
    try:
        time.sleep(random.uniform(0.5, 1.0))
        print("🔍 点击 Today 按钮...")
        today_btn = page.get_by_role("button", name="Today")
        today_btn.scroll_into_view_if_needed(timeout=3000)
        # 人类化操作：先hover，再点击
        try:
            today_btn.hover(timeout=1000)
            time.sleep(random.uniform(0.2, 0.4))
        except Exception:
            pass
        today_btn.click(timeout=5000, delay=random.randint(50, 150))
        time.sleep(random.uniform(0.8, 1.5))
        print("✓ 已点击 Today 按钮")
        return True
    except Exception as e:
        print(f"⚠ 点击 Today 按钮失败: {e}")
        return False


def select_date_in_calendar(page: Page, target_date: datetime, data_type: str = "traffic") -> bool:
    """
    在日期选择器中选择指定日期
    
    Args:
        page: Playwright的Page对象
        target_date: 目标日期
        data_type: 数据类型，"traffic" 或 "sales"，默认为 "traffic"
        
    Returns:
        如果选择成功返回True，否则返回False
    """
    try:
        # 点击日期选择器输入框
        time.sleep(random.uniform(0.3, 0.5))
        print(f"🔍 点击日期选择器输入框...")
        # Sales页面和Traffic页面都使用日期选择器，但Sales需要更精确的定位
        if data_type == "sales":
            # 对于Sales页面，使用filter筛选包含可见input的日期选择器
            date_picker = page.get_by_test_id("beast-core-datePicker-input").filter(has=page.locator("input:visible"))
            date_picker.first.wait_for(state="visible", timeout=5000)
            date_picker.first.scroll_into_view_if_needed(timeout=3000)
            try:
                date_picker.first.hover(timeout=1000)
                time.sleep(random.uniform(0.2, 0.4))
            except Exception:
                pass
            date_picker.first.click(timeout=5000, delay=random.randint(50, 150))
            time.sleep(random.uniform(0.8, 1.5))
            print("✓ 已打开日期选择器")
        else:
            date_input = page.get_by_test_id("beast-core-datePicker-htmlInput").first
            # 等待元素可见
            date_input.wait_for(state="visible", timeout=5000)
            date_input.scroll_into_view_if_needed(timeout=3000)
            # 人类化操作：先hover，再点击
            try:
                date_input.hover(timeout=1000)
                time.sleep(random.uniform(0.2, 0.4))
            except Exception:
                pass
            date_input.click(timeout=5000, delay=random.randint(50, 150))
            time.sleep(random.uniform(0.8, 1.5))
            print("✓ 已打开日期选择器")
        
        # 等待日期选择器面板出现
        time.sleep(random.uniform(0.5, 1.0))
        
        # 获取目标日期的月份（英文缩写）
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        target_month = month_names[target_date.month - 1]
        
        # 检查当前显示的月份是否匹配
        max_attempts = 12  # 最多尝试12次（一年）
        month_matched = False
        for attempt in range(max_attempts):
            try:
                # 获取当前显示的月份文本
                month_text_element = page.locator('.RPR_dateText_123')
                if month_text_element.is_visible(timeout=2000):
                    current_month_text = month_text_element.inner_text(timeout=2000).strip()
                    print(f"🔍 当前月份: {current_month_text}, 目标月份: {target_month}")
                    if current_month_text == target_month:
                        print(f"✓ 月份已匹配: {target_month}")
                        month_matched = True
                        break
                
                # 如果月份不匹配，点击左箭头切换到上一个月
                print(f"🔍 当前月份不匹配，点击左箭头切换到上一个月...")
                # 使用更精确的选择器：先定位到日期选择器的头部，再找左箭头
                # Sales和Traffic都使用datePicker，所以使用相同的header定位
                date_picker_header = page.get_by_test_id("beast-core-datePicker-dropdown-header").first
                prev_arrow = date_picker_header.get_by_test_id("beast-core-icon-left")
                prev_arrow.scroll_into_view_if_needed(timeout=3000)
                # 人类化操作：先hover，再点击
                try:
                    prev_arrow.hover(timeout=1000)
                    time.sleep(random.uniform(0.2, 0.4))
                except Exception:
                    pass
                prev_arrow.click(timeout=5000, delay=random.randint(50, 150))
                time.sleep(random.uniform(0.5, 0.8))
            except Exception as e:
                print(f"⚠ 切换月份时出错: {e}")
                if attempt < max_attempts - 1:
                    continue
                else:
                    return False
        
        if not month_matched:
            print(f"⚠ 无法切换到目标月份: {target_month}")
            return False
        
        # 点击对应的日期数字
        target_day = target_date.day
        try:
            print(f"🔍 点击日期: {target_day}号...")
            # 查找包含目标日期的单元格，使用 title 属性
            day_cell = page.locator(f'td[role="date-cell"] div[title="{target_day}"]').first
            day_cell.scroll_into_view_if_needed(timeout=3000)
            # 人类化操作：先hover，再点击
            try:
                day_cell.hover(timeout=1000)
                time.sleep(random.uniform(0.2, 0.4))
            except Exception:
                pass
            day_cell.click(timeout=5000, delay=random.randint(50, 150))
            time.sleep(random.uniform(0.5, 1.0))
            print(f"✓ 已选择日期: {target_date.strftime('%Y-%m-%d')}")
            return True
        except Exception as e:
            print(f"⚠ 点击日期失败: {e}")
            # 尝试另一种方式：通过文本内容查找
            try:
                day_cell = page.locator('td[role="date-cell"]').filter(has_text=f"^{target_day}$").first
                day_cell.scroll_into_view_if_needed(timeout=3000)
                # 人类化操作：先hover，再点击
                try:
                    day_cell.hover(timeout=1000)
                    time.sleep(random.uniform(0.2, 0.4))
                except Exception:
                    pass
                day_cell.click(timeout=5000, delay=random.randint(50, 150))
                time.sleep(random.uniform(0.5, 1.0))
                print(f"✓ 已选择日期: {target_date.strftime('%Y-%m-%d')}")
                return True
            except Exception as e2:
                print(f"⚠ 备用方式点击日期也失败: {e2}")
                return False
            
    except Exception as e:
        print(f"⚠ 选择日期失败: {e}")
        return False


def click_apply_button(page: Page) -> bool:
    """点击 Apply 按钮并等待页面加载完成"""
    try:
        time.sleep(random.uniform(0.3, 0.5))
        print("🔍 点击 Apply 按钮...")
        apply_btn = page.get_by_role("button", name="Apply")
        apply_btn.scroll_into_view_if_needed(timeout=3000)
        # 人类化操作：先hover，再点击
        try:
            apply_btn.hover(timeout=1000)
            time.sleep(random.uniform(0.2, 0.4))
        except Exception:
            pass
        apply_btn.click(timeout=5000, delay=random.randint(50, 150))
        print("✓ 已点击 Apply 按钮")
        
        # 随机等待，确保 Apply 生效
        print("⏳ 等待 Apply 生效...")
        time.sleep(random.uniform(1.5, 2.0))
        
        # 等待 DOM 加载完成
        try:
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            print("✓ DOM 加载完成")
        except Exception as e:
            print(f"⚠ DOM 加载超时: {e}")
        
        # 等待网络空闲
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
            print("✓ 网络空闲，页面加载完成")
        except Exception as e:
            print(f"⚠ 网络空闲等待超时: {e}")
        
        # 等待 Download 按钮出现
        try:
            print("⏳ 等待 Download 按钮出现...")
            download_btn = page.get_by_role("button", name="Download")
            download_btn.wait_for(state="visible", timeout=10000)
            print("✓ Download 按钮已出现")
        except Exception as e:
            print(f"⚠ 等待 Download 按钮超时: {e}")
        
        # 额外等待确保页面完全稳定
        time.sleep(random.uniform(0.5, 1.0))
        
        return True
    except Exception as e:
        print(f"⚠ 点击 Apply 按钮失败: {e}")
        return False


def download_file(page: Page, download_path: Path, country_code: str, date: datetime, data_type: str) -> bool:
    """
    点击 Download 按钮并等待文件下载
    
    Args:
        page: Playwright的Page对象
        download_path: 下载目录路径
        country_code: 国家代码
        date: 日期
        data_type: 数据类型（"traffic" 或 "sales"）
        
    Returns:
        如果下载成功返回True，否则返回False
    """
    try:
        # 确保下载目录存在
        download_path.mkdir(parents=True, exist_ok=True)
        
        # 点击 Download 按钮并等待下载
        time.sleep(random.uniform(0.3, 0.5))
        print("🔍 点击 Download 按钮...")
        
        # 增加超时时间到60秒
        with page.expect_download(timeout=60000) as download_info:
            download_btn = page.get_by_role("button", name="Download")
            download_btn.scroll_into_view_if_needed(timeout=3000)
            # 人类化操作：先hover，再点击
            try:
                download_btn.hover(timeout=1000)
                time.sleep(random.uniform(0.2, 0.4))
            except Exception:
                pass
            download_btn.click(timeout=5000, delay=random.randint(50, 150))
        
        download = download_info.value
        # 保存文件到指定目录
        date_str = date.strftime('%Y-%m-%d')
        file_name = f"{country_code}_{data_type}_{date_str}.xlsx"
        file_path = download_path / file_name
        
        download.save_as(file_path)
        print(f"✓ 文件已下载: {file_path}")
        time.sleep(random.uniform(1.0, 2.0))
        return True
        
    except Exception as e:
        print(f"⚠ 下载文件失败: {e}")
        return False


def download_for_loop(page: Page, country_code: str, data_type: str = "traffic") -> bool:
    """
    循环下载指定国家的数据
    
    流程说明：
    1. 获取需要下载的日期范围（从历史导入目录中查找最新文件）
    2. 对每个日期执行以下操作：
       - 点击 Today 按钮
       - 点击日期选择器输入框
       - 检查并切换月份（如果不对应则点击左箭头）
       - 点击对应的日期数字
       - 点击 Apply 按钮
       - 点击 Download 按钮并保存文件到指定目录
    
    Args:
        page: Playwright的Page对象
        country_code: 国家代码（如"IT", "DE"等）
        data_type: 数据类型，"traffic" 或 "sales"，默认为 "traffic"
        
    Returns:
        如果所有下载成功返回True，否则返回False
    """
    try:
        # ============== 循环下载流程开始 ==================
        print("\n" + "="*60)
        print(f"开始执行循环下载流程")
        print(f"国家: {country_code}, 数据类型: {data_type}")
        print("="*60)
        
        # 获取日期范围
        print(f"\n正在获取需要下载的日期范围...")
        
        # 根据 data_type 确定使用哪个路径来获取日期范围
        if data_type == "traffic":
            base_path = None  # 使用默认的 traffic 路径
        else:
            # 对于 sales，需要使用 sales 路径
            if country_code not in DOWNLOAD_PATHS:
                print(f"⚠ 国家代码 {country_code} 在 DOWNLOAD_PATHS 中未配置")
                return False
            base_path = Path(DOWNLOAD_PATHS[country_code]["sales"])
        
        date_range = get_date_range_from_history(country_code=country_code, base_path=base_path)
        
        if not date_range:
            print(f"⚠ 没有需要下载的日期")
            return False
        
        print(f"✓ 共需要下载 {len(date_range)} 天的数据")
        
        # 获取下载路径
        if country_code not in DOWNLOAD_PATHS:
            print(f"⚠ 国家代码 {country_code} 在 DOWNLOAD_PATHS 中未配置")
            return False
        
        download_path = Path(DOWNLOAD_PATHS[country_code][data_type])
        
        # 对每个日期进行循环下载
        success_count = 0
        fail_count = 0
        
        for idx, date in enumerate(date_range, 1):
            print(f"\n{'='*60}")
            print(f"处理第 {idx}/{len(date_range)} 个日期: {date.strftime('%Y-%m-%d')}")
            print(f"{'='*60}")
            
            # 1. 点击 Today 按钮
            if not click_today_button(page):
                print(f"⚠ 跳过日期 {date.strftime('%Y-%m-%d')}：无法点击 Today 按钮")
                fail_count += 1
                continue
            
            # 2. 选择日期
            if not select_date_in_calendar(page, date, data_type):
                print(f"⚠ 跳过日期 {date.strftime('%Y-%m-%d')}：无法选择日期")
                fail_count += 1
                continue
            
            # 3. 点击 Apply 按钮
            if not click_apply_button(page):
                print(f"⚠ 跳过日期 {date.strftime('%Y-%m-%d')}：无法点击 Apply 按钮")
                fail_count += 1
                continue
            
            # 4. 点击 Download 按钮并下载文件（带重试机制）
            max_download_retries = 3
            download_success = False
            
            for download_attempt in range(1, max_download_retries + 1):
                if download_attempt > 1:
                    print(f"\n🔄 第 {download_attempt}/{max_download_retries} 次重试下载日期 {date.strftime('%Y-%m-%d')}...")
                    # 重试时重新执行日期选择流程
                    if not click_today_button(page):
                        print(f"⚠ 重试时无法点击 Today 按钮")
                        continue
                    if not select_date_in_calendar(page, date, data_type):
                        print(f"⚠ 重试时无法选择日期")
                        continue
                    if not click_apply_button(page):
                        print(f"⚠ 重试时无法点击 Apply 按钮")
                        continue
                
                if download_file(page, download_path, country_code, date, data_type):
                    success_count += 1
                    print(f"✓ 日期 {date.strftime('%Y-%m-%d')} 下载成功")
                    download_success = True
                    break
                else:
                    if download_attempt < max_download_retries:
                        print(f"⚠ 第 {download_attempt} 次下载失败，准备重试...")
                        time.sleep(random.uniform(2.0, 3.0))
            
            if not download_success:
                fail_count += 1
                error_msg = f"日期 {date.strftime('%Y-%m-%d')} 下载失败，已重试 {max_download_retries} 次"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            # 每次下载后稍作延迟
            time.sleep(random.uniform(1.5, 2.5))
        
        print(f"\n{'='*60}")
        print(f"循环下载流程执行完成")
        print(f"成功: {success_count}, 失败: {fail_count}")
        print(f"{'='*60}\n")
        
        return fail_count == 0
        
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"⚠ 循环下载流程执行失败: {e}")
        print(f"{'='*60}\n")
        return False


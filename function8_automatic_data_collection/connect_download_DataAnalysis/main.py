"""连接紫鸟浏览器模板 - 已配置好连接，可直接在此文件中添加操作代码"""

import random
import time
import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

# 添加父目录到路径，以便导入父目录的模块
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

from playwright.sync_api import Page, Locator

from browser_connection import connect_to_matching_browser
from config import (
    SHOP_IDENTIFIERS,
    BROWSER_CONFIG,
    DATA_ANALYSIS,
)

# 从 select_country.py 导入国家选择函数
from select_country import select_country
# 从 get_date_range_from_history.py 导入日期范围函数
from get_date_range_from_history import get_date_range_from_history
# 从 download_for_loop.py 导入循环下载函数
from download_for_loop import download_for_loop


def main():
    """主函数 - 在此添加您的操作代码"""
    try:
        # 连接到匹配的店铺浏览器
        browser_info = connect_to_matching_browser(
            shop_identifiers='',
            #shop_identifiers=SHOP_IDENTIFIERS,
            port=BROWSER_CONFIG["port"],
            auto_scan=BROWSER_CONFIG["auto_scan"]
        )
        
        # 获取连接对象
        page = browser_info["page"]          # 已匹配的TEMU页面
        context = browser_info["context"]    # 浏览器上下文
        browser = browser_info["browser"]     # 浏览器对象
        playwright = browser_info["playwright"]  # Playwright实例
        
        # 注意：通过CDP连接的浏览器，Playwright的expect_download()会自动处理下载
        # 无需额外设置accept_downloads
        
        # 打印连接信息
        #print(f"\n店铺ID: {SHOP_CONFIG['shop_id']}")
        print(f"空白店铺id")
        print(f"当前页面URL: {page.url}")
        print(f"当前页面标题: {page.title()}")
        
        # =========================================================== #
        # 开始点击操作代码 - 循环处理所有国家
        # =========================================================== #
        
        # 记录开始时间
        start_time = time.time()
        
        # 根据 DATA_ANALYSIS 列表循环处理每个国家
        for country_idx, country_code in enumerate(DATA_ANALYSIS, 1):
            print(f"\n{'='*60}")
            print(f"开始处理第 {country_idx}/{len(DATA_ANALYSIS)} 个国家: {country_code}")
            print(f"{'='*60}\n")
            
            # 选择国家
            select_country(page, country_code)
            
            # ================== 进入分析页面 ==================
            # 检查 Product analytics 菜单项是否存在
            time.sleep(random.uniform(0.5, 1.0))
            product_analytics_exists = False
            try:
                # 查找包含 "Product analytics" 的菜单项
                menu_item = page.locator(
                    'li[data-testid="beast-core-menu-menuItem-li"]'
                ).filter(has_text="Product analytics")
                
                if menu_item.is_visible(timeout=2000):
                    product_analytics_exists = True
                    print("✓ Product analytics 菜单项已存在")
            except Exception:
                product_analytics_exists = False
            
            # 如果不存在，先点击 Analytics 菜单（重试3次）
            if not product_analytics_exists:
                max_retries = 3
                analytics_clicked = False
                for attempt in range(1, max_retries + 1):
                    try:
                        print(f"🔍 第 {attempt}/{max_retries} 次尝试：点击 Analytics 菜单...")
                        analytics_menu = page.get_by_test_id(
                            "beast-core-menu-subMenu-subMenuTitle"
                        ).get_by_text("Analytics")
                        analytics_menu.scroll_into_view_if_needed(timeout=3000)
                        # 人类化操作：先hover，再点击
                        try:
                            analytics_menu.hover(timeout=1000)
                            time.sleep(random.uniform(0.2, 0.4))
                        except Exception:
                            pass
                        analytics_menu.click(timeout=5000, delay=random.randint(50, 150))
                        time.sleep(random.uniform(0.8, 1.5))
                        print("✓ 已点击 Analytics 菜单")
                        analytics_clicked = True
                        break
                    except Exception as e:
                        print(f"⚠ 第 {attempt} 次尝试失败: {e}")
                        if attempt < max_retries:
                            time.sleep(random.uniform(1.0, 2.0))
                
                if not analytics_clicked:
                    raise Exception(f"点击 Analytics 菜单失败，已重试 {max_retries} 次")
            
            # 无论是否存在，都要点击 Product analytics 按钮（重试3次）
            max_retries = 3
            product_analytics_clicked = False
            for attempt in range(1, max_retries + 1):
                try:
                    time.sleep(random.uniform(0.5, 1.0))
                    print(f"🔍 第 {attempt}/{max_retries} 次尝试：点击 Product analytics 按钮...")
                    product_analytics_btn = page.locator(
                        'li[data-testid="beast-core-menu-menuItem-li"]'
                    ).filter(has_text="Product analytics")
                    product_analytics_btn.scroll_into_view_if_needed(timeout=3000)
                    # 人类化操作：先hover，再点击
                    try:
                        product_analytics_btn.hover(timeout=1000)
                        time.sleep(random.uniform(0.2, 0.4))
                    except Exception:
                        pass
                    product_analytics_btn.click(timeout=5000, delay=random.randint(50, 150))
                    time.sleep(random.uniform(0.8, 1.5))
                    print("✓ 已点击 Product analytics 按钮")
                    product_analytics_clicked = True
                    break
                except Exception as e:
                    print(f"⚠ 第 {attempt} 次尝试失败: {e}")
                    if attempt < max_retries:
                        time.sleep(random.uniform(1.0, 2.0))
            
            if not product_analytics_clicked:
                raise Exception(f"点击 Product analytics 按钮失败，已重试 {max_retries} 次")
            # ============================================

            # ==============点击Traffic标签================
           
            # 点击 Traffic 标签（重试3次）
            max_retries = 3
            traffic_clicked = False
            for attempt in range(1, max_retries + 1):
                try:
                    time.sleep(random.uniform(0.5, 1.0))
                    print(f"🔍 第 {attempt}/{max_retries} 次尝试：点击 Traffic 标签...")
                    traffic_tab = page.get_by_test_id("beast-core-tab-itemLabel-wrapper").get_by_text("Traffic")
                    traffic_tab.scroll_into_view_if_needed(timeout=3000)
                    try:
                        traffic_tab.hover(timeout=1000)
                        time.sleep(random.uniform(0.2, 0.4))
                    except Exception:
                        pass
                    traffic_tab.click(timeout=5000, delay=random.randint(50, 150))
                    time.sleep(random.uniform(0.5, 1.0))
                    print("✓ 已点击 Traffic 标签")
                    traffic_clicked = True
                    break
                except Exception as e:
                    print(f"⚠ 第 {attempt} 次尝试失败: {e}")
                    if attempt < max_retries:
                        time.sleep(random.uniform(1.0, 2.0))
            
            if not traffic_clicked:
                raise Exception(f"点击 Traffic 标签失败，已重试 {max_retries} 次")
            
            # ============== 循环下载 Traffic 数据 ==========
            download_for_loop(page, country_code=country_code, data_type="traffic")


            # ==============点击Sales标签===================
            
            # 点击 Sales 标签（重试3次）
            max_retries = 3
            sales_clicked = False
            for attempt in range(1, max_retries + 1):
                try:
                    time.sleep(random.uniform(0.5, 1.0))
                    print(f"🔍 第 {attempt}/{max_retries} 次尝试：点击 Sales 标签...")
                    sales_tab = page.get_by_test_id("beast-core-tab-itemLabel-wrapper").get_by_text("Sales")
                    sales_tab.scroll_into_view_if_needed(timeout=3000)
                    # 人类化操作：先hover，再点击
                    try:
                        sales_tab.hover(timeout=1000)
                        time.sleep(random.uniform(0.2, 0.4))
                    except Exception:
                        pass
                    sales_tab.click(timeout=5000, delay=random.randint(50, 150))
                    time.sleep(random.uniform(0.8, 1.5))
                    print("✓ 已点击 Sales 标签")
                    sales_clicked = True
                    break
                except Exception as e:
                    print(f"⚠ 第 {attempt} 次尝试失败: {e}")
                    if attempt < max_retries:
                        time.sleep(random.uniform(1.0, 2.0))
            
            if not sales_clicked:
                raise Exception(f"点击 Sales 标签失败，已重试 {max_retries} 次")

            
            # ============== 循环下载 Sales 数据 ===========
            download_for_loop(page, country_code=country_code, data_type="sales")
            
            print(f"\n{'='*60}")
            print(f"国家 {country_code} 处理完成")
            print(f"{'='*60}\n")
            
            # 每个国家处理完后稍作延迟
            if country_idx < len(DATA_ANALYSIS):
                time.sleep(random.uniform(1.5, 2.5))

        # 计算并打印总运行时间
        end_time = time.time()
        total_time = end_time - start_time
        hours = int(total_time // 3600)
        minutes = int((total_time % 3600) // 60)
        seconds = int(total_time % 60)
        
        print(f"\n{'='*60}")
        print("所有国家处理完成！")
        print(f"总运行时间: {hours}小时 {minutes}分钟 {seconds}秒 (共 {total_time:.2f} 秒)")
        print(f"{'='*60}")
        
        # =========================================================== #
        # 操作代码结束
        # =========================================================== #

    except Exception as e:
        error_msg = str(e)
        if "点击国家选择器失败" in error_msg:
            print(f"❌ 选择国家失败，程序停止: {e}")
            raise
        print(f"连接失败: {e}")

if __name__ == "__main__":
    main()


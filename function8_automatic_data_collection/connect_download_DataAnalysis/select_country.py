import random
import time
from playwright.sync_api import Page
# 参考肖老师
# 国家名称到国家编号的映射
COUNTRY_MAPPING = {
    "Italy": "IT",
    "Germany": "DE",
    "France": "FR",
    "Spain": "ES",
    "Netherlands": "NL",
    "Belgium": "BE",
    "Austria": "AT",
    "Czech Republic": "CZ",
    "Hungary": "HU",
    "Romania": "RO",
    "Sweden": "SE",
    "Portugal": "PT",
    "Denmark": "DK",
    "Poland": "PL",
    "Greece": "GR",
    "Slovakia": "SK",
    "Finland": "FI",
    "Norway": "NO",
    "Switzerland": "CH",
    "Estonia": "EE",
    "Latvia": "LV",
    "Lithuania": "LT",
    "Cuba": "CU",
}


def select_country(page: Page, country_code: str) -> bool:
    """
    选择指定国家
    
    根据国家编号（如"IT"）直接点击对应的"Marketplace in [国家名]"文本
    
    Args:
        page: Playwright的Page对象
        country_code: 国家编号（如"IT", "DE", "FR"等）
        
    Returns:
        如果选择成功返回True，否则返回False
    """
    # 根据国家编号查找对应的国家名称
    country_name = None
    for name, code in COUNTRY_MAPPING.items():
        if code.upper() == country_code.upper():
            country_name = name
            break
    
    if not country_name:
        print(f"⚠ 未找到国家编号 '{country_code}' 对应的国家名称")
        return False
    
    print(f"\n正在选择国家: {country_name} ({country_code})...")
    # ==========================================下拉菜单检查=======================================
    # 先检查下拉菜单是否已经出现
    dropdown_selectors = [
        "//div[@data-testid='beast-core-portal']",
        "//div[contains(@class, 'PT_popover_123')]",
        "//div[contains(text(), 'Country')]",
        "//div[contains(text(), 'Marketplace in')]",
        "//li[contains(text(), 'Marketplace in')]",
    ]
    dropdown_found = False
    for selector in dropdown_selectors:
        try:
            if page.locator(selector).first.is_visible(timeout=500):
                dropdown_found = True
                print("✓ 下拉菜单已存在，跳过点击国家选择器")
                break
        except:
            continue
    
    # ==========================================国家选择器=======================================
    # 如果下拉菜单未出现，才点击国家选择器
    if not dropdown_found:
        max_retries = 2
        button_clicked = False
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                # 使用 locator 查找包含 EN 文本的按钮
                country_button = page.locator('div[role="button"]').filter(has=page.locator('span', has_text="EN")).first
                country_button.scroll_into_view_if_needed(timeout=3000)
                # 人类化操作：先hover，再点击
                try:
                    country_button.hover(timeout=1000)
                    time.sleep(random.uniform(0.2, 0.4))
                except Exception:
                    pass
                country_button.click(timeout=5000, delay=random.randint(50, 150))
                time.sleep(random.uniform(0.5, 1.0))
                print(f"✓ 已点击国家选择器")
                button_clicked = True
                break
            except Exception as e:
                last_error = e
                error_msg = str(e)
                is_strict_mode_error = "strict mode violation" in error_msg.lower() or "resolved to" in error_msg.lower()
                if is_strict_mode_error:
                    print(f"⚠ 第 {attempt}/{max_retries} 次尝试：点击国家选择器失败（strict mode violation）: {e}")
                else:
                    print(f"⚠ 第 {attempt}/{max_retries} 次尝试：点击国家选择器失败: {e}")
                if attempt < max_retries:
                    time.sleep(random.uniform(1.0, 2.0))
        
        if not button_clicked:
            error_msg = f"点击国家选择器失败，已重试 {max_retries} 次。最后错误: {last_error}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        # 等待下拉菜单打开
        time.sleep(random.uniform(0.5, 1.0))
        
        # 等待下拉菜单出现
        dropdown_found = False
        for selector in dropdown_selectors:
            try:
                page.wait_for_selector(selector, timeout=2000, state="visible")
                dropdown_found = True
                break
            except:
                continue
        
        if not dropdown_found:
            time.sleep(1.0)
    # ========================================================================================
    # ==========================================目标国家=======================================
    # 直接点击目标国家选项
    try:
        # 等待下拉菜单完全展开
        time.sleep(random.uniform(0.7, 1.0))
        
        # 直接使用 get_by_text 点击对应的国家选项
        country_text = f"Marketplace in {country_name}"
        print(f"🔍 查找并点击: '{country_text}'")
        
        try:
            country_option = page.get_by_text(country_text)
            country_option.scroll_into_view_if_needed(timeout=3000)
            # 人类化操作：先hover，再点击
            try:
                country_option.hover(timeout=1000)
                time.sleep(random.uniform(0.2, 0.4))
            except Exception:
                pass
            country_option.click(timeout=5000, delay=random.randint(50, 150))
            
            print(f"✓ 已选择国家: {country_name} ({country_code})")
            
            # 点击后立即等待，确保点击生效
            print("⏳ 等待点击生效...")
            time.sleep(random.uniform(1.5, 2.0))
            
            # 等待页面加载完成
            print("⏳ 等待页面加载完成...")
            time.sleep(random.uniform(1.2, 1.8))
            
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
            
            # 额外等待确保页面完全加载
            time.sleep(random.uniform(0.8, 1.5))
            
            return True
            
        except Exception as e:
            print(f"⚠ 点击国家选项 '{country_text}' 失败: {e}")
            try:
                page.keyboard.press("Escape")
            except:
                pass
            return False

    except Exception as e:
        print(f"⚠ 选择国家失败: {e}")
    # ========================================================================================
        # 关闭下拉菜单
        try:
            page.keyboard.press("Escape")
        except:
            pass
        return False
    
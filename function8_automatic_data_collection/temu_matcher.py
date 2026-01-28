"""TEMU店铺匹配模块 - 垂直功能（店铺匹配验证）"""
#txw：注意需要提前打开对应的temu店铺
from __future__ import annotations

import re
from typing import List, Optional

from playwright.sync_api import Page


# txw:规范化文本，去除多余空白字符(connect_to_browser)
def normalize_text(value: str) -> str:
    """
    规范化文本，去除多余空白字符
    
    Args:
        value: 待处理的文本字符串
        
    Returns:
        规范化后的文本，多个连续空白字符被替换为单个空格，并去除首尾空白
    """
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


#txw:检查页面是否匹配指定店铺标识符(连接端口后的处理函数会用到)
def check_shop_match(page: Page, shop_identifiers: List[str]) -> bool:
    """
    检查页面是否匹配指定的店铺标识符
    
    通过多种策略验证页面是否匹配指定的店铺：
    1. 优先检查店铺ID（纯数字，长度≥10）是否在URL或页面内容中
    2. 检查店铺标识符是否出现在URL或页面标题中
    3. 如果搜索到TEMU页面但ID不匹配，会报告但不接受匹配
    
    Args:
        page: Playwright的Page对象，要检查的页面
        shop_identifiers: 店铺标识符列表，可以是店铺ID或其他标识符
        
    Returns:
        如果页面匹配店铺标识符返回True，否则返回False
        如果没有提供shop_identifiers，默认返回True
    """
    if not shop_identifiers:
        return True

    try:
        url = (page.url or "").lower() #txw:页面URL
        try:
            title = (page.title() or "").lower()
        except Exception:
            title = ""

        shop_id_found = False
        for identifier in shop_identifiers:
            if identifier.isdigit() and len(identifier) >= 10:
                shop_id_found = True
                if identifier in url:
                    print(f"  ✓ 匹配到店铺ID: {identifier} (在URL中)")#txw：策略1 - 在URL中查找店铺ID
                    return True
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=5000)
                    body_text = normalize_text(page.inner_text("body", timeout=3000))#txw：策略2 - 在页面内容中查找店铺ID,查找DOM内容是否有id
                    if identifier in body_text:
                        print(f"  ✓ 匹配到店铺ID: {identifier} (在页面内容中)")
                        return True
                except Exception:
                    pass

        for identifier in shop_identifiers:
            ident_lower = identifier.lower()
            if ident_lower in url or ident_lower in title:
                print(f"  ✓ 匹配到店铺标识: {identifier} (在URL/标题中)")
                return True

        return False
    except Exception as exc:
        print(f"  ⚠ 检查店铺匹配时出错: {exc}")
        return False


#txw:从页面列表中选择匹配的TEMU页面(连接端口后的处理函数会用到)
def select_temu_page(pages: List[Page], shop_identifiers: Optional[List[str]] = None, port: Optional[int] = None) -> Page:
    """
    从页面列表中选择匹配的TEMU页面
    
    优先选择匹配店铺标识符的TEMU页面，如果没有匹配的则选择第一个TEMU页面，
    如果都没有则选择第一个页面。
    
    Args:
        pages: 页面列表
        shop_identifiers: 店铺标识符列表，用于匹配页面
        
    Returns:
        选中的Page对象
        
    Raises:
        RuntimeError: 如果店铺ID不匹配，会抛出异常并报告搜索到TEMU页面但ID不匹配
    """
    selected_page = None
    temu_pages = []

    # 第一步：查找所有TEMU页面
    for page in pages:
        url = page.url or ""
        print(f"  发现页面: {url}")
        if "temu" in url.lower():
            temu_pages.append(page)
    
    # 第二步：如果有店铺标识符，尝试匹配
    if shop_identifiers and temu_pages:
        for idx, page in enumerate(temu_pages, 1):
            if check_shop_match(page, shop_identifiers): #txw:check_shop_match 检查页面是否匹配指定店铺标识符
                selected_page = page
                print(f"✅找到匹配的TEMU页面: {page.url}")
                break
            else:
                port_info = f"端口 {port} 的" if port is not None else ""
                page_info = f"第 {idx} 页面"
                shop_id = shop_identifiers[0] if shop_identifiers else "未知"
                prefix = f"{port_info}{page_info}" if port_info else page_info
                print(f"  {prefix}：\"{page.url}\"没有匹配店铺id：{shop_id} 跳过")
        
        # 如果未找到匹配的页面，报告搜索到TEMU页面但ID不匹配
        if selected_page is None:
            page_urls = [p.url for p in temu_pages]
            page_titles = []
            for p in temu_pages:
                try:
                    page_titles.append(p.title() or "")
                except Exception:
                    page_titles.append("")
            
            error_msg = (
                f"  ⚠️搜索到TEMU页面，但店铺ID不匹配\n"
                f"  ⚠️期望的店铺标识符: {shop_identifiers}\n"
                f"  ⚠️搜索到的TEMU页面:\n"
            )
            for i, (url, title) in enumerate(zip(page_urls, page_titles), 1):
                error_msg += f"    页面{i}: {url}\n"
                if title:
                    error_msg += f"      标题: {title}\n"
            error_msg += f"  提示: 请确保浏览器中打开的是正确的店铺页面"
            raise RuntimeError(error_msg)
    
    # 第三步：如果没有店铺标识符，选择第一个TEMU页面（没有提供店铺标识符的情况-容错机制）
    elif temu_pages:
        selected_page = temu_pages[0]
        print(f"✅选择第一个TEMU页面: {selected_page.url}")
    
    # 第四步：如果没有TEMU页面，选择第一个页面
    if selected_page is None:
        selected_page = pages[0]  # 如果没有找到匹配的页面，使用第一个标签页
        print(f"✅未找到TEMU页面，使用第一个页面: {selected_page.url}")
    ##############################################################
    # 第五步：检查页面URL是否包含seller-eu，如果不包含则抛出异常以便切换端口
    if selected_page:
        page_url = (selected_page.url or "").lower()
        if "seller-eu" not in page_url:
            port_info = f"端口 {port} 的" if port is not None else ""
            raise RuntimeError(
                f"  ⚠️{port_info}页面URL不包含seller-eu: {selected_page.url}\n"
                f"  提示: 将尝试其他端口连接"
            )
    ##############################################################
    return selected_page


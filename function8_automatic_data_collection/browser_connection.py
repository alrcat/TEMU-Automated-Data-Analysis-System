"""浏览器连接模块 - 通用连接功能（端口检测和CDP连接）"""

from __future__ import annotations

import re
import subprocess
from typing import Any, Dict, List, Optional

import requests
from playwright import sync_api
from playwright.sync_api import Browser, Playwright

# 导入TEMU匹配模块（可选，如果存在则使用）
try:
    from temu_matcher import select_temu_page
    TEMU_MATCHER_AVAILABLE = True
except ImportError:
    TEMU_MATCHER_AVAILABLE = False
    select_temu_page = None


# 尝试导入配置，如果不存在则使用默认值
try:
    from config import CDP_PORT_RANGES, COMMON_CDP_PORTS, BROWSER_CONFIG
    EXCLUDE_PORTS = BROWSER_CONFIG.get("exclude", [])
except ImportError:
    # 默认配置
    CDP_PORT_RANGES = [
        (50000, 51000),
        (60000, 61000),
        (60500, 60600),
        (65000, 66000),
        (9222, 9300),
    ]
    COMMON_CDP_PORTS = [
        60511, 60512, 60513, 65472, 65473, 9222, 9223, 9224,
        60000, 60001, 60510, 60514, 60515, 60520, 60521
    ]
    EXCLUDE_PORTS = []

# txw:自动扫描端口函数，返回所有监听端口(connect_to_browser)
def list_listening_ports(keywords: Optional[List[str]] = None, return_all: bool = False) -> List[int]:
    """
    动态检测紫鸟/Chrome进程的监听端口txw:！！！
    
    通过系统命令（Windows使用netstat/tasklist，macOS/Linux使用lsof）检测浏览器进程
    监听的端口，并过滤出可能的CDP端口范围。
    
    Args:
        keywords: 用于过滤进程的关键词列表，默认为["ziniaobro", "ziniao-ga", "ziniao", "chrome"]
        return_all: 如果为True，返回所有监听端口而不进行关键词过滤（用于调试）
        
    Returns:
        检测到的端口列表，优先返回CDP端口范围内的端口（50000-51000, 60000-61000等）
        如果范围内没有端口，会尝试验证范围外的端口是否为CDP端口（最多20个）
    """
    import platform

    keywords = keywords or ["ziniaobro", "ziniao-ga", "ziniao", "chrome"]
    ports: List[int] = []

    system = platform.system().lower()

    if system == "windows":
        try:
            # 方法1：使用PowerShell获取所有浏览器进程的PID（更可靠）
            browser_pids = set()
            try:
                ps_pid_cmd = (
                    "Get-Process | "
                    "Where-Object {$_.ProcessName -like '*ziniao*' -or $_.ProcessName -like '*chrome*'} | "
                    "Select-Object -ExpandProperty Id"
                )
                pid_output = subprocess.check_output(
                    ["powershell", "-Command", ps_pid_cmd],
                    text=True,
                    shell=True,
                )
                for line in pid_output.splitlines():
                    line = line.strip()
                    if line.isdigit():
                        browser_pids.add(int(line))
            except Exception:
                pass

            # 方法2：使用tasklist作为备用方法获取PID
            if not browser_pids:
                try:
                    tasklist_output = subprocess.check_output(
                        ["tasklist", "/FI", "IMAGENAME eq ziniaobro.exe", "/FO", "CSV"],
                        text=True,
                        shell=True,
                    )
                    for line in tasklist_output.splitlines()[1:]:
                        if "ziniaobro.exe" in line.lower():
                            parts = line.split('","')
                            if len(parts) >= 2:
                                try:
                                    pid = int(parts[1].strip('"'))
                                    browser_pids.add(pid)
                                except ValueError:
                                    pass
                except Exception:
                    pass

                try:
                    tasklist_output = subprocess.check_output(
                        ["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/FO", "CSV"],
                        text=True,
                        shell=True,
                    )
                    for line in tasklist_output.splitlines()[1:]:
                        if "chrome.exe" in line.lower():
                            parts = line.split('","')
                            if len(parts) >= 2:
                                try:
                                    pid = int(parts[1].strip('"'))
                                    browser_pids.add(pid)
                                except ValueError:
                                    pass
                except Exception:
                    pass

            # 方法3：使用PowerShell获取这些PID对应的所有监听端口（最可靠）
            if browser_pids or return_all:
                try:
                    if browser_pids:
                        ps_cmd = (
                            "Get-NetTCPConnection | "
                            "Where-Object {$_.State -eq 'Listen'} | "
                            "Select-Object LocalPort, OwningProcess | "
                            "Where-Object {$_.OwningProcess -in @(" + ",".join(map(str, browser_pids)) + ")} | "
                            "Select-Object -ExpandProperty LocalPort | "
                            "Sort-Object -Unique"
                        )
                    else:
                        ps_cmd = (
                            "Get-NetTCPConnection | "
                            "Where-Object {$_.State -eq 'Listen'} | "
                            "Select-Object -ExpandProperty LocalPort | "
                            "Sort-Object -Unique"
                        )
                    output = subprocess.check_output(
                        ["powershell", "-Command", ps_cmd],
                        text=True,
                        shell=True,
                    )
                    for line in output.splitlines():
                        line = line.strip()
                        if line.isdigit():
                            port = int(line)
                            if port not in ports:
                                ports.append(port)
                except Exception as e:
                    # 如果PowerShell失败，回退到netstat方法
                    try:
                        output = subprocess.check_output(
                            ["netstat", "-ano"],
                            text=True,
                            shell=True,
                        )
                        for line in output.splitlines():
                            if "LISTENING" in line.upper():
                                match = re.search(r":(\d+)\s+.*LISTENING\s+(\d+)", line, re.IGNORECASE)
                                if match:
                                    port = int(match.group(1))
                                    pid = int(match.group(2))
                                    if return_all or pid in browser_pids:
                                        if port not in ports:
                                            ports.append(port)
                    except Exception:
                        pass
            else:
                # 如果无法获取PID，使用netstat作为备用方法
                try:
                    output = subprocess.check_output(
                        ["netstat", "-ano"],
                        text=True,
                        shell=True,
                    )
                    for line in output.splitlines():
                        if "LISTENING" in line.upper():
                            match = re.search(r":(\d+)\s+.*LISTENING\s+(\d+)", line, re.IGNORECASE)
                            if match:
                                port = int(match.group(1))
                                pid = int(match.group(2))
                                if return_all or pid in browser_pids:
                                    if port not in ports:
                                        ports.append(port)
                except Exception:
                    pass
        except Exception as exc:
            print(f"⚠ Windows端口检测失败: {exc}")
            return []
    else:
        try:
            output = subprocess.check_output(
                ["lsof", "-iTCP", "-sTCP:LISTEN", "-n", "-P"],
                text=True,
            )
            for line in output.splitlines():
                lower_line = line.lower()
                if return_all or any(keyword in lower_line for keyword in keywords):
                    match = re.search(r":(\d+)\s+\(LISTEN\)", line)
                    if match:
                        port = int(match.group(1))
                        if port not in ports:
                            ports.append(port)
        except Exception as exc:
            print(f"⚠ 无法执行 lsof: {exc}")
            return []

    # 使用配置文件中的端口范围，如果没有配置文件则使用默认值
    cdp_port_ranges = CDP_PORT_RANGES

    # 添加调试信息：显示检测到的所有端口
    if ports:
        print(f"  🔍 检测到 {len(ports)} 个候选端口（过滤前）")
        # 显示前10个端口作为调试信息
        debug_ports = sorted(ports)[:10]
        print(f"  📋 示例端口: {debug_ports}")

    filtered_ports = []
    out_of_range_ports = []
    excluded_count = 0
    for port in ports:
        if port in EXCLUDE_PORTS:
            excluded_count += 1
            continue
        in_range = any(start <= port <= end for start, end in cdp_port_ranges)
        if in_range:
            filtered_ports.append(port)
        else:
            out_of_range_ports.append(port)
    
    if excluded_count > 0:
        print(f"  ℹ️  已排除 {excluded_count} 个端口（在EXCLUDE_PORTS中）")

    # 优先验证范围外的端口（紫鸟端口可能在范围外，如52937、64839、61989）
    # 即使范围内有端口，也优先验证范围外端口，因为紫鸟常用端口在范围外
    if out_of_range_ports:
        print(f"  检测到 {len(out_of_range_ports)} 个范围外的端口")
        if len(out_of_range_ports) <= 20:
            print(f"  验证所有范围外的端口是否为CDP端口...")
        else:
            print(f"  优先验证范围外的端口是否为CDP端口（最多验证20个）...")
        verified_ports = []
        for port in out_of_range_ports[:20]:
            if port in EXCLUDE_PORTS:  # 再次检查排除端口
                continue
            if is_cdp_port(port):
                verified_ports.append(port)
        if verified_ports:
            print(f"  ✓ 在范围外端口中找到 {len(verified_ports)} 个有效CDP端口")
            return verified_ports

    # 如果范围外没有找到，验证范围内的端口是否为有效的CDP端口
    if filtered_ports:
        # 再次过滤排除端口，确保不会返回
        filtered_ports = [p for p in filtered_ports if p not in EXCLUDE_PORTS]
        if filtered_ports:
            # 验证范围内的端口是否为有效的CDP端口（验证所有范围内的端口）
            print(f"  验证范围内的端口是否为CDP端口（验证 {len(filtered_ports)} 个）...")
            verified_filtered_ports = []
            for port in filtered_ports:
                if is_cdp_port(port):
                    verified_filtered_ports.append(port)
            if verified_filtered_ports:
                print(f"  ✓ 在范围内端口中找到 {len(verified_filtered_ports)} 个有效CDP端口")
                return verified_filtered_ports
            else:
                print(f"  ⚠️ 范围内的端口验证失败，没有找到有效的CDP端口")

    return []

# txw:检查端口是否暴露Chrome DevTools Protocol (CDP) 端点(connect_to_browser)
def is_cdp_port(port: int) -> bool:
    """
    检查端口是否暴露Chrome DevTools Protocol (CDP) 端点
    
    通过访问端口的 /json/version 端点来验证是否为有效的CDP端口。
    如果端口返回包含 webSocketDebuggerUrl 的JSON响应，则认为是有效的CDP端口。
    
    Args:
        port: 要检查的端口号
        
    Returns:
        如果端口是有效的CDP端口返回True，否则返回False
    """
    try:
        resp = requests.get(f"http://127.0.0.1:{port}/json/version", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("webSocketDebuggerUrl"):
                browser_desc = data.get("Browser") or data.get("Product") or "unknown"
                print(f"  端口 {port} 可用 (Browser: {browser_desc})")
                return True
    except Exception:
        pass
    return False

# txw:主函数
def connect_to_browser(
    port: Optional[int] = None,
    auto_scan: bool = True,
) -> Dict[str, object]:#txw！！！：（通用连接，不带店铺匹配）
    """
    连接到紫鸟浏览器并返回Playwright对象

    Args:
        port: 手动指定的端口号，如果为None则自动扫描
        auto_scan: 如果port为None，是否自动扫描端口

    Returns:
        包含以下键的字典:
        - playwright: Playwright实例
        - playwright_owned: 是否由本函数创建的Playwright实例
        - browser: Browser实例
        - context: BrowserContext实例
        - pages: 页面列表（所有打开的标签页）
    """
    created_playwright = False
    playwright = sync_api.sync_playwright().start()
    created_playwright = True

    try:
        if port is not None:
            print(f"正在连接指定端口: {port}")
            return _connect_to_port(playwright, port, created_playwright)#！！txw:连接到指定端口的内部函数

        if not auto_scan:
            raise RuntimeError("未指定端口且auto_scan=False")

        print("自动扫描可用端口...")
        detected_ports = []

        all_ports = list_listening_ports() #txw:自动扫描端口函数，返回所有监听端口
        if all_ports:
            print(f"🔍 动态检测到 {len(all_ports)} 个候选端口")
            # list_listening_ports已经验证过端口，直接使用
            detected_ports = all_ports

        # 如果正常检测失败，尝试使用return_all=True获取所有监听端口（备用机制）
        if not detected_ports:
            print("⚠️ 正常检测未找到端口，尝试备用检测方法...")
            all_listening_ports = list_listening_ports(return_all=True)
            if all_listening_ports:
                print(f"  备用检测找到 {len(all_listening_ports)} 个监听端口，开始验证...")
                # 过滤掉排除的端口
                candidate_ports = [p for p in all_listening_ports if p not in EXCLUDE_PORTS]
                # 优先验证范围外的端口（紫鸟常用端口在范围外）
                out_of_range = [p for p in candidate_ports if not any(start <= p <= end for start, end in CDP_PORT_RANGES)]
                if out_of_range:
                    print(f"  验证 {len(out_of_range[:30])} 个范围外的端口（最多30个）...")
                    for p in out_of_range[:30]:
                        if is_cdp_port(p):
                            detected_ports.append(p)
                            print(f"  ✓ 备用检测找到有效CDP端口: {p}")
                # 如果范围外没有找到，验证范围内的端口
                if not detected_ports:
                    in_range = [p for p in candidate_ports if any(start <= p <= end for start, end in CDP_PORT_RANGES)]
                    if in_range:
                        print(f"  验证 {len(in_range[:20])} 个范围内的端口（最多20个）...")
                        for p in in_range[:20]:
                            if is_cdp_port(p):
                                detected_ports.append(p)
                                print(f"  ✓ 备用检测找到有效CDP端口: {p}")

        if not detected_ports: #txw:如果未找到有效的CDP端口，则扫描常见端口范围
            print("扫描常见端口范围...")
            common_ports = COMMON_CDP_PORTS
            scan_ranges = CDP_PORT_RANGES
            # 先快速扫描常见端口
            print("  快速扫描常见CDP端口...")
            for p in common_ports:
                if p in EXCLUDE_PORTS:
                    continue
                if is_cdp_port(p):
                    detected_ports.append(p)
                    print(f"  ✓ 在常见端口中找到有效CDP端口: {p}")
            
            # 如果常见端口中没有找到，再扫描范围
            if not detected_ports:
                print("  扫描端口范围（每个范围只扫描第一个有效端口）...")
                for start, end in scan_ranges:
                    range_size = end - start + 1
                    if range_size > 100:
                        print(f"    扫描范围 {start}-{end}（范围较大，可能需要一些时间）...")
                    for p in range(start, end + 1):
                        if p in EXCLUDE_PORTS:
                            continue
                        if p in common_ports:
                            continue
                        if is_cdp_port(p):
                            detected_ports.append(p)
                            print(f"  ✓ 在范围 {start}-{end} 中找到有效CDP端口: {p}")
                            break

        if not detected_ports:
            raise RuntimeError("未找到任何可用的CDP端口。请确保紫鸟浏览器已打开并开启了远程调试功能")

        detected_ports = [p for p in detected_ports if p not in EXCLUDE_PORTS]
        print(f"尝试连接 {len(detected_ports)} 个端口...")
        for detected_port in detected_ports:
            try:
                return _connect_to_port(playwright, detected_port, created_playwright) #！！txw:连接到指定端口的内部函数
            except Exception as exc:
                print(f"  ⚠️端口 {detected_port} 连接失败: {exc}")
                continue

        raise RuntimeError("所有端口连接失败")

    except Exception:
        if created_playwright:
            playwright.stop()
        raise


# txw:连接到指定端口的内部函数(connect_to_browser)
def _connect_to_port(
    playwright: Playwright,
    port: int,
    created_playwright: bool,
) -> Dict[str, object]:
    """
    连接到指定端口的内部函数
    
    通过CDP协议连接到指定端口的浏览器，获取浏览器上下文和页面。
    
    Args:
        playwright: Playwright实例
        port: 要连接的CDP端口号
        created_playwright: 是否由外部创建的Playwright实例（用于资源清理）
        
    Returns:
        包含以下键的字典:
        - playwright: Playwright实例
        - playwright_owned: 是否由本函数创建的Playwright实例
        - browser: Browser实例
        - context: BrowserContext实例
        - pages: 页面列表（所有打开的标签页）
        
    Raises:
        RuntimeError: 如果未找到浏览器上下文或页面
    """
    target_url = f"http://127.0.0.1:{port}"

    # Playwright 的 Chromium 浏览器对象

    browser = playwright.chromium.connect_over_cdp(target_url, timeout=5000)#！！txw:通过CDP协议连接到指定端口的浏览器
    #获取浏览器中的所有上下文（BrowserContext）。

    contexts = browser.contexts #txw:浏览器上下文列表
    if not contexts:
        raise RuntimeError("  ⚠️未找到任何浏览器上下文")

    context = contexts[0]
    pages = context.pages
    if not pages:
        raise RuntimeError("  ⚠️未找到任何页面")

    print("✅第一部分成功：成功连接到浏览器") # txw:第一部分成功
    print(f"✓ 可用页面数: {len(pages)}")

    return {
        "playwright": playwright,
        "playwright_owned": created_playwright,
        "browser": browser,
        "context": context,
        "pages": pages,
    }


#txw:连接到匹配店铺的浏览器（如果第一个端口店铺检测失败，自动尝试多个端口）
def connect_to_matching_browser(   #txw！！！：（带店铺id的匹配连接）
    shop_identifiers: List[str],
    port: Optional[int] = None,
    auto_scan: bool = True,
) -> Dict[str, Any]:
    """
    连接到匹配指定店铺的浏览器，自动尝试多个端口
    
    如果当前端口连接的页面不匹配店铺ID，会自动尝试其他端口，
    因为可能打开了多个紫鸟店铺，每个店铺可能使用不同的端口。
    
    Args:
        shop_identifiers: 店铺标识符列表（如店铺ID），用于匹配页面
        port: 手动指定的端口号，如果为None则自动扫描所有端口
        auto_scan: 如果port为None，是否自动扫描端口
        
    Returns:
        包含以下键的字典:
        - playwright: Playwright实例
        - playwright_owned: 是否由本函数创建的Playwright实例
        - browser: Browser实例
        - context: BrowserContext实例
        - page: Page实例（已匹配到指定店铺的页面）
        
    Raises:
        RuntimeError: 如果所有端口都不匹配指定的店铺ID
    """
    if not TEMU_MATCHER_AVAILABLE or not select_temu_page:
        raise RuntimeError("temu_matcher模块不可用，无法进行店铺匹配")
    

    
    playwright = None
    created_playwright = False
    
    try:
        # 如果指定了端口，先尝试该端口
        browser_info = None
        if port is not None:
            try:
                browser_info = connect_to_browser(port=port, auto_scan=False)
                pages = browser_info["pages"]
                page = select_temu_page(pages, shop_identifiers, port=port)
                print(f"✅第二部分成功：端口 {port} 连接成功，店铺匹配")#端口匹配不同，但都连接和id验证成功
                return {
                    "playwright": browser_info["playwright"],
                    "playwright_owned": browser_info["playwright_owned"],
                    "browser": browser_info["browser"],
                    "context": browser_info["context"],
                    "page": page,
                }
            ##############################################################
            except RuntimeError as e:
                error_msg = str(e)
                if "店铺ID不匹配" in error_msg or "搜索到TEMU页面" in error_msg or "seller-eu" in error_msg:
                    if "seller-eu" in error_msg:
                        print(f"  ⚠️端口 {port} 的页面URL不包含seller-eu，尝试其他端口...")
                    else:
                        print("⚠️开始备用模式搜寻ID：重新查找匹配的TEMU页面，防止寻找到的店铺ID不匹配")
                        print(f"  ⚠️端口 {port} 连接的页面不匹配店铺ID，尝试其他端口...")#表示切换端口
            ##############################################################
                    # 关闭当前连接，释放资源
                    if browser_info and browser_info.get("playwright_owned") and browser_info.get("playwright"):
                        browser_info["playwright"].stop()
                else:
                    # 如果不是店铺ID不匹配的错误，关闭连接后重新抛出
                    if browser_info and browser_info.get("playwright_owned") and browser_info.get("playwright"):
                        browser_info["playwright"].stop()
                    raise
        
        # 获取所有可用端口
        print("扫描所有可用端口...")
        detected_ports = []
        
        all_ports = list_listening_ports()
        if all_ports:
            print(f"🔍 动态检测到 {len(all_ports)} 个候选端口")
            # list_listening_ports已经验证过端口，直接使用
            detected_ports = all_ports
        
        # 如果正常检测失败，尝试使用return_all=True获取所有监听端口（备用机制）
        if not detected_ports:
            print("⚠️ 正常检测未找到端口，尝试备用检测方法...")
            all_listening_ports = list_listening_ports(return_all=True)
            if all_listening_ports:
                print(f"  备用检测找到 {len(all_listening_ports)} 个监听端口，开始验证...")
                # 过滤掉排除的端口
                candidate_ports = [p for p in all_listening_ports if p not in EXCLUDE_PORTS]
                # 优先验证范围外的端口（紫鸟常用端口在范围外）
                out_of_range = [p for p in candidate_ports if not any(start <= p <= end for start, end in CDP_PORT_RANGES)]
                if out_of_range:
                    print(f"  验证 {len(out_of_range[:30])} 个范围外的端口（最多30个）...")
                    for p in out_of_range[:30]:
                        if is_cdp_port(p):
                            detected_ports.append(p)
                            print(f"  ✓ 备用检测找到有效CDP端口: {p}")
                # 如果范围外没有找到，验证范围内的端口
                if not detected_ports:
                    in_range = [p for p in candidate_ports if any(start <= p <= end for start, end in CDP_PORT_RANGES)]
                    if in_range:
                        print(f"  验证 {len(in_range[:20])} 个范围内的端口（最多20个）...")
                        for p in in_range[:20]:
                            if is_cdp_port(p):
                                detected_ports.append(p)
                                print(f"  ✓ 备用检测找到有效CDP端口: {p}")
        
        if not detected_ports:
            print("扫描常见端口范围...")
            common_ports = COMMON_CDP_PORTS
            scan_ranges = CDP_PORT_RANGES
            # 先快速扫描常见端口
            print("  快速扫描常见CDP端口...")
            for p in common_ports:
                if p in EXCLUDE_PORTS:
                    continue
                if is_cdp_port(p):
                    detected_ports.append(p)
                    print(f"  ✓ 在常见端口中找到有效CDP端口: {p}")
            
            # 如果常见端口中没有找到，再扫描范围
            if not detected_ports:
                print("  扫描端口范围（每个范围只扫描第一个有效端口）...")
                for start, end in scan_ranges:
                    range_size = end - start + 1
                    if range_size > 100:
                        print(f"    扫描范围 {start}-{end}（范围较大，可能需要一些时间）...")
                    for p in range(start, end + 1):
                        if p in EXCLUDE_PORTS:
                            continue
                        if p in common_ports:
                            continue
                        if is_cdp_port(p):
                            detected_ports.append(p)
                            print(f"  ✓ 在范围 {start}-{end} 中找到有效CDP端口: {p}")
                            break
        
        detected_ports = [p for p in detected_ports if p not in EXCLUDE_PORTS]
        
        # 如果指定了端口，将其移到列表最前面（优先尝试）
        if port is not None and port in detected_ports:
            detected_ports.remove(port)
            detected_ports.insert(0, port)
        
        if not detected_ports:
            raise RuntimeError("⚠️未找到任何可用的CDP端口。请确保紫鸟浏览器已打开并开启了远程调试功能")#紫鸟浏览器没打开
        
        print(f"尝试连接 {len(detected_ports)} 个端口，查找匹配的店铺...")
        
        # 依次尝试每个端口
        for detected_port in detected_ports:
            try:
                browser_info = connect_to_browser(port=detected_port, auto_scan=False)
                pages = browser_info["pages"]
                
                # 尝试选择匹配的页面
                try:
                    page = select_temu_page(pages, shop_identifiers, port=detected_port)
                    print(f"✅第二部分成功：端口 {detected_port} 连接成功，店铺匹配")#端口匹配不同，但都连接和id验证成功
                    return {
                        "playwright": browser_info["playwright"],
                        "playwright_owned": browser_info["playwright_owned"],
                        "browser": browser_info["browser"],
                        "context": browser_info["context"],
                        "page": page,
                    }
                except RuntimeError as e:
                    error_msg = str(e)
                    if "店铺ID不匹配" in error_msg or "搜索到TEMU页面" in error_msg or "seller-eu" in error_msg:
                        if "seller-eu" in error_msg:
                            print(f"  ⚠️端口 {detected_port} 的页面URL不包含seller-eu，继续尝试其他端口...")
                        else:
                            print(f"  ⚠️端口 {detected_port} 连接的页面不匹配店铺ID，继续尝试其他端口...")
                        # 关闭当前连接，释放资源
                        if browser_info.get("playwright_owned") and browser_info.get("playwright"):
                            browser_info["playwright"].stop()
                        continue
                    else:
                        raise
            except Exception as exc:
                error_msg = str(exc)
                if "店铺ID不匹配" in error_msg or "搜索到TEMU页面" in error_msg or "seller-eu" in error_msg:
                    if "seller-eu" in error_msg:
                        print(f"⚠️端口 {detected_port} 的页面URL不包含seller-eu: {error_msg}")
                    else:
                        print(f"⚠️端口 {detected_port} 连接的页面不匹配店铺ID: {error_msg}")
                    continue
                else:
                    print(f"⚠️端口 {detected_port} 连接失败: {exc}")
                    continue
        
        # 所有端口都尝试过了，都不匹配，尝试验证范围外的端口
        print(f"\n⚠️ 已尝试所有 {len(detected_ports)} 个端口，但都没有找到匹配的店铺页面")
        print("🔍 尝试验证范围外的端口是否为CDP端口...")
        
        # 重新获取所有监听端口（包括范围外的）
        all_listening_ports = list_listening_ports(return_all=True)
        if all_listening_ports:
            # 过滤掉已尝试的端口和排除的端口
            out_of_range_ports = [
                p for p in all_listening_ports 
                if p not in detected_ports 
                and p not in EXCLUDE_PORTS
                and not any(start <= p <= end for start, end in CDP_PORT_RANGES)
            ]
            
            if out_of_range_ports:
                print(f"  检测到 {len(out_of_range_ports)} 个范围外的端口，开始验证...")
                verified_ports = []
                for port in out_of_range_ports[:20]:  # 最多验证20个
                    if is_cdp_port(port):
                        verified_ports.append(port)
                        print(f"  ✓ 范围外端口 {port} 是有效的CDP端口")
                
                if verified_ports:
                    print(f"  找到 {len(verified_ports)} 个有效的范围外CDP端口，开始尝试连接...")
                    for verified_port in verified_ports:
                        try:
                            browser_info = connect_to_browser(port=verified_port, auto_scan=False)
                            pages = browser_info["pages"]
                            
                            try:
                                page = select_temu_page(pages, shop_identifiers, port=verified_port)
                                print(f"✅第二部分成功：范围外端口 {verified_port} 连接成功，店铺匹配")
                                return {
                                    "playwright": browser_info["playwright"],
                                    "playwright_owned": browser_info["playwright_owned"],
                                    "browser": browser_info["browser"],
                                    "context": browser_info["context"],
                                    "page": page,
                                }
                            except RuntimeError as e:
                                error_msg = str(e)
                                if "店铺ID不匹配" in error_msg or "搜索到TEMU页面" in error_msg or "seller-eu" in error_msg:
                                    if "seller-eu" in error_msg:
                                        print(f"  ⚠️范围外端口 {verified_port} 的页面URL不包含seller-eu，继续尝试...")
                                    else:
                                        print(f"  ⚠️范围外端口 {verified_port} 连接的页面不匹配店铺ID，继续尝试...")
                                    if browser_info.get("playwright_owned") and browser_info.get("playwright"):
                                        browser_info["playwright"].stop()
                                    continue
                                else:
                                    raise
                        except Exception as exc:
                            error_msg = str(exc)
                            if "店铺ID不匹配" in error_msg or "搜索到TEMU页面" in error_msg or "seller-eu" in error_msg:
                                print(f"  ⚠️范围外端口 {verified_port} 连接失败: {error_msg}")
                                continue
                            else:
                                print(f"  ⚠️范围外端口 {verified_port} 连接失败: {exc}")
                                continue
        
        # 所有端口都尝试过了，都不匹配
        raise RuntimeError(
            f"\n"
            f"⚠️提示: 请确保浏览器中打开了正确的店铺页面，或检查店铺ID是否正确\n"
            f"❌ 已尝试所有端口（包括范围外端口），但都没有找到匹配店铺ID {shop_identifiers} 的页面。"
        )
    
    except Exception:
        if created_playwright and playwright:
            playwright.stop()
        raise










"""
初始化：创建 Playwright 实例
端口检测：list_listening_ports() → 系统命令检测 → is_cdp_port() 验证
连接浏览器：_connect_to_port() → connect_over_cdp() → 获取 contexts 和 pages
店铺匹配（仅 connect_to_matching_browser）：select_temu_page() → check_shop_match()(不带店铺id：connect_to_browser函数)
错误处理：失败时关闭连接，尝试下一个端口

"""
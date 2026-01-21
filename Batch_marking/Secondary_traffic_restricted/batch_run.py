# -*- coding: utf-8 -*-
"""
批量运行所有国家的二级流量受限标记脚本
"""

import os
import sys
import subprocess
from datetime import datetime

def get_country_dirs(base_dir):
    """获取所有国家目录"""
    country_dirs = []
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path) and item.startswith('ROA1_'):
            add_file = os.path.join(item_path, 'add.py')
            if os.path.exists(add_file):
                country_dirs.append((item, item_path))
    return sorted(country_dirs)

def run_add_script(country_dir_path):
    """运行单个国家的add.py脚本"""
    add_file = os.path.join(country_dir_path, 'add.py')
    if not os.path.exists(add_file):
        return None, f"未找到add.py文件"
    
    try:
        result = subprocess.run(
            [sys.executable, add_file],
            cwd=country_dir_path,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode, result.stdout + result.stderr
    except Exception as e:
        return -1, f"运行出错: {str(e)}"

def main():
    """主函数"""
    base_dir = os.path.dirname(__file__)
    print("=" * 80)
    print("批量运行二级流量受限标记脚本")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    country_dirs = get_country_dirs(base_dir)
    
    if not country_dirs:
        print("未找到任何国家目录")
        return
    
    print(f"找到 {len(country_dirs)} 个国家目录:\n")
    for country_name, _ in country_dirs:
        print(f"  - {country_name}")
    print()
    
    results = []
    for country_name, country_dir_path in country_dirs:
        print("=" * 80)
        print(f"正在处理: {country_name}")
        print("=" * 80)
        
        returncode, output = run_add_script(country_dir_path)
        
        if returncode == 0:
            status = "✓ 成功"
        else:
            status = "✗ 失败"
        
        results.append({
            'country': country_name,
            'status': status,
            'returncode': returncode,
            'output': output
        })
        
        print(output)
        print()
    
    print("=" * 80)
    print("运行汇总")
    print("=" * 80)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    success_count = sum(1 for r in results if r['returncode'] == 0)
    fail_count = len(results) - success_count
    
    print(f"总计: {len(results)} 个国家")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个\n")
    
    print("详细结果:")
    for result in results:
        print(f"  {result['status']} - {result['country']}")
    
    if fail_count > 0:
        print("\n失败详情:")
        for result in results:
            if result['returncode'] != 0:
                print(f"\n{result['country']}:")
                print(result['output'])

if __name__ == '__main__':
    main()


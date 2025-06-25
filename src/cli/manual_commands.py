#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动操作命令处理模块

处理所有manual相关的命令
"""

import asyncio
from src.tools.manual_tools import ManualTools
from src.utils.text_utils import safe_print
from src.utils.logger import get_logger

logger = get_logger(__name__)


def manual_command(action: str, **kwargs) -> bool:
    """
    处理manual相关命令
    
    Args:
        action: 操作类型
        **kwargs: 其他参数
        
    Returns:
        操作是否成功
    """
    tools = ManualTools()
    
    if action == "collect":
        # 手动收集数据
        data_type = kwargs.get('data_type', 'all')
        dimension = kwargs.get('dimension', 'both')
        return tools.collect_data(data_type=data_type, dimension=dimension)
        
    elif action == "browser":
        # 打开浏览器
        page = kwargs.get('page', 'home')
        stay_open = kwargs.get('stay_open', True)
        return tools.open_browser(page=page, stay_open=stay_open)
        
    elif action == "export":
        # 导出数据
        format = kwargs.get('format', 'excel')
        output_dir = kwargs.get('output_dir')
        return tools.export_data(format=format, output_dir=output_dir)
        
    elif action == "analyze":
        # 分析趋势
        return tools.analyze_trends()
        
    elif action == "backup":
        # 备份数据
        include_cookies = kwargs.get('include_cookies', True)
        return tools.backup_data(include_cookies=include_cookies)
        
    elif action == "restore":
        # 恢复备份
        backup_path = kwargs.get('backup_path')
        if not backup_path:
            safe_print("❌ 请指定备份路径")
            return False
        return tools.restore_backup(backup_path=backup_path)
        
    else:
        safe_print(f"❌ 未知操作: {action}")
        safe_print("💡 可用操作: collect, browser, export, analyze, backup, restore")
        return False


def add_manual_parser(subparsers):
    """
    添加manual命令解析器
    
    Args:
        subparsers: argparse子解析器
    """
    manual_parser = subparsers.add_parser("manual", help="手动操作工具")
    manual_subparsers = manual_parser.add_subparsers(dest="manual_action", help="手动操作类型")
    
    # 数据收集命令
    collect_parser = manual_subparsers.add_parser("collect", help="手动收集数据")
    collect_parser.add_argument(
        "--type", 
        dest="data_type",
        choices=["dashboard", "content", "fans", "all"], 
        default="all",
        help="数据类型 (默认: all)"
    )
    collect_parser.add_argument(
        "--dimension", 
        choices=["7days", "30days", "both"], 
        default="both",
        help="时间维度 (默认: both)"
    )
    
    # 浏览器命令
    browser_parser = manual_subparsers.add_parser("browser", help="打开已登录的浏览器")
    browser_parser.add_argument(
        "--page", 
        choices=["home", "publish", "data", "fans", "content", "settings", "notes", "explore"],
        default="home",
        help="要打开的页面 (默认: home)"
    )
    browser_parser.add_argument(
        "--no-stay", 
        dest="stay_open",
        action="store_false",
        help="不保持浏览器打开"
    )
    
    # 导出命令
    export_parser = manual_subparsers.add_parser("export", help="导出数据")
    export_parser.add_argument(
        "--format", 
        choices=["excel", "json"], 
        default="excel",
        help="导出格式 (默认: excel)"
    )
    export_parser.add_argument(
        "--output", 
        dest="output_dir",
        help="输出目录"
    )
    
    # 分析命令
    manual_subparsers.add_parser("analyze", help="分析数据趋势")
    
    # 备份命令
    backup_parser = manual_subparsers.add_parser("backup", help="备份数据和cookies")
    backup_parser.add_argument(
        "--no-cookies", 
        dest="include_cookies",
        action="store_false",
        help="不包含cookies"
    )
    
    # 恢复命令
    restore_parser = manual_subparsers.add_parser("restore", help="恢复备份")
    restore_parser.add_argument(
        "backup_path",
        help="备份目录路径"
    )
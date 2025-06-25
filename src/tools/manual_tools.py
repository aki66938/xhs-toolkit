#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动操作工具集

提供各种手动操作的实用功能，包括数据收集、浏览器操作、数据导出等
"""

import os
import json
import time
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.core.config import XHSConfig
from src.core.browser import ChromeDriverManager
from src.auth.cookie_manager import CookieManager
# 数据收集函数会在需要时动态导入
from src.utils.logger import get_logger
from src.utils.text_utils import safe_print

logger = get_logger(__name__)


class ManualTools:
    """手动操作工具类"""
    
    def __init__(self):
        """初始化工具"""
        self.config = XHSConfig()
        self.cookie_manager = CookieManager(self.config)
        self.browser_manager = None
        
    def collect_data(self, data_type: str = "all", dimension: str = "both") -> bool:
        """
        手动收集数据
        
        Args:
            data_type: 数据类型 (dashboard/content/fans/all)
            dimension: 时间维度 (7days/30days/both)
            
        Returns:
            是否成功
        """
        safe_print(f"📊 开始手动收集数据: {data_type}")
        
        try:
            # 验证cookies
            if not self.cookie_manager.validate_cookies():
                safe_print("❌ Cookies验证失败，请先获取有效的Cookies")
                safe_print("💡 运行: python xhs_toolkit.py cookie save")
                return False
            
            # 初始化浏览器
            self.browser_manager = ChromeDriverManager(self.config)
            driver = self.browser_manager.create_driver()
            cookies = self.cookie_manager.load_cookies()
            
            # 加载cookies到浏览器
            driver.get("https://www.xiaohongshu.com")
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"添加cookie失败: {e}")
            
            # 根据数据类型收集
            collectors = []
            if data_type in ["dashboard", "all"]:
                from src.xiaohongshu.data_collector.dashboard import collect_dashboard_data
                collectors.append(("Dashboard", lambda dim: collect_dashboard_data(driver, save_data=True)))
            if data_type in ["content", "all"]:
                from src.xiaohongshu.data_collector.content_analysis import collect_content_analysis_data
                collectors.append(("Content", lambda dim: collect_content_analysis_data(driver, save_data=True)))
            if data_type in ["fans", "all"]:
                from src.xiaohongshu.data_collector.fans import collect_fans_data
                collectors.append(("Fans", lambda dim: collect_fans_data(driver, save_data=True)))
            
            if not collectors:
                safe_print(f"❌ 未知的数据类型: {data_type}")
                safe_print("💡 可用类型: dashboard, content, fans, all")
                return False
            
            # 确定时间维度
            dimensions = []
            if dimension in ["7days", "both"]:
                dimensions.append("7days")
            if dimension in ["30days", "both"]:
                dimensions.append("30days")
            
            if not dimensions:
                safe_print(f"❌ 未知的时间维度: {dimension}")
                safe_print("💡 可用维度: 7days, 30days, both")
                return False
            
            # 收集数据
            success_count = 0
            total_count = len(collectors)
            
            for name, collect_func in collectors:
                safe_print(f"\n📈 收集{name}数据...")
                try:
                    # 这里的collect_func已经包含了dimension参数
                    data = collect_func(None)  # 数据收集函数会自己处理维度
                    if data:
                        safe_print(f"  ✅ {name}数据收集成功")
                        success_count += 1
                    else:
                        safe_print(f"  ⚠️ {name}数据为空")
                except Exception as e:
                    safe_print(f"  ❌ {name}数据收集失败: {e}")
                    logger.exception(f"收集{name}数据失败")
            
            safe_print(f"\n📊 数据收集完成: {success_count}/{total_count} 成功")
            return success_count > 0
            
        except Exception as e:
            safe_print(f"❌ 数据收集失败: {e}")
            logger.exception("数据收集异常")
            return False
        finally:
            if self.browser_manager:
                self.browser_manager.close_driver()
    
    def open_browser(self, page: str = "home", stay_open: bool = True) -> bool:
        """
        打开已登录的浏览器页面
        
        Args:
            page: 页面类型 (home/publish/data/fans/content/settings)
            stay_open: 是否保持浏览器打开
            
        Returns:
            是否成功
        """
        safe_print(f"🌐 打开浏览器页面: {page}")
        
        # 页面URL映射
        page_urls = {
            "home": "https://creator.xiaohongshu.com/new/home",
            "publish": "https://creator.xiaohongshu.com/publish/publish",
            "data": "https://creator.xiaohongshu.com/statistics/data-analysis",
            "fans": "https://creator.xiaohongshu.com/creator/fans",
            "content": "https://creator.xiaohongshu.com/creator/content",
            "settings": "https://creator.xiaohongshu.com/settings/profile",
            "notes": "https://www.xiaohongshu.com/user/profile",
            "explore": "https://www.xiaohongshu.com/explore"
        }
        
        try:
            # 验证cookies
            if not self.cookie_manager.validate_cookies():
                safe_print("❌ Cookies验证失败，请先获取有效的Cookies")
                safe_print("💡 运行: python xhs_toolkit.py cookie save")
                return False
            
            # 获取页面URL
            url = page_urls.get(page)
            if not url:
                safe_print(f"❌ 未知的页面类型: {page}")
                safe_print(f"💡 可用页面: {', '.join(page_urls.keys())}")
                return False
            
            # 初始化浏览器
            self.browser_manager = ChromeDriverManager(self.config)
            
            # 创建浏览器并加载cookies
            driver = self.browser_manager.create_driver()
            cookies = self.cookie_manager.load_cookies()
            
            # 先访问主站点设置cookies
            driver.get("https://www.xiaohongshu.com")
            time.sleep(2)
            
            # 添加cookies
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"添加cookie失败: {e}")
            
            # 访问目标页面
            safe_print(f"🔗 访问页面: {url}")
            driver.get(url)
            
            safe_print(f"✅ 已打开{page}页面")
            
            if stay_open:
                safe_print("💡 浏览器将保持打开状态，按Ctrl+C关闭")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    safe_print("\n👋 关闭浏览器")
            
            return True
            
        except Exception as e:
            safe_print(f"❌ 打开浏览器失败: {e}")
            logger.exception("打开浏览器异常")
            return False
        finally:
            if not stay_open and self.browser_manager:
                self.browser_manager.close_driver()
    
    def export_data(self, format: str = "excel", output_dir: Optional[str] = None) -> bool:
        """
        导出数据到指定格式
        
        Args:
            format: 导出格式 (excel/json)
            output_dir: 输出目录
            
        Returns:
            是否成功
        """
        safe_print(f"📤 导出数据为{format}格式")
        
        try:
            # 确定数据目录
            data_dir = Path(self.config.data_path) / "creator_db"
            if not data_dir.exists():
                safe_print("❌ 未找到数据文件，请先收集数据")
                return False
            
            # 确定输出目录
            if output_dir:
                output_path = Path(output_dir)
            else:
                output_path = Path.cwd() / "exports"
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 时间戳
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format == "excel":
                # 创建Excel文件
                excel_file = output_path / f"xhs_data_{timestamp}.xlsx"
                with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                    # 导出各类数据
                    data_files = {
                        "Dashboard": data_dir / "dashboard_data.csv",
                        "Content": data_dir / "content_analysis_data.csv",
                        "Fans": data_dir / "fans_data.csv"
                    }
                    
                    exported_sheets = []
                    for sheet_name, csv_file in data_files.items():
                        if csv_file.exists():
                            df = pd.read_csv(csv_file)
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                            exported_sheets.append(sheet_name)
                            safe_print(f"  ✅ 导出{sheet_name}数据")
                    
                    if exported_sheets:
                        safe_print(f"\n✅ 数据已导出到: {excel_file}")
                        return True
                    else:
                        safe_print("❌ 没有找到可导出的数据")
                        return False
            
            elif format == "json":
                # 导出为JSON格式
                json_dir = output_path / f"xhs_data_{timestamp}"
                json_dir.mkdir(exist_ok=True)
                
                data_files = {
                    "dashboard": data_dir / "dashboard_data.csv",
                    "content": data_dir / "content_analysis_data.csv",
                    "fans": data_dir / "fans_data.csv"
                }
                
                exported_files = []
                for name, csv_file in data_files.items():
                    if csv_file.exists():
                        df = pd.read_csv(csv_file)
                        json_file = json_dir / f"{name}.json"
                        df.to_json(json_file, orient='records', force_ascii=False, indent=2)
                        exported_files.append(name)
                        safe_print(f"  ✅ 导出{name}数据")
                
                if exported_files:
                    safe_print(f"\n✅ 数据已导出到: {json_dir}")
                    return True
                else:
                    safe_print("❌ 没有找到可导出的数据")
                    return False
            
            else:
                safe_print(f"❌ 不支持的格式: {format}")
                safe_print("💡 支持的格式: excel, json")
                return False
                
        except Exception as e:
            safe_print(f"❌ 导出数据失败: {e}")
            logger.exception("导出数据异常")
            return False
    
    def analyze_trends(self) -> bool:
        """
        分析数据趋势
        
        Returns:
            是否成功
        """
        safe_print("📈 分析数据趋势")
        
        try:
            # 读取数据
            data_dir = Path(self.config.data_path) / "creator_db"
            
            # Dashboard数据分析
            dashboard_file = data_dir / "dashboard_data.csv"
            if dashboard_file.exists():
                safe_print("\n📊 Dashboard数据分析:")
                df = pd.read_csv(dashboard_file)
                if not df.empty:
                    latest = df.iloc[-1]
                    safe_print(f"  最新数据时间: {latest['采集时间']}")
                    safe_print(f"  时间维度: {latest['时间维度']}")
                    safe_print(f"  总浏览量: {latest['浏览']}")
                    safe_print(f"  总点赞量: {latest['点赞']}")
                    safe_print(f"  互动率: {latest['互动']}")
                    
                    # 计算趋势
                    if len(df) > 1:
                        prev = df.iloc[-2]
                        view_change = int(latest['浏览']) - int(prev['浏览'])
                        like_change = int(latest['点赞']) - int(prev['点赞'])
                        safe_print(f"  浏览量变化: {'+' if view_change >= 0 else ''}{view_change}")
                        safe_print(f"  点赞量变化: {'+' if like_change >= 0 else ''}{like_change}")
            
            # 粉丝数据分析
            fans_file = data_dir / "fans_data.csv"
            if fans_file.exists():
                safe_print("\n👥 粉丝数据分析:")
                df = pd.read_csv(fans_file)
                if not df.empty:
                    latest = df.iloc[-1]
                    safe_print(f"  总粉丝数: {latest['总粉丝数']}")
                    safe_print(f"  新增粉丝: {latest['新增粉丝']}")
                    safe_print(f"  流失粉丝: {latest['流失粉丝']}")
                    safe_print(f"  净增长: {int(latest['新增粉丝']) - int(latest['流失粉丝'])}")
            
            # 内容数据分析
            content_file = data_dir / "content_analysis_data.csv"
            if content_file.exists():
                safe_print("\n📝 内容数据分析:")
                df = pd.read_csv(content_file)
                if not df.empty:
                    safe_print(f"  总笔记数: {len(df)}")
                    safe_print(f"  平均浏览量: {df['浏览'].astype(int).mean():.0f}")
                    safe_print(f"  平均点赞量: {df['点赞'].astype(int).mean():.0f}")
                    
                    # 找出表现最好的笔记
                    best_note = df.loc[df['浏览'].astype(int).idxmax()]
                    safe_print(f"\n  🏆 表现最佳笔记:")
                    safe_print(f"    标题: {best_note['标题']}")
                    safe_print(f"    浏览: {best_note['浏览']}")
                    safe_print(f"    点赞: {best_note['点赞']}")
            
            return True
            
        except Exception as e:
            safe_print(f"❌ 分析数据失败: {e}")
            logger.exception("分析数据异常")
            return False
    
    def backup_data(self, include_cookies: bool = True) -> bool:
        """
        备份数据和cookies
        
        Args:
            include_cookies: 是否包含cookies
            
        Returns:
            是否成功
        """
        safe_print("💾 开始备份数据")
        
        try:
            # 创建备份目录
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path.cwd() / "backups" / f"backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 备份数据文件
            data_dir = Path(self.config.data_path) / "creator_db"
            if data_dir.exists():
                import shutil
                backup_data_dir = backup_dir / "data"
                shutil.copytree(data_dir, backup_data_dir)
                safe_print(f"✅ 数据文件已备份")
            
            # 备份cookies
            if include_cookies:
                cookies = self.cookie_manager.load_cookies()
                if cookies:
                    cookies_file = backup_dir / "cookies.json"
                    with open(cookies_file, 'w', encoding='utf-8') as f:
                        json.dump(cookies, f, ensure_ascii=False, indent=2)
                    safe_print(f"✅ Cookies已备份")
            
            # 备份配置信息
            config_info = {
                "backup_time": timestamp,
                "version": self.config.version,
                "config": self.config.to_dict()
            }
            config_file = backup_dir / "config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_info, f, ensure_ascii=False, indent=2)
            
            safe_print(f"\n✅ 备份完成: {backup_dir}")
            return True
            
        except Exception as e:
            safe_print(f"❌ 备份失败: {e}")
            logger.exception("备份数据异常")
            return False
    
    def restore_backup(self, backup_path: str) -> bool:
        """
        恢复备份
        
        Args:
            backup_path: 备份目录路径
            
        Returns:
            是否成功
        """
        safe_print(f"📂 恢复备份: {backup_path}")
        
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists():
                safe_print(f"❌ 备份目录不存在: {backup_path}")
                return False
            
            # 恢复数据文件
            backup_data_dir = backup_dir / "data"
            if backup_data_dir.exists():
                import shutil
                data_dir = Path(self.config.data_path) / "creator_db"
                if data_dir.exists():
                    shutil.rmtree(data_dir)
                shutil.copytree(backup_data_dir, data_dir)
                safe_print("✅ 数据文件已恢复")
            
            # 恢复cookies
            cookies_file = backup_dir / "cookies.json"
            if cookies_file.exists():
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                self.cookie_manager.save_cookies(cookies)
                safe_print("✅ Cookies已恢复")
            
            safe_print("\n✅ 备份恢复完成")
            return True
            
        except Exception as e:
            safe_print(f"❌ 恢复备份失败: {e}")
            logger.exception("恢复备份异常")
            return False
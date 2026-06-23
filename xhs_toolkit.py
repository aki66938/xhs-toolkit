#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书MCP工具包 - 统一入口

集成cookie管理和MCP服务器功能的统一工具
"""

import os
import sys
import argparse
import json
import time
import asyncio
from pathlib import Path


# 导入重构后的模块
from src.core.config import XHSConfig
from src.core.exceptions import XHSToolkitError, format_error_message
from src.auth.cookie_manager import CookieManager
from src.server.mcp_server import MCPServer
from src.xiaohongshu.client import XHSClient
from src.xiaohongshu.models import XHSNote
from src.utils.logger import setup_logger, get_logger
from src.utils.text_utils import safe_print
from src.cli.manual_commands import manual_command, add_manual_parser

logger = get_logger(__name__)

def print_banner():
    """打印工具横幅"""
    from src import __version__
    banner = f"""
╭─────────────────────────────────────────╮
│           小红书MCP工具包               │
│     Xiaohongshu MCP Toolkit v{__version__}      │
╰─────────────────────────────────────────╯
"""
    try:
        print(banner)
    except UnicodeEncodeError:
        # Windows GBK编码兼容性处理
        simple_banner = f"""
==========================================
          小红书MCP工具包
    Xiaohongshu MCP Toolkit v{__version__}
==========================================
"""
        print(simple_banner)

def cookie_command(action: str) -> bool:
    """
    处理cookie相关命令
    
    Args:
        action: 操作类型 (save, show, validate, test)
        
    Returns:
        操作是否成功
    """
    safe_print(f"🍪 执行Cookie操作: {action}")
    
    try:
        # 初始化配置和cookie管理器
        config = XHSConfig()
        cookie_manager = CookieManager(config)
        
        if action == "save":
            safe_print("📝 注意：新版本直接获取创作者中心权限cookies")
            safe_print("🔧 这将解决跳转到创作者中心时cookies失效的问题")
            
            result = cookie_manager.save_cookies_interactive()
            if result:
                safe_print("\n🎉 Cookies获取成功！")
                safe_print("💡 现在可以正常访问创作者中心功能了")
            return result
            
        elif action == "show":
            cookie_manager.display_cookies_info()
            return True
            
        elif action == "validate":
            result = cookie_manager.validate_cookies()
            if result:
                safe_print("✅ Cookies验证通过，可以正常使用创作者功能")
            else:
                safe_print("❌ Cookies验证失败，可能影响创作者中心访问")
                safe_print("💡 建议重新获取: python xhs_toolkit.py cookie save")
            return result
            
        elif action == "test":
            safe_print("🧪 测试ChromeDriver配置...")
            result = cookie_manager.test_chromedriver_config()
            return result
            
        else:
            safe_print(f"❌ 未知操作: {action}")
            safe_print("💡 可用操作: save, show, validate, test")
            return False
            
    except XHSToolkitError as e:
        safe_print(f"❌ Cookie操作失败: {format_error_message(e)}")
        return False
    except Exception as e:
        safe_print(f"❌ Cookie操作出现未知错误: {e}")
        if action == "save":
            safe_print("💡 常见解决方案:")
            safe_print("   1. 确保Chrome和ChromeDriver版本兼容")
            safe_print("   2. 检查网络连接是否正常")
            safe_print("   3. 确认小红书网站可以正常访问")
        return False

def server_command(action: str, port: int = 8000, host: str = "0.0.0.0") -> bool:
    """
    服务器管理命令
    
    Args:
        action: 操作类型 (start, stop, status)
        port: 服务器端口
        host: 服务器主机
        
    Returns:
        操作是否成功
    """
    if action == "start":
        safe_print("🚀 启动MCP服务器...")
        
        # 设置环境变量
        os.environ["SERVER_PORT"] = str(port)
        os.environ["SERVER_HOST"] = host
        
        try:
            # 初始化配置和服务器
            config = XHSConfig()
            server = MCPServer(config)
            # 使用asyncio.run来运行异步的start方法
            asyncio.run(server.start())
            return True
            
        except KeyboardInterrupt:
            safe_print("👋 服务器已停止")
            return True
        except XHSToolkitError as e:
            safe_print(f"❌ 服务器启动失败: {format_error_message(e)}")
            return False
        except Exception as e:
            safe_print(f"❌ 服务器启动出现未知错误: {e}")
            return False
            
    elif action == "stop":
        safe_print("🛑 正在停止MCP服务器...")
        
        try:
            import subprocess
            import signal
            
            # 查找MCP服务器进程
            result = subprocess.run(
                ["ps", "aux"] if os.name != 'nt' else ["tasklist"],
                capture_output=True,
                text=True
            )
            
            mcp_processes = []
            search_terms = ['xhs_mcp_server', 'xhs_toolkit.py']
            
            for line in result.stdout.split('\n'):
                if any(term in line for term in search_terms) and 'grep' not in line:
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1] if os.name != 'nt' else parts[1]
                        mcp_processes.append(pid)
            
            if not mcp_processes:
                safe_print("❌ 未找到运行中的MCP服务器")
                return False
            
            for pid in mcp_processes:
                safe_print(f"🔍 找到MCP服务器进程: {pid}")
                try:
                    if os.name == 'nt':  # Windows
                        subprocess.run(["taskkill", "/F", "/PID", pid], check=True)
                    else:  # Unix-like
                        os.kill(int(pid), signal.SIGTERM)
                        time.sleep(2)
                        try:
                            os.kill(int(pid), 0)
                            os.kill(int(pid), signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    
                    safe_print(f"✅ 进程 {pid} 已停止")
                    
                except Exception as e:
                    safe_print(f"⚠️ 停止进程 {pid} 时出错: {e}")
            
            # 清理ChromeDriver进程
            safe_print("🧹 清理ChromeDriver进程...")
            try:
                if os.name == 'nt':
                    subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe"], 
                                 capture_output=True)
                else:
                    subprocess.run(["pkill", "-f", "chromedriver"], 
                                 capture_output=True)
            except:
                pass
                
            safe_print("✅ MCP服务器已停止")
            return True
            
        except Exception as e:
            safe_print(f"❌ 停止服务器时出错: {e}")
            return False
            
    elif action == "status":
        safe_print("🔍 检查MCP服务器状态...")
        
        try:
            import subprocess
            
            result = subprocess.run(
                ["ps", "aux"] if os.name != 'nt' else ["tasklist"],
                capture_output=True,
                text=True
            )
            
            mcp_processes = []
            search_terms = ['xhs_mcp_server', 'xhs_toolkit.py']
            
            for line in result.stdout.split('\n'):
                if any(term in line for term in search_terms) and 'grep' not in line:
                    mcp_processes.append(line.strip())
            
            if mcp_processes:
                safe_print(f"✅ 找到 {len(mcp_processes)} 个运行中的MCP服务器:")
                for proc in mcp_processes:
                    parts = proc.split()
                    pid = parts[1] if len(parts) > 1 else "unknown"
                    print(f"   • 进程ID: {pid}")
            else:
                safe_print("❌ 未找到运行中的MCP服务器")
            
            return len(mcp_processes) > 0
                
        except Exception as e:
            safe_print(f"❌ 检查状态时出错: {e}")
            return False
            
    else:
        safe_print(f"❌ 未知的服务器操作: {action}")
        safe_print("💡 可用操作: start, stop, status")
        return False

async def publish_command(title: str, content: str, topics: str = "",
                         location: str = "", images: str = "", videos: str = ""):
    """
    发布小红书笔记
    
    Args:
        title: 笔记标题
        content: 笔记内容  
        topics: 话题（逗号分隔）
        location: 位置信息
        images: 图片路径（逗号分隔）
        videos: 视频路径（逗号分隔）
    """
    logger.info("🚀 开始发布小红书笔记")
    
    try:
        # 检查和初始化组件
        await ensure_component_initialization()
        
        # 创建笔记对象，使用智能解析
        note = await XHSNote.async_smart_create(
            title=title,
            content=content,
            topics=topics,
            location=location,
            images=images,
            videos=videos
        )
        
        logger.info(f"📝 笔记信息: 标题={note.title}, 话题={note.topics}")
        
        # 发布笔记
        result = await client.publish_note(note)
        
        if result.success:
            logger.info(f"✅ 笔记发布成功!")
            if result.final_url:
                logger.info(f"🔗 笔记链接: {result.final_url}")
        else:
            logger.error(f"❌ 笔记发布失败: {result.message}")
        
        return result
        
    except Exception as e:
        logger.error(f"💥 发布过程出错: {e}")
        import traceback
        logger.debug(f"详细错误信息: {traceback.format_exc()}")
        return XHSPublishResult(success=False, message=f"发布异常: {str(e)}")

def config_command(action: str) -> bool:
    """
    配置管理命令
    
    Args:
        action: 操作类型 (show, validate, example)
        
    Returns:
        操作是否成功
    """
    try:
        config = XHSConfig()
        
        if action == "show":
            safe_print("🔧 当前配置信息:")
            print("=" * 50)
            config_dict = config.to_dict()
            for key, value in config_dict.items():
                print(f"{key}: {value}")
            return True
            
        elif action == "validate":
            safe_print("🔍 验证配置...")
            validation = config.validate_config()
            
            if validation["valid"]:
                safe_print("✅ 配置验证通过")
                return True
            else:
                safe_print("❌ 配置验证失败:")
                for issue in validation["issues"]:
                    print(f"   • {issue}")
                return False
                
        elif action == "example":
            safe_print("📄 生成配置示例文件...")
            config.save_env_example()
            safe_print("✅ 已生成 env_example 文件")
            safe_print("💡 请复制为 .env 文件并根据需要修改配置")
            return True
            
        else:
            safe_print(f"❌ 未知操作: {action}")
            safe_print("💡 可用操作: show, validate, example")
            return False
            
    except XHSToolkitError as e:
        safe_print(f"❌ 配置操作失败: {format_error_message(e)}")
        return False
    except Exception as e:
        safe_print(f"❌ 配置操作出现未知错误: {e}")
        return False

def status_command() -> bool:
    """显示系统状态"""
    try:
        safe_print("📊 系统状态检查:")
        print("=" * 50)
        
        # 配置状态
        config = XHSConfig()
        validation = config.validate_config()
        
        safe_print(f"🔧 配置状态: {'✅ 正常' if validation['valid'] else '❌ 有问题'}")
        if not validation["valid"]:
            for issue in validation["issues"]:
                print(f"   • {issue}")
        
        # Cookies状态
        cookie_manager = CookieManager(config)
        cookies = cookie_manager.load_cookies()
        safe_print(f"🍪 Cookies状态: {'✅ 已加载' if cookies else '❌ 未找到'} ({len(cookies)} 个)")
        
        # 服务器状态
        server_running = server_command("status")
        safe_print(f"🚀 MCP服务器: {'✅ 运行中' if server_running else '❌ 未运行'}")
        
        # 系统信息
        import platform
        safe_print(f"💻 操作系统: {platform.system()} {platform.release()}")
        safe_print(f"🐍 Python版本: {platform.python_version()}")
        
        return validation["valid"]
        
    except Exception as e:
        safe_print(f"❌ 状态检查失败: {e}")
        return False

def main():
    """主入口函数"""
    print_banner()
    
    # 设置日志
    setup_logger()
    
    parser = argparse.ArgumentParser(description="小红书MCP工具包")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # Cookie管理命令
    cookie_parser = subparsers.add_parser("cookie", help="Cookie管理")
    cookie_parser.add_argument("action", choices=["save", "show", "validate", "test"], 
                              help="操作类型")
    
    # 服务器管理命令
    server_parser = subparsers.add_parser("server", help="MCP服务器管理")
    server_parser.add_argument("action", choices=["start", "stop", "status"], 
                              help="操作类型")
    server_parser.add_argument("--port", type=int, default=8000, help="服务器端口")
    server_parser.add_argument("--host", default="0.0.0.0", help="服务器主机")
    
    # 发布命令
    publish_parser = subparsers.add_parser("publish", help="发布笔记")
    publish_parser.add_argument("title", help="笔记标题")
    publish_parser.add_argument("content", help="笔记内容")
    publish_parser.add_argument("--topics", default="", help="话题（逗号分隔）")
    publish_parser.add_argument("--location", default="", help="位置信息")
    publish_parser.add_argument("--images", default="", help="图片路径（逗号分隔）")
    publish_parser.add_argument("--videos", default="", help="视频路径（逗号分隔）")
    
    # 配置管理命令
    config_parser = subparsers.add_parser("config", help="配置管理")
    config_parser.add_argument("action", choices=["show", "validate", "example"], 
                              help="操作类型")
    
    # 状态检查命令
    subparsers.add_parser("status", help="显示系统状态")
    
    # 手动操作命令
    add_manual_parser(subparsers)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        success = False
        
        if args.command == "cookie":
            success = cookie_command(args.action)
        elif args.command == "server":
            success = server_command(args.action, args.port, args.host)
        elif args.command == "publish":
            success = asyncio.run(publish_command(
                args.title, args.content, args.topics, args.location, args.images, args.videos
            ))
        elif args.command == "config":
            success = config_command(args.action)
        elif args.command == "status":
            success = status_command()
        elif args.command == "manual":
            if not args.manual_action:
                parser.parse_args(['manual', '--help'])
                return
            # 构建参数字典
            kwargs = {}
            if args.manual_action == "collect":
                kwargs['data_type'] = args.data_type
                kwargs['dimension'] = args.dimension
            elif args.manual_action == "browser":
                kwargs['page'] = args.page
                kwargs['stay_open'] = args.stay_open
            elif args.manual_action == "export":
                kwargs['format'] = args.format
                kwargs['output_dir'] = args.output_dir
            elif args.manual_action == "backup":
                kwargs['include_cookies'] = args.include_cookies
            elif args.manual_action == "restore":
                kwargs['backup_path'] = args.backup_path
            
            success = manual_command(args.manual_action, **kwargs)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        safe_print("\n👋 操作已取消")
        sys.exit(1)
    except Exception as e:
        safe_print(f"❌ 程序执行出错: {e}")
        logger.exception("程序执行异常")
        sys.exit(1)

if __name__ == "__main__":
    main() 
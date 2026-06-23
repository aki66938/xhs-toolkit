"""
小红书MCP服务器模块

提供MCP协议的服务器实现，支持AI客户端通过MCP协议与小红书交互
"""

import os
import json
import asyncio
import signal
import sys
import socket
import uuid
import time
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass, asdict

from fastmcp import FastMCP

from ..core.config import XHSConfig
from ..core.exceptions import format_error_message, XHSToolkitError
from ..xiaohongshu.client import XHSClient
from ..xiaohongshu.models import XHSNote
from ..utils.logger import get_logger, setup_logger
from ..data import storage_manager, data_scheduler
from ..auth.smart_auth_server import SmartAuthServer, create_smart_auth_server

logger = get_logger(__name__)


@dataclass
class PublishTask:
    """发布任务数据类"""
    task_id: str
    status: str  # "pending", "uploading", "filling", "publishing", "completed", "failed"
    note: XHSNote
    progress: int  # 0-100
    message: str
    result: Dict[str, Any] = None
    start_time: float = None
    end_time: float = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 移除note对象，避免序列化问题
        if 'note' in data:
            data['note_title'] = self.note.title
            data['note_has_images'] = bool(self.note.images)
            data['note_has_videos'] = bool(self.note.videos)
            del data['note']
        return data


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, PublishTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
    
    def create_task(self, note: XHSNote) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())[:8]  # 使用短ID
        task = PublishTask(
            task_id=task_id,
            status="pending",
            note=note,
            progress=0,
            message="任务已创建，准备开始",
            start_time=time.time()
        )
        self.tasks[task_id] = task
        logger.info(f"📋 创建新任务: {task_id} - {note.title}")
        return task_id
    
    def get_task(self, task_id: str) -> PublishTask:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, status: str = None, progress: int = None, message: str = None, result: Dict = None):
        """更新任务状态"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            if status:
                task.status = status
            if progress is not None:
                task.progress = progress
            if message:
                task.message = message
            if result:
                task.result = result
            if status in ["completed", "failed"]:
                task.end_time = time.time()
            logger.info(f"📋 更新任务 {task_id}: {status} ({progress}%) - {message}")
    
    def remove_old_tasks(self, max_age_seconds: int = 3600):
        """移除超过指定时间的旧任务"""
        current_time = time.time()
        expired_tasks = []
        for task_id, task in self.tasks.items():
            if task.end_time and (current_time - task.end_time) > max_age_seconds:
                expired_tasks.append(task_id)
        
        for task_id in expired_tasks:
            del self.tasks[task_id]
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
                del self.running_tasks[task_id]
            logger.info(f"🗑️ 清理过期任务: {task_id}")


class MCPServer:
    """MCP服务器管理器"""
    
    def __init__(self, config: XHSConfig):
        """
        初始化MCP服务器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.xhs_client = XHSClient(config)
        self.mcp = FastMCP("小红书MCP服务器")
        self.task_manager = TaskManager()  # 添加任务管理器
        self.scheduler_initialized = False  # 调度器初始化标志
        self.auth_server = create_smart_auth_server(config)  # 智能认证服务器
        self._setup_tools()
        self._setup_resources()
        self._setup_prompts()
    
    async def _initialize_data_collection(self) -> None:
        """初始化数据采集功能"""
        if self.scheduler_initialized:
            return  # 已经初始化过了
            
        try:
            import os
            logger.info("📊 初始化数据采集功能...")
            
            # 检查cookies是否存在，数据采集需要登录状态
            cookies = self.xhs_client.cookie_manager.load_cookies()
            if not cookies:
                logger.warning("⚠️ 未找到cookies文件，跳过数据采集功能初始化")
                logger.info("💡 数据采集需要登录状态，请先运行: python xhs_toolkit.py cookie save")
                self.scheduler_initialized = False
                return
            
            logger.info(f"✅ 检测到 {len(cookies)} 个cookies，可以进行数据采集")
            
            # 初始化存储管理器
            storage_manager.initialize()
            storage_info = storage_manager.get_storage_info()
            logger.info(f"💾 存储配置: {storage_info['storage_types']}")
            
            # 检查是否启用自动采集
            enable_auto_collection = os.getenv('ENABLE_AUTO_COLLECTION', 'false').lower() == 'true'
            
            if enable_auto_collection:
                # 初始化调度器
                data_scheduler.initialize(self.xhs_client)
                
                # 启动调度器
                await data_scheduler.start()
                
                if data_scheduler.is_running():
                    job_info = data_scheduler.get_job_info()
                    logger.info("⏰ 数据采集调度器已启动")
                    
                    # 显示下次执行时间
                    if job_info.get('jobs'):
                        for job in job_info['jobs']:
                            next_run = job.get('next_run_time')
                            if next_run:
                                logger.info(f"📅 下次采集时间: {next_run}")
                else:
                    logger.warning("⚠️ 调度器启动失败")
            else:
                logger.info("📊 自动数据采集已禁用")
                
            self.scheduler_initialized = True
            
        except Exception as e:
            import traceback
            logger.error(f"❌ 数据采集功能初始化失败: {e}")
            logger.error(f"❌ 错误详情: {traceback.format_exc()}")
            self.scheduler_initialized = False
    
    def _setup_tools(self) -> None:
        """设置MCP工具"""
        
        @self.mcp.tool()
        async def test_connection() -> str:
            """
            测试MCP连接是否正常
            
            Returns:
                连接状态信息
            """
            logger.info("🧪 收到连接测试请求")
            try:
                import time
                import os
                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                
                # 检查配置
                config_status = self.config.to_dict()
                config_status["current_time"] = current_time
                
                # 添加数据采集状态
                config_status["data_collection"] = {
                    "scheduler_initialized": self.scheduler_initialized,
                    "auto_collection_enabled": os.getenv('ENABLE_AUTO_COLLECTION', 'false').lower() == 'true',
                    "storage_info": storage_manager.get_storage_info() if self.scheduler_initialized else None
                }
                
                logger.info(f"✅ 连接测试完成: {config_status}")
                
                result = {
                    "status": "success",
                    "message": "MCP连接正常！",
                    "config": config_status,
                    "timestamp": current_time
                }
                
                return json.dumps(result, ensure_ascii=False, indent=2)
                
            except Exception as e:
                error_msg = f"连接测试失败: {str(e)}"
                logger.error(f"❌ {error_msg}")
                return error_msg
        
        @self.mcp.tool()
        async def smart_publish_note(title: str, content: str, images=None, videos=None, 
                                   topics=None, location: str = "") -> str:
            """
            发布小红书笔记（支持多种输入格式）
            
            这是主要的笔记发布工具，支持更灵活的参数输入，可以处理来自不同平台的各种数据格式。
            
            Args:
                title (str): 笔记标题
                content (str): 笔记内容  
                images: 图片，支持格式：
                       - 本地路径："image.jpg" 或 ["/path/to/image.jpg"]
                       - 网络地址："https://example.com/image.jpg"
                       - 混合数组：["local.jpg", "https://example.com/img.jpg"]
                       - 逗号分隔字符串："a.jpg,b.jpg,c.jpg"
                videos: 视频路径（目前仅支持本地文件）
                topics: 话题，支持字符串或数组格式
                location (str, optional): 位置信息
            
            Returns:
                str: 任务ID和状态信息
                
            示例:
                # 使用网络图片
                smart_publish_note(
                    title="美食分享",
                    content="今天的美食",
                    images=["https://example.com/food.jpg"]
                )
                
            """
            logger.info(f"🚀 启动发布任务: 标题='{title}'")
            logger.debug(f"📋 参数详情: images={images}, videos={videos}, topics={topics}")
            
            try:
                # 使用异步智能创建方法
                note = await XHSNote.async_smart_create(
                    title=title,
                    content=content,
                    topics=topics,
                    location=location,
                    images=images,
                    videos=videos
                )
                
                # 记录解析结果
                logger.info(f"✅ 智能解析结果: 图片{len(note.images) if note.images else 0}张, 视频{len(note.videos) if note.videos else 0}个, 话题{len(note.topics) if note.topics else 0}个")
                
                # 创建异步任务
                task_id = self.task_manager.create_task(note)
                
                # 启动后台任务
                async_task = asyncio.create_task(self._execute_publish_task(task_id))
                self.task_manager.running_tasks[task_id] = async_task
                
                result = {
                    "success": True,
                    "task_id": task_id,
                    "message": f"发布任务已启动，任务ID: {task_id}",
                    "next_step": f"请使用 check_task_status('{task_id}') 查看进度",
                    "parsing_result": {
                        "images_parsed": note.images if note.images else [],
                        "videos_parsed": note.videos if note.videos else [],
                        "topics_parsed": note.topics if note.topics else [],
                        "images_count": len(note.images) if note.images else 0,
                        "videos_count": len(note.videos) if note.videos else 0,
                        "topics_count": len(note.topics) if note.topics else 0,
                        "content_type": "图文" if note.images else "视频" if note.videos else "纯文本"
                    }
                }
                
                return json.dumps(result, ensure_ascii=False, indent=2)
                
            except Exception as e:
                error_msg = f"发布任务启动失败: {str(e)}"
                logger.error(f"❌ {error_msg}")
                return json.dumps({
                    "success": False,
                    "message": error_msg,
                    "suggestion": "请检查输入格式，确保图片/视频路径正确或网络连接正常"
                }, ensure_ascii=False, indent=2)
        
        @self.mcp.tool()
        async def check_task_status(task_id: str) -> str:
            """
            检查发布任务状态
            
            Args:
                task_id (str): 任务ID
            
            Returns:
                str: 任务状态信息
            """
            logger.info(f"📊 检查任务状态: {task_id}")
            
            task = self.task_manager.get_task(task_id)
            if not task:
                return json.dumps({
                    "success": False,
                    "message": f"任务 {task_id} 不存在"
                }, ensure_ascii=False, indent=2)
            
            # 计算运行时间
            elapsed_time = 0
            if task.start_time:
                elapsed_time = int(time.time() - task.start_time)
            
            result = {
                "success": True,
                "task_id": task_id,
                "status": task.status,
                "progress": task.progress,
                "message": task.message,
                "elapsed_seconds": elapsed_time,
                "is_completed": task.status in ["completed", "failed"]
            }
            
            # 如果任务完成，包含结果
            if task.result:
                result["result"] = task.result
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        @self.mcp.tool()
        async def get_task_result(task_id: str) -> str:
            """
            获取已完成任务的结果
            
            Args:
                task_id (str): 任务ID
            
            Returns:
                str: 任务结果信息
            """
            logger.info(f"📋 获取任务结果: {task_id}")
            
            task = self.task_manager.get_task(task_id)
            if not task:
                return json.dumps({
                    "success": False,
                    "message": f"任务 {task_id} 不存在"
                }, ensure_ascii=False, indent=2)
            
            if task.status not in ["completed", "failed"]:
                return json.dumps({
                    "success": False,
                    "message": f"任务 {task_id} 尚未完成，当前状态: {task.status}",
                    "current_status": task.status,
                    "progress": task.progress
                }, ensure_ascii=False, indent=2)
            
            # 返回完整结果
            result = {
                "success": task.status == "completed",
                "task_id": task_id,
                "status": task.status,
                "message": task.message,
                "execution_time": int(task.end_time - task.start_time) if task.end_time and task.start_time else 0
            }
            
            if task.result:
                result["publish_result"] = task.result
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        @self.mcp.tool()
        async def login_xiaohongshu(force_relogin: bool = False, quick_mode: bool = False) -> str:
            """
            智能登录小红书
            
            当用户说"登录小红书"时调用此工具。提供MCP专用的智能流程，无需用户交互确认。
            
            Args:
                force_relogin: 是否强制重新登录，即使当前状态有效
                quick_mode: 快速模式，降低验证要求以避免超时
                
            Returns:
                登录结果的JSON字符串
            """
            logger.info(f"🚀 MCP工具调用：智能小红书 (force_relogin={force_relogin}, quick_mode={quick_mode})")
            
            try:
                # 如果是快速模式，先检查是否已有cookies
                if quick_mode:
                    cookies_file = Path(self.config.cookies_file)
                    if cookies_file.exists():
                        logger.info("⚡ 快速模式：发现已有cookies，跳过登录")
                        return json.dumps({
                            "success": True,
                            "message": "✅ 快速模式：检测到已有cookies，跳过登录流程",
                            "action": "quick_skip",
                            "status": "valid",
                            "mode": "mcp_quick"
                        }, ensure_ascii=False, indent=2)
                
                # 使用MCP专用的智能模式
                result = await self.auth_server.smart_login(interactive=False, mcp_mode=True)
                
                # 格式化返回消息
                if result.get("success", False):
                    action = result.get("action", "unknown")
                    if action == "mcp_auto_login":
                        message = f"✅ {result['message']}\n🤖 MCP智能登录已完成，cookies已保存"
                    elif action == "skipped":
                        message = f"✅ {result['message']}\n💡 当前登录状态有效"
                    else:
                        message = f"✅ {result['message']}"
                else:
                    message = f"❌ {result['message']}\n🔧 请检查浏览器或网络连接"
                
                logger.info(f"✅ MCP自动登录结果: {result.get('action', 'unknown')}")
                return json.dumps({
                    "success": result.get("success", False),
                    "message": message,
                    "action": result.get("action", "unknown"),
                    "status": result.get("status", "unknown"),
                    "mode": "mcp_auto"
                }, ensure_ascii=False, indent=2)
                
            except Exception as e:
                error_msg = f"MCP自动登录执行失败: {str(e)}"
                logger.error(f"❌ {error_msg}")
                return json.dumps({
                    "success": False,
                    "message": f"❌ {error_msg}",
                    "error": str(e),
                    "mode": "mcp_auto",
                    "suggestion": "可以尝试快速模式：login_xiaohongshu(quick_mode=True)"
                }, ensure_ascii=False, indent=2)
        
        @self.mcp.tool()
        async def get_creator_data_analysis() -> str:
            """
            获取创作者数据用于分析
            
            Returns:
                str: 包含所有创作者数据的详细信息用于数据分析
            """
            logger.info("📊 获取创作者数据用于分析")
            
            try:
                # 检查cookies是否存在，数据分析需要登录状态
                cookies = self.xhs_client.cookie_manager.load_cookies()
                if not cookies:
                    return json.dumps({
                        "success": False,
                        "message": "数据分析需要登录状态，未找到cookies文件",
                        "suggestion": "请先运行: python xhs_toolkit.py cookie save"
                    }, ensure_ascii=False, indent=2)
                
                if not self.scheduler_initialized:
                    return json.dumps({
                        "success": False,
                        "message": "数据采集功能未初始化，可能因为cookies问题",
                        "suggestion": "请检查cookies状态并重启服务器"
                    }, ensure_ascii=False, indent=2)
                
                # 获取存储管理器
                csv_storage = storage_manager.get_csv_storage()
                
                # 读取所有数据
                dashboard_data = await csv_storage.get_latest_data('dashboard', limit=100)
                content_data = await csv_storage.get_latest_data('content_analysis', limit=100)
                fans_data = await csv_storage.get_latest_data('fans', limit=100)
                
                # 获取存储信息
                storage_info = storage_manager.get_storage_info()
                
                result = {
                    "success": True,
                    "message": "创作者数据获取成功，可用于分析",
                    "data_summary": {
                        "dashboard_records": len(dashboard_data),
                        "content_records": len(content_data),
                        "fans_records": len(fans_data),
                        "storage_info": storage_info
                    },
                    "dashboard_data": dashboard_data,
                    "content_analysis_data": content_data,
                    "fans_data": fans_data,
                    "analysis_tips": {
                        "dashboard": "仪表板数据包含账号整体表现指标",
                        "content": "内容分析数据包含每篇笔记的详细表现",
                        "fans": "粉丝数据包含粉丝增长趋势"
                    },
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                }
                
                return json.dumps(result, ensure_ascii=False, indent=2)
                
            except Exception as e:
                error_msg = f"获取创作者数据失败: {str(e)}"
                logger.error(f"❌ {error_msg}")
                return json.dumps({
                    "success": False,
                    "message": error_msg
                }, ensure_ascii=False, indent=2)
        
    
    async def _execute_publish_task(self, task_id: str) -> None:
        """
        执行发布任务的后台逻辑
        
        Args:
            task_id: 任务ID
        """
        task = self.task_manager.get_task(task_id)
        if not task:
            logger.error(f"❌ 任务 {task_id} 不存在")
            return
        
        try:
            # 阶段0：快速验证登录状态（仅检查cookies存在性）
            self.task_manager.update_task(task_id, status="validating", progress=5, message="正在快速验证登录状态...")
            
            try:
                # 只检查cookies文件是否存在，避免重复的详细验证
                cookies_file = Path(self.config.cookies_file)
                if not cookies_file.exists():
                    self.task_manager.update_task(
                        task_id, 
                        status="failed", 
                        progress=0, 
                        message="❌ 未找到登录cookies，请先登录小红书",
                        result={
                            "success": False,
                            "error_type": "auth_required",
                            "user_action_required": "需要登录小红书",
                            "suggested_command": "请对AI说：'登录小红书'"
                        }
                    )
                    logger.warning(f"⚠️ 任务 {task_id} 因缺少cookies而停止")
                    return
                
                # 快速验证通过，继续发布流程
                self.task_manager.update_task(task_id, status="initializing", progress=10, message="✅ 登录状态验证通过，正在初始化浏览器...")
                
            except Exception as e:
                logger.error(f"❌ 登录状态验证出错: {e}")
                self.task_manager.update_task(
                    task_id, 
                    status="failed", 
                    progress=0, 
                    message=f"❌ 登录状态验证出错: {str(e)}",
                    result={
                        "success": False,
                        "error_type": "validation_error",
                        "error": str(e),
                        "suggested_action": "请重新登录小红书后重试"
                    }
                )
                return
            
            # 阶段1：初始化浏览器
            # 创建新的客户端实例，避免并发冲突
            client = XHSClient(self.config)
            
            # 阶段2：上传文件
            if task.note.images or task.note.videos:
                self.task_manager.update_task(task_id, status="uploading", progress=20, message="正在上传文件...")
                
                # 执行发布过程
                result = await client.publish_note(task.note)
                
                if result.success:
                    self.task_manager.update_task(
                        task_id, 
                        status="completed", 
                        progress=100, 
                        message="发布成功！",
                        result=result.to_dict()
                    )
                else:
                    self.task_manager.update_task(
                        task_id, 
                        status="failed", 
                        progress=0, 
                        message=f"发布失败: {result.message}",
                        result=result.to_dict()
                    )
            else:
                # 没有文件的快速发布
                self.task_manager.update_task(task_id, status="publishing", progress=60, message="正在发布笔记...")
                
                result = await client.publish_note(task.note)
                
                if result.success:
                    self.task_manager.update_task(
                        task_id, 
                        status="completed", 
                        progress=100, 
                        message="发布成功！",
                        result=result.to_dict()
                    )
                else:
                    self.task_manager.update_task(
                        task_id, 
                        status="failed", 
                        progress=0, 
                        message=f"发布失败: {result.message}",
                        result=result.to_dict()
                    )
                
        except Exception as e:
            error_msg = f"任务执行失败: {str(e)}"
            logger.error(f"❌ 任务 {task_id} 执行失败: {e}")
            self.task_manager.update_task(
                task_id, 
                status="failed", 
                progress=0, 
                message=error_msg,
                result={"success": False, "message": error_msg}
            )
        finally:
            # 清理运行任务记录
            if task_id in self.task_manager.running_tasks:
                del self.task_manager.running_tasks[task_id]

    def _setup_resources(self) -> None:
        """设置MCP资源"""
        
        @self.mcp.resource("xhs://config")
        def get_xhs_config() -> str:
            """获取小红书MCP服务器配置信息"""
            config_info = self.config.to_dict()
            config_info["server_status"] = "running"
            return json.dumps(config_info, ensure_ascii=False, indent=2)
        
        @self.mcp.resource("xhs://help")
        def get_xhs_help() -> str:
            """获取小红书MCP服务器使用帮助"""
            help_text = """
# 小红书MCP服务器使用帮助

## 可用工具

### 1. test_connection
- 功能: 测试MCP连接
- 参数: 无

### 2. start_publish_task
- 功能: 启动异步发布任务（解决MCP超时问题）
- 参数:
  - title: 笔记标题
  - content: 笔记内容
  - tags: 标签（逗号分隔）
  - location: 位置信息
  - images: 图片路径（逗号分隔多个路径）
  - videos: 视频路径（逗号分隔多个路径）

### 3. check_task_status
- 功能: 检查发布任务状态
- 参数:
  - task_id: 任务ID

### 4. get_task_result
- 功能: 获取已完成任务的结果
- 参数:
  - task_id: 任务ID

### 5. close_browser
- 功能: 关闭浏览器

### 6. test_publish_params
- 功能: 测试发布参数解析（调试用）
- 参数:
  - title: 测试标题
  - content: 测试内容
  - image_path: 测试图片路径

## 可用资源

- xhs://config - 查看服务器配置
- xhs://help - 查看此帮助信息

## 环境变量

- CHROME_PATH: Chrome浏览器路径
- WEBDRIVER_CHROME_DRIVER: ChromeDriver路径
- json_path: Cookies文件路径
"""
            return help_text
    
    def _setup_prompts(self) -> None:
        """设置MCP提示词"""
        
        @self.mcp.prompt()
        def xiaohongshu_content_creation(topic: str, style: str = "生活分享") -> str:
            """
            小红书内容创作助手
            
            Args:
                topic: 内容主题
                style: 写作风格（生活分享、美妆护肤、美食探店、旅行攻略等）
            
            Returns:
                内容创作提示词
            """
            prompt = f"""
请帮我创作一篇关于"{topic}"的小红书笔记，风格为"{style}"。

要求：
1. 标题要吸引人，包含emoji和关键词
2. 内容要有价值，包含具体的建议或信息
3. 适当使用emoji让内容更生动
4. 添加相关标签（3-5个）
5. 字数控制在200-500字
6. 语言风格要贴近小红书用户习惯

请按以下格式输出：

【标题】
[在这里写标题]

【正文】
[在这里写正文内容]

【标签】
[在这里列出相关标签]

【发布建议】
[发布时间、配图建议等]
"""
            return prompt
    
    def _setup_signal_handlers(self) -> None:
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info("👋 收到停止信号，正在优雅关闭服务器...")
            # 清理资源
            try:
                # 停止数据采集调度器
                if self.scheduler_initialized and data_scheduler.is_running():
                    logger.info("🧹 停止数据采集调度器...")
                    asyncio.run(data_scheduler.stop())
                
                # 清理浏览器实例
                if hasattr(self.xhs_client, 'browser_manager') and self.xhs_client.browser_manager.is_initialized:
                    logger.info("🧹 清理残留的浏览器实例...")
                    self.xhs_client.browser_manager.close_driver()
            except Exception as cleanup_error:
                logger.warning(f"⚠️ 清理资源时出错: {cleanup_error}")
            
            logger.info("✅ 服务器已停止")
            os._exit(0)  # 强制退出避免ASGI错误
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def start_stdio(self) -> None:
        """启动stdio模式的MCP服务器（用于Claude Desktop）"""
        # 设置日志只输出到stderr，避免干扰stdio通信
        import sys
        from ..utils.logger import setup_logger, get_logger
        
        # 重新配置日志，只输出到stderr
        import logging
        root_logger = logging.getLogger()
        root_logger.handlers = []
        
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s'))
        root_logger.addHandler(stderr_handler)
        root_logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        logger.info("🚀 启动MCP服务器（stdio模式）...")
        
        # 验证配置
        validation = self.config.validate_config()
        if not validation["valid"]:
            logger.error("❌ 配置验证失败:")
            for issue in validation["issues"]:
                logger.error(f"   • {issue}")
            return
        
        logger.info("✅ 配置验证通过")
        
        # 工具已在__init__中注册
        logger.info(f"🎯 MCP工具列表:")
        for tool in ["test_connection", "smart_publish_note", "check_task_status", 
                    "get_task_result", "login_xiaohongshu", "get_creator_data_analysis"]:
            logger.info(f"   • {tool}")
        
        # 初始化数据采集（如果启用）
        try:
            cookies = self.xhs_client.cookie_manager.load_cookies()
            if cookies and os.getenv('ENABLE_AUTO_COLLECTION', 'false').lower() == 'true':
                logger.info("📊 初始化数据采集功能...")
                # stdio模式下使用无头浏览器
                self.xhs_client.browser_manager.headless = True
                await self._initialize_data_collection()

                if self.scheduler_initialized:
                    logger.info("✅ 数据采集功能初始化完成")
                else:
                    logger.info("ℹ️ 数据采集功能未启用或初始化失败")
            else:
                logger.info("ℹ️ 数据采集功能未启用")
        except Exception as e:
            logger.warning(f"⚠️ 数据采集功能初始化失败: {e}")
        
        # 使用stdio transport
        logger.info("🎯 MCP工具已注册，等待客户端连接...")
        await self.mcp.run_async(transport="stdio")
    
    async def start(self) -> None:
        """启动MCP服务器"""
        logger.info("🚀 启动小红书 MCP 服务器...")
        
        # 设置日志级别
        setup_logger(self.config.log_level)
        
        # 验证配置
        logger.info("🔍 验证配置...")
        validation = self.config.validate_config()
        
        if not validation["valid"]:
            logger.error("❌ 配置验证失败:")
            for issue in validation["issues"]:
                logger.error(f"   • {issue}")
            logger.error("💡 请检查 .env 文件配置")
            return
        
        logger.info("✅ 配置验证通过")
        
        # 设置信号处理
        self._setup_signal_handlers()
        
        # 获取本机IP地址
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("10.254.254.254", 80))
            local_ip = s.getsockname()[0]
            s.close()
            logger.info(f"📡 本机IP地址: {local_ip}")
        except Exception:
            local_ip = "未知"
            
        logger.info(f"🚀 启动SSE服务器 (端口{self.config.server_port})")
        logger.info("📡 可通过以下地址访问:")
        logger.info(f"   • http://localhost:{self.config.server_port}/sse (本机)")
        if local_ip != "未知":
            logger.info(f"   • http://{local_ip}:{self.config.server_port}/sse (内网)")
        
        logger.info("🎯 MCP工具列表:")
        logger.info("   • test_connection - 测试MCP连接")
        logger.info("   • smart_publish_note - 发布小红书笔记（支持智能路径解析）")
        logger.info("   • check_task_status - 检查发布任务状态")
        logger.info("   • get_task_result - 获取已完成任务的结果")
        logger.info("   • login_xiaohongshu - 智能登录小红书")
        logger.info("   • get_creator_data_analysis - 获取创作者数据用于分析")
        
        logger.info("🔧 按 Ctrl+C 停止服务器")
        logger.info("💡 终止时的ASGI错误信息是正常现象，可以忽略")
        
        # 初始化数据采集功能（无头模式）
        logger.info("📊 初始化数据采集功能（无头模式）...")
        try:
            await self._initialize_data_collection()
            if self.scheduler_initialized:
                logger.info("✅ 数据采集功能初始化完成（无头模式）")
            else:
                logger.info("ℹ️ 数据采集功能未启用或初始化失败")
        except Exception as e:
            logger.warning(f"⚠️ 数据采集功能初始化失败: {e}")
        
        try:
            # 使用FastMCP内置的run方法，禁用uvicorn的日志以避免干扰MCP通信
            import logging
            logging.getLogger("uvicorn").setLevel(logging.WARNING)
            logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
            
            await self.mcp.run_async(transport="sse", port=self.config.server_port, host=self.config.server_host)
            
        except KeyboardInterrupt:
            logger.info("👋 收到停止信号，正在关闭服务器...")
        except Exception as e:
            logger.error(f"❌ 服务器启动失败: {e}")
            raise
        finally:
            # 清理资源
            try:
                # 停止数据采集调度器
                if self.scheduler_initialized and data_scheduler.is_running():
                    logger.info("🧹 停止数据采集调度器...")
                    asyncio.run(data_scheduler.stop())
                
                # 清理浏览器实例
                if hasattr(self.xhs_client, 'browser_manager') and self.xhs_client.browser_manager.is_initialized:
                    logger.info("🧹 清理残留的浏览器实例...")
                    self.xhs_client.browser_manager.close_driver()
            except Exception as cleanup_error:
                logger.warning(f"⚠️ 清理资源时出错: {cleanup_error}")
            
            logger.info("✅ 服务器已停止")


# 便捷函数
def create_mcp_server(config: XHSConfig) -> MCPServer:
    """
    创建MCP服务器的便捷函数
    
    Args:
        config: 配置管理器实例
        
    Returns:
        MCP服务器实例
    """
    return MCPServer(config)


def main():
    """主函数入口"""
    import sys
    from ..core.config import XHSConfig
    
    config = XHSConfig()
    server = MCPServer(config)
    
    # 检查是否通过stdio启动（Claude Desktop使用）
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        # 使用stdio模式
        asyncio.run(server.start_stdio())
    else:
        # 默认使用SSE模式（用于其他客户端）
        asyncio.run(server.start())


if __name__ == "__main__":
    main() 
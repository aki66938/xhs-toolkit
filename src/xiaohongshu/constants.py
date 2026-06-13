"""
小红书模块常量定义

集中管理CSS选择器、URL、配置等常量，遵循DRY原则
"""

from typing import Dict, List


class XHSUrls:
    """小红书相关URL常量"""
    
    CREATOR_CENTER = "https://creator.xiaohongshu.com"
    PUBLISH_PAGE = "https://creator.xiaohongshu.com/publish/publish?from=menu"
    LOGIN_PAGE = "https://www.xiaohongshu.com/login"


class XHSSelectors:
    """小红书页面CSS选择器常量"""
    
    # 文件上传相关
    FILE_UPLOAD_INPUT = ".upload-input"
    FILE_UPLOAD_INPUT_ALT = "input[type='file']"
    FILE_UPLOAD_CONTAINER = "[class*='upload'][type='file']"
    
    # 发布模式切换
    CREATOR_TABS = ".creator-tab"
    IMAGE_TAB_TEXT = "上传图文"
    VIDEO_TAB_TEXT = "上传视频"
    
    # 内容填写
    TITLE_INPUT = ".d-text"
    TITLE_INPUT_ALT = "[placeholder*='标题']"
    CONTENT_EDITOR = "[contenteditable='true']"  # Tiptap 编辑器（小红书已升级）
    CONTENT_EDITOR_ALT = ".tiptap"
    CONTENT_EDITOR_LEGACY = ".ql-editor"  # 旧版 Quill 编辑器（备用）
    
    # 发布按钮
    PUBLISH_BUTTON = ".publishBtn"
    PUBLISH_BUTTON_ALT = "[class*='publish']"
    PUBLISH_BUTTON_XPATH = "//button[contains(text(), '发布')]"
    
    # 上传状态
    UPLOAD_PROGRESS = ".upload-progress"
    UPLOAD_SUCCESS = ".upload-success"
    UPLOAD_ERROR = ".upload-error"
    
    # 视频处理状态
    VIDEO_PROCESSING = ".video-processing"
    VIDEO_COMPLETE = ".video-complete"


class XHSConfig:
    """小红书配置常量"""
    
    # 文件限制
    MAX_IMAGES = 9
    MAX_VIDEOS = 1
    MAX_TITLE_LENGTH = 50
    MAX_CONTENT_LENGTH = 1000
    MAX_TOPICS = 10
    MAX_TOPIC_LENGTH = 20
    
    # 支持的文件格式
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.m4v']
    
    # 等待时间配置（秒）
    DEFAULT_WAIT_TIME = 10
    LONG_WAIT_TIME = 30
    SHORT_WAIT_TIME = 5
    PAGE_LOAD_TIME = 20
    FILE_UPLOAD_TIME = 60
    VIDEO_PROCESSING_TIME = 120
    
    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 2


class XHSMessages:
    """小红书相关消息常量"""
    
    # 成功消息
    PUBLISH_SUCCESS = "笔记发布成功"
    UPLOAD_SUCCESS = "文件上传成功"
    LOGIN_SUCCESS = "登录成功"
    
    # 错误消息
    PUBLISH_FAILED = "笔记发布失败"
    UPLOAD_FAILED = "文件上传失败"
    LOGIN_REQUIRED = "需要登录"
    NETWORK_ERROR = "网络连接错误"
    FILE_NOT_FOUND = "文件不存在"
    INVALID_FILE_FORMAT = "不支持的文件格式"
    
    # 警告消息
    LONG_CONTENT_WARNING = "内容较长，可能影响发布效果"
    TOO_MANY_IMAGES_WARNING = "图片数量过多"
    LARGE_FILE_WARNING = "文件过大，上传可能较慢"


def get_file_upload_selectors() -> List[str]:
    """获取文件上传选择器列表，按优先级排序"""
    return [
        XHSSelectors.FILE_UPLOAD_INPUT,
        XHSSelectors.FILE_UPLOAD_INPUT_ALT,
        XHSSelectors.FILE_UPLOAD_CONTAINER
    ]


def get_title_input_selectors() -> List[str]:
    """获取标题输入框选择器列表，按优先级排序"""
    return [
        XHSSelectors.TITLE_INPUT,
        XHSSelectors.TITLE_INPUT_ALT
    ]


def get_publish_button_selectors() -> List[str]:
    """获取发布按钮选择器列表，按优先级排序"""
    return [
        XHSSelectors.PUBLISH_BUTTON,
        XHSSelectors.PUBLISH_BUTTON_ALT
    ]


def is_supported_image_format(file_path: str) -> bool:
    """检查是否为支持的图片格式"""
    import os
    _, ext = os.path.splitext(file_path.lower())
    return ext in XHSConfig.SUPPORTED_IMAGE_FORMATS


def is_supported_video_format(file_path: str) -> bool:
    """检查是否为支持的视频格式"""
    import os
    _, ext = os.path.splitext(file_path.lower())
    return ext in XHSConfig.SUPPORTED_VIDEO_FORMATS 
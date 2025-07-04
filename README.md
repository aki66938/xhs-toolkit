# 📕 小红书创作者MCP工具包

[![许可证](https://img.shields.io/github/license/aki66938/xhs-toolkit)](LICENSE)
[![微信公众号](https://img.shields.io/badge/凯隐的无人化生产矩阵-公众号-bule?style=flat-square&logo=wechat)]((https://kayin-1253854796.cos.ap-shanghai.myqcloud.com/ownmedia/20250622023225261.jpg?imageSlim))

一个强大的小红书自动化工具包，支持通过MCP协议与AI客户端（如Claude Desktop等）集成，实现与AI对话即可进行内容创作、发布及创作者数据分析。

## ✨ 主要特性

- 🍪 **Cookie管理**: 安全获取、验证和管理小红书登录凭证
- 🤖 **MCP协议支持**: 与Claude Desktop、CherryStudio等AI客户端无缝集成
- 📝 **自动发布**: 支持图文和视频笔记的自动化发布
- 🖼️ **多样化图片支持**: 支持本地图片、网络URL
- ⏰ **定时任务**: 支持cron表达式的定时数据采集
- 📊 **数据采集**: 自动采集创作者中心仪表板、内容分析、粉丝数据
- 🧠 **AI数据分析**: 中文表头数据，AI可直接理解和分析
- 💾 **数据存储**: 支持csv本地存储（sql目前保留，暂不开发）
- 🎯 **统一接口**: 一个工具解决llm操作小红书自动化需求

## 📋 功能清单

### 登录
- [x] **登录** - 支持传统的命令行登录和通过与AI对话完成登录

### 内容发布
- [x] **图文发布** - 支持发布图文笔记
- [x] **视频发布** - 支持发布视频笔记
- [x] **话题标签** - 支持自动添加话题标签，提升内容曝光度
- [ ] **内容搜索** - 支持指定搜索（开发计划中）

### 数据采集 
- [x] **仪表板数据** - 采集账号概览数据（粉丝数、获赞数等）
- [x] **内容分析数据** - 采集笔记表现数据（浏览量、点赞数等）
- [x] **粉丝数据** - 采集粉丝增长和分析数据
- [x] **定时采集** - 支持cron表达式的自动定时采集
- [x] **数据存储** - CSV本地存储（默认）

## 📋 环境要求

### 🌐 浏览器环境
- **Google Chrome 浏览器** (最新版本推荐)
- **ChromeDriver** (版本必须与Chrome版本完全匹配)

### 🔍 查看Chrome版本
在Chrome浏览器中访问：`chrome://version/`

<!-- ![chrome版本](src/static/check_chrome_version.png) -->
![chrome版本](https://kayin-1253854796.cos.ap-shanghai.myqcloud.com/ownmedia/20250622022832077.png?imageSlim)

### 📥 ChromeDriver安装方式

#### 方法一：自动下载（推荐）
```bash
# 使用webdriver-manager自动管理
pip install webdriver-manager
```

#### 方法二：手动下载
1. 📋 访问官方下载页面：[Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/)
2. 🎯 选择与您Chrome版本完全匹配的ChromeDriver
3. 📁 下载后解压到合适位置（如 `/usr/local/bin/` 或 `C:\tools\`）
4. ⚙️ 在 `.env` 文件中配置正确路径

#### 方法三：包管理器安装
```bash
# macOS (Homebrew)
brew install --cask chromedriver

# Windows (Chocolatey)  
choco install chromedriver

# Linux (Ubuntu/Debian)
sudo apt-get install chromium-chromedriver
```

> ⚠️ **重要提示**：版本不匹配是最常见的问题原因，请确保ChromeDriver版本与Chrome浏览器版本完全一致！

### 🌐 远程浏览器连接

支持连接到已运行的远程Chrome实例，提高性能和支持远程部署场景。

#### 🔧 配置方法

在 `.env` 文件中添加以下配置：

```bash
# 启用远程浏览器连接
ENABLE_REMOTE_BROWSER=true
REMOTE_BROWSER_HOST=http://xx.xx.xx.xx
REMOTE_BROWSER_PORT=xxxx
```

#### 🚀 启动远程Chrome
- 如果报错没有权限，请检查 `./chrome-data` 目录是否存在切查看是否有读写权限，如果没有读写权限，请按照下面的步骤修复
  1. `docker run --rm selenium/standalone-chrome id seluser` 获取seluser的uid，例如返回 `uid=1200(seluser) gid=1200(seluser) groups=1200(seluser)`
  2. `sudo chown -R 1200:1200 ./chrome-data` 赋予seluser的读写权限，1200是seluser的uid
  3. 重新执行 `docker-compose up --force-recreate` 启动容器

```bash
version: '3.8'

services:
  selenium-chrome:
    image: selenium/standalone-chrome:latest
    container_name: selenium-chrome
    ports:
      - "54444:4444"
      - "57900:7900"
    shm_size: 2g
    environment:
      - SE_VNC_NO_PASSWORD=1
    volumes:
      - ./chrome-data:/home/seluser  # 更换挂载路径，确保权限
    restart: unless-stopped
    command: >
      bash -c "mkdir -p /home/seluser/.config/google-chrome &&
              touch /home/seluser/.config/google-chrome/test.txt &&
              /opt/bin/entry_point.sh"
```

#### 💡 使用场景

- **远程部署**：在服务器上运行Chrome，本地连接使用
- **性能优化**：复用已运行的Chrome实例，避免重复启动
- **开发调试**：连接到已登录的Chrome实例，保持会话状态
- **Docker环境**：在容器间共享Chrome实例

#### ⚠️ 注意事项

- 远程连接时不会启动新的Chrome实例
- 确保目标Chrome实例已开启远程调试功能
- 某些操作（如窗口大小调整）在远程模式下可能不支持

## 🚀 快速开始

### 💡 极简使用方式

```bash
# 克隆项目
git clone https://github.com/aki66938/xhs-toolkit.git
cd xhs-toolkit

# 运行（会自动安装依赖）
./xhs              # Mac/Linux
xhs.bat            # Windows

# 或使用 Python
python install_deps.py  # 安装依赖向导
./xhs                   # 启动程序
```

### 🎮 交互式菜单

运行 `./xhs` 后会显示友好的菜单界面：

```
╭─────────────────────────────────────────╮
│         小红书MCP工具包 v1.3.0           │
│           快速操作菜单系统                │
╰─────────────────────────────────────────╯

【主菜单】
1. 🔄 数据收集
2. 🌐 浏览器操作
3. 📊 数据管理
4. 🍪 Cookie管理
5. 🚀 MCP服务器
6. ⚙️  系统工具
0. 退出
```

### 🛠️ 从源码运行

#### 方法一：uv (推荐 ⚡)

```bash
# 克隆项目
git clone https://github.com/aki66938/xhs-toolkit.git
cd xhs-toolkit

# 使用uv安装依赖并运行
uv sync
uv run python xhs_toolkit.py status  ## 验证工具是否可用
```

> 💡 **uv使用提示**：文档中所有 `python` 命令都可以用 `uv run python` 替代，享受更快的依赖管理体验！

#### 方法二：pip (传统方式)

```bash
# 克隆项目
git clone https://github.com/aki66938/xhs-toolkit.git
cd xhs-toolkit

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
python xhs_toolkit.py status  ## 验证工具是否可用
```



## 🛠️ 使用指南

### 1. 创建配置文件

复制并编辑配置文件：

```bash
cp env_example .env
vim .env  # 编辑配置
```

**必需配置**：
```bash
# Chrome浏览器路径
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# ChromeDriver路径  
WEBDRIVER_CHROME_DRIVER="/opt/homebrew/bin/chromedriver"
```

### 2. 获取登录凭证

```bash
# 方式一：使用交互式菜单
./xhs
# 选择 4 -> Cookie管理 -> 1 -> 获取新的Cookies

# 方式二：直接命令
./xhs cookie save
```

在弹出的浏览器中, 如果是连接的远程浏览器，可以访问 http://ip:57900 访问vnc界面，然后执行下面的步骤：
1. 登录小红书创作者中心
2. 确保能正常访问创作者中心功能
3. 完成后按回车键保存

### 3. 启动MCP服务器

```bash
# 方式一：使用交互式菜单
./xhs
# 选择 5 -> MCP服务器 -> 1 -> 启动服务器

# 方式二：直接命令
./xhs server start
```

### 4. 客户端配置
**Claude Desktop**

#### 使用 uv（推荐）
在 `~/Library/Application Support/Claude/claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "xhs-toolkit": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/xhs-toolkit",
        "run",
        "python",
        "-m",
        "src.server.mcp_server",
        "--stdio"
      ]
    }
  }
}
```

#### 使用系统 Python
如果不使用 uv，可以配置为：

```json
{
  "mcpServers": {
    "xhs-toolkit": {
      "command": "python3",
      "args": [
        "-m",
        "src.server.mcp_server",
        "--stdio"
      ],
      "cwd": "/path/to/xhs-toolkit",
      "env": {
        "PYTHONPATH": "/path/to/xhs-toolkit"
      }
    }
  }
}
```

**注意**：
- 需要将 `/path/to/xhs-toolkit` 替换为实际的项目路径
- macOS 用户配置文件位置：`~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows 用户配置文件位置：`%APPDATA%\Claude\claude_desktop_config.json`
- 修改配置后需要重启 Claude Desktop

**cherry studio**

在MCP配置中添加

![Cherry Studio配置](https://kayin-1253854796.cos.ap-shanghai.myqcloud.com/ownmedia/20250622022940845.png?imageSlim)

**n8n**

在n8n的AI agent节点的tool中添加配置配置

![n8n的AI agent配置](https://kayin-1253854796.cos.ap-shanghai.myqcloud.com/ownmedia/20250622023033506.png?imageSlim)

## 🔧 主要功能

### MCP工具列表

| 工具名称 | 功能说明 | 参数 | 备注 |
|---------|----------|------|------|
| `test_connection` | 测试MCP连接 | 无 | 连接状态检查 |
| `smart_publish_note` | 发布小红书笔记 ⚡ | title, content, images, videos, tags, topics | 支持本地路径、网络URL、话题标签 |
| `check_task_status` | 检查发布任务状态 | task_id | 查看任务进度 |
| `get_task_result` | 获取已完成任务的结果 | task_id | 获取最终发布结果 |
| `login_xiaohongshu` | 智能登录小红书 | force_relogin, quick_mode | MCP专用无交互登录 |
| `get_creator_data_analysis` | 获取创作者数据用于分析 | 无 | AI数据分析专用 |



### 💬 AI对话式操作指南

通过与AI对话即可完成登录、发布、数据分析等操作，无需学习复杂命令。

#### 🔐 智能登录
```
用户："登录小红书"
```

**重要提示**：
- 🚨 首次使用请不要更改`headless`参数，获取到cookies后再更改为无头模式
- 🌐 AI调用登录工具后会拉起浏览器，首次登录需要手动输入验证码或扫码
- 🍪 成功后会自动保存cookies到本地，下次就免登录了

#### 📝 内容发布

**图文发布（本地图片）**：
```
请发布一篇小红书笔记，标题："今日分享"，内容："..."，图片路径："/User/me/xhs/poster.png"
```

**图文发布（网络图片）**：
```
请发布一篇小红书笔记，标题："美食分享"，内容："今天的美食"，使用这个网络图片：https://example.com/food.jpg
```


**视频发布**：
```
请发布一篇小红书视频，标题："今日vlog"，内容："..."，视频路径："/User/me/xhs/video.mp4"
```

**带话题标签发布**：
```
请发布一篇小红书笔记，标题："AI学习心得"，内容："今天学习了机器学习基础"，话题："AI，人工智能，学习心得"，图片："/path/to/image.jpg"
```


#### 📊 数据分析
```
请分析我的小红书账号数据，给出内容优化建议
```

#### 🔧 发布原理

手工上传过程中，浏览器会弹窗让用户选中文件路径，AI会将用户提供的路径参数传递给MCP工具，自动完成上传动作。

#### ⚡ 智能等待机制

- **📷 图片上传**：快速上传，无需等待
- **🎬 视频上传**：轮询检测上传进度，等待"上传成功"标识出现
- **⏱️ 超时保护**：最长等待2分钟，避免MCP调用超时 
- **📊 状态监控**：DEBUG模式显示视频文件大小和时长信息
- **🔄 高效轮询**：每2秒检查一次，精确文本匹配 

### 📊 数据采集与AI分析功能

自动采集小红书创作者数据，支持定时任务和AI智能分析。

#### 🧠 AI数据分析特性
- **中文表头**: CSV文件使用中文表头，AI可直接理解数据含义
- **智能分析**: 通过 `get_creator_data_analysis` MCP工具获取完整数据
- **数据驱动**: AI基于真实数据提供内容优化建议
- **趋势分析**: 分析账号表现趋势和粉丝增长情况


#### 采集的数据类型

1. **仪表板数据**: 粉丝数、获赞数、浏览量等账号概览数据
2. **内容分析数据**: 笔记表现数据，包括浏览量、点赞数、评论数等
3. **粉丝数据**: 粉丝增长趋势、粉丝画像分析等


#### 定时任务示例

采用cron语法，写入配置文件.env
```bash
# 每6小时采集一次
COLLECTION_SCHEDULE=0 */6 * * *

# 工作日上午9点采集
COLLECTION_SCHEDULE=0 9 * * 1-5

# 每月1号凌晨2点采集
COLLECTION_SCHEDULE=0 2 1 * *
```
### 🎯 手动操作工具

新增交互式菜单和手动操作工具，提供更便捷的操作体验：

#### 主要功能
- **🔄 数据收集**: 手动触发数据采集，支持选择数据类型和时间维度
- **🌐 浏览器操作**: 快速打开已登录的小红书各页面
- **📊 数据管理**: 导出Excel/JSON、分析数据趋势、备份恢复
- **🍪 Cookie管理**: 获取、查看、验证Cookies状态

#### 使用示例
```bash
# 启动交互式菜单
./xhs

# 或使用命令行
./xhs manual collect --type all      # 收集所有数据
./xhs manual browser --page publish  # 打开发布页面
./xhs manual export --format excel   # 导出Excel
./xhs manual analyze                 # 分析数据趋势
```

---
## 🚀 更新日志 - v1.3.0

### 🎯 重要功能更新

#### 🏷️ 话题标签自动化功能（完整实现）
- **全新话题自动化系统**：基于严谨的Playwright验证测试，实现真正有效的小红书话题标签添加
- **智能输入机制**：使用Actions类逐字符输入和JavaScript事件模拟，完美模拟真实用户操作
- **完整DOM验证**：支持检测`data-topic`属性和隐藏标识，确保话题获得平台流量推荐
- **多重备用方案**：多种输入方式和验证机制，提供99%+的成功率保障

#### 🔧 话题架构重构升级
- **术语统一**：全面从"标签"重构为"话题"，符合小红书平台术语
- **组件化设计**：新增`topic_automation.py`专用模块，提供基础和高级自动化功能
- **接口统一**：更新所有模型、接口和服务器代码，保持向后兼容性

#### 🧪 基于实测的关键修复
- **输入方式修复**：解决直接`send_keys`无法触发下拉菜单的问题
- **验证机制改进**：多层验证确保话题转换成功，包含完整的元数据检查
- **容错处理增强**：即使某个环节失败也有多个备用方案，确保功能稳定性

### 使用示例

```python
# 新的话题功能使用（MCP工具中自动支持）
smart_publish_note(
    title="AI学习心得",
    content="分享一些人工智能学习经验",
    topics=["AI", "人工智能", "学习心得"],  # 新增话题参数
    images=["image.jpg"]
)
```

### 技术细节
- **验证测试覆盖率**：基于3次严谨的Playwright验证测试
- **DOM结构适配**：完全适配小红书真实的话题标签DOM结构
- **性能优化**：智能等待机制和并发处理，提升自动化效率

### 测试效果

![1.3.0](https://kayin-1253854796.cos.ap-shanghai.myqcloud.com/ownmedia/20250628032152894.gif?imageSlim)

---

<details>
<summary>📜 点击查看 v1.2.5 更新日志</summary>
## 🚀 更新日志 - v1.2.5

### 新增功能

#### 🎮 交互式菜单系统
- 统一入口 `./xhs`，无需记忆复杂命令
- 数字选择菜单，操作更直观
- 实时状态显示，了解系统状态
- 支持Windows（xhs.bat）和Unix系统

#### 🛠️ 手动操作工具集
- **manual collect**: 手动数据收集，支持选择类型和维度
- **manual browser**: 打开已登录浏览器，快速访问各页面
- **manual export**: 导出数据为Excel或JSON格式
- **manual analyze**: 分析数据趋势，查看最佳笔记
- **manual backup/restore**: 数据备份和恢复功能

#### 🔧 改进的依赖管理
- 智能检测uv/pip环境
- 自动选择最佳Python环境
- 新增 `install_deps.py` 安装向导
- 同时支持uv和pip安装方式

### 优化改进
- 简化启动命令，统一使用 `./xhs`
- 改进Windows支持，提供bat和PowerShell脚本
- 优化代码结构，拆分模块避免单文件过大
- 增强错误处理和用户提示
</details>

---

<details>
<summary>📜 点击查看 v1.2.4 更新日志</summary>
## 🚀 更新日志 - v1.2.4

### 新增功能

#### 🌐 网络图片支持
- 支持 HTTP/HTTPS 图片链接直接发布
- 自动下载网络图片到本地临时目录
- 支持常见图片格式（jpg、png、gif、webp）

#### 📁 改进的图片处理
- 新增 `ImageProcessor` 模块统一处理各种图片输入
- 支持混合输入：`["local.jpg", "https://example.com/img.jpg"]`
- 更灵活的输入格式支持

### 使用示例

```python
# 网络图片
smart_publish_note(
    title="美食分享",
    content="今天的美食",
    images=["https://example.com/food.jpg"]
)

# 混合使用
smart_publish_note(
    title="旅行记录",
    content="风景很美",
    images=["/local/photo.jpg", "https://example.com/view.jpg"]
)
```

### 其他优化
- 改进文本处理，保留换行符
- 更新文档说明
</details>
---

<details>
<summary>📜 点击查看 v1.2.3 更新日志</summary>
## 🚀 更新日志 - v1.2.3

### 🔧 重要修复

#### 🖥️ 无头模式优化
- **修复无头模式失效问题**：增强Chrome无头模式配置，添加多重保险参数
- **优化浏览器启动逻辑**：使用`--headless=new`和`--headless`双重无头模式配置
- **优化配置验证**：确保所有模块都使用统一的HEADLESS配置，避免配置不一致问题

### 💡 细节
- 添加了`--disable-gpu-compositing`、`--disable-notifications`等多个Chrome参数
- 改进了MCP服务器启动时的异步初始化逻辑
- 增强了Windows环境下的兼容性和稳定性
</details>
---

<details>
<summary>📜 点击查看 v1.2.2 更新日志</summary>

## 🚀 更新日志 - v1.2.2

### 🆕 新增功能

#### 🔐 智能登录系统
- 新增自动化登录检测机制，支持MCP模式下的无交互登录
- 实现四重检测机制：URL状态、页面元素、身份验证、错误状态检测
- 添加智能等待机制，自动监测登录完成状态
- 优化cookies保存逻辑，区分交互模式和自动化模式

#### 🧠 智能路径解析系统
- 新增智能文件路径识别功能，支持多种输入格式自动解析
- 新增 `smart_parse_file_paths()` 函数，使用JSON解析、ast.literal_eval等多种解析方式
- 适配LLM对话场景和dify等平台的数组数据传递

**支持的输入格式**：
- 逗号分隔：`"a.jpg,b.jpg,c.jpg"`
- 数组字符串：`"[a.jpg,b.jpg,c.jpg]"`
- JSON数组：`'["a.jpg","b.jpg","c.jpg"]'`
- 真实数组：`["a.jpg", "b.jpg", "c.jpg"]`
- 混合格式：`"[a.jpg,'b.jpg',\"c.jpg\"]"`

#### 🛠️ 代码架构优化
- 重构登录相关模块，提升代码可维护性
- 优化异常处理机制，增强系统稳定性

### 🔧 修复功能

#### 📝 路径处理优化
- 解决用户反馈的多张图片上传格式识别问题
- 智能区分字符串和数组格式，避免数据类型判断错误
- 支持从不同平台（dify、LLM对话等）传递的各种数据格式
- 增强容错能力，即使格式不标准也能尽量解析

</details>

---


## 🚀 开发路线图

### 📋 待开发功能

#### 🔥 高优先级
- **🔐 无头模式登录** - 完善无头模式下的自动登录流程，提升自动化体验
 

#### 🔮 长期规划
- **🤖 AI创作声明** - 智能检测AI生成内容，自动添加创作声明标识
- **👥 多账号管理** - 支持多账号切换发布（遵循平台政策，单IP限制3个账号）
- **🌐 代理模式支持** - 配合多账号功能，支持代理网络访问
- **🐳 Docker容器化** - 提供容器化部署方案，便于多实例管理和部署
- **​🔍 内容审核机制** - 敏感词提醒或过滤

## 🔧 故障排除

### ChromeDriver常见问题

#### ❌ 问题：版本不匹配错误
```
selenium.common.exceptions.SessionNotCreatedException: session not created: This version of ChromeDriver only supports Chrome version XX
```

**✅ 解决方案**：
1. 🔍 检查Chrome版本：访问 `chrome://version/`
2. 📥 下载对应版本的ChromeDriver：[Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/)
3. ⚙️ 更新 `.env` 文件中的路径配置

#### ❌ 问题：ChromeDriver找不到
```
selenium.common.exceptions.WebDriverException: 'chromedriver' executable needs to be in PATH
```

**✅ 解决方案**：
1. 确认ChromeDriver已下载并解压
2. 方案A：将ChromeDriver添加到系统PATH
3. 方案B：在 `.env` 中配置完整路径：`WEBDRIVER_CHROME_DRIVER="/path/to/chromedriver"`
4. Linux/macOS: 确保文件有执行权限 `chmod +x chromedriver`

#### ❌ 问题：Chrome浏览器路径错误
```
selenium.common.exceptions.WebDriverException: unknown error: cannot find Chrome binary
```

**✅ 解决方案**：在 `.env` 文件中配置正确的Chrome路径
```bash
# macOS
CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Windows
CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"

# Linux
CHROME_PATH="/usr/bin/google-chrome"
```

### 其他常见问题

#### ❌ 问题：MCP连接失败
**✅ 解决方案**：
1. 确认服务器已启动：`python xhs_toolkit.py server start`
2. 检查端口8000是否被占用
3. 重启Claude Desktop或其他MCP客户端

#### ❌ 问题：登录失败
**✅ 解决方案**：
1. 清除旧的cookies：删除 `xhs_cookies.json` 文件
2. 重新获取cookies：`python xhs_toolkit.py cookie save`
3. 确保使用正确的小红书创作者中心账号

---

## 🙏 贡献者

感谢所有为项目做出贡献的人！

<a href="https://github.com/aki66938/xhs-toolkit/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=aki66938/xhs-toolkit" />
</a>

如果您也想为项目做出贡献，欢迎提交 Pull Request 或 Issue！

## 📄 许可证

本项目基于 [MIT许可证](LICENSE) 开源。

## 🔐 安全承诺

- ✅ **本地存储**: 所有数据仅保存在本地
- ✅ **开源透明**: 代码完全开源，可审计
- ✅ **用户控制**: 您完全控制自己的数据


<div align="center">
Made with ❤️ for content creators
</div> 

# xhs-toolkit (修复版)

这是 xhs-toolkit 的修复版本，解决了原版本中发布功能无法正常工作的问题。

## 🎯 主要改进

- ✅ 修复了发布按钮无法识别的问题
- ✅ 更新了编辑器选择器（支持 Tiptap）
- ✅ 添加了确认弹窗处理
- ✅ 增强了发布成功验证
- ✅ 提高了发布成功率

详细修复说明请查看 [FIXES.md](./FIXES.md)

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 下载 ChromeDriver

确保 ChromeDriver 版本与你的 Chrome 浏览器版本匹配。

```bash
# 查看 Chrome 版本
google-chrome --version  # Linux
# 或
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version  # macOS

# 下载对应版本的 ChromeDriver
# https://googlechromelabs.github.io/chrome-for-testing/
```

### 3. 配置环境变量

创建 `.env` 文件：

```bash
# Chrome 和 ChromeDriver 路径
XHS_CHROME_DRIVER_PATH=/path/to/chromedriver
XHS_CHROME_BINARY_PATH=/path/to/chrome  # 可选
XHS_CHROME_USER_DATA_DIR=./chrome_data

# Cookies 文件路径
XHS_COOKIES_FILE=./xhs_cookies.json

# 浏览器模式
XHS_HEADLESS=false  # 设置为 true 启用无头模式
```

### 4. 保存 Cookies

```bash
python xhs_toolkit.py cookie save
```

这会打开浏览器，请手动登录小红书创作者中心，然后按提示保存 cookies。

### 5. 发布笔记

```bash
python xhs_toolkit.py publish \
  "笔记标题" \
  "笔记内容" \
  --topics "话题1,话题2,话题3" \
  --images "/path/to/image1.jpg,/path/to/image2.jpg"
```

## 📖 使用示例

### 发布图文笔记

```bash
python xhs_toolkit.py publish \
  "OpenClaw - 你的AI助手" \
  "OpenClaw 是一个强大的 AI 助手和 IDE。

主要功能：
• 智能代码补全
• 自动化任务执行
• 多平台集成

让 AI 成为你的编程伙伴！🚀" \
  --topics "AI助手,开发工具,效率工具" \
  --images "/path/to/cover.png"
```

### 通过 MCP 集成

如果你使用 OpenClaw 或其他支持 MCP 的工具，可以这样配置：

```json
{
  "mcpServers": {
    "xhs-toolkit": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "src.server.mcp_server", "--stdio"],
      "cwd": "/path/to/xhs-toolkit",
      "env": {
        "PYTHONPATH": "/path/to/xhs-toolkit"
      }
    }
  }
}
```

## 🔧 命令行工具

### Cookie 管理

```bash
# 保存 cookies
python xhs_toolkit.py cookie save

# 查看 cookies 信息
python xhs_toolkit.py cookie show

# 验证 cookies
python xhs_toolkit.py cookie validate

# 测试 ChromeDriver 配置
python xhs_toolkit.py cookie test
```

### 配置管理

```bash
# 查看当前配置
python xhs_toolkit.py config show

# 验证配置
python xhs_toolkit.py config validate

# 生成配置示例
python xhs_toolkit.py config example
```

### 系统状态

```bash
# 查看系统状态
python xhs_toolkit.py status
```

## 🐛 常见问题

### 1. ChromeDriver 版本不匹配

**错误：** `This version of ChromeDriver only supports Chrome version XX`

**解决：** 下载与你的 Chrome 版本匹配的 ChromeDriver。

### 2. Cookies 失效

**错误：** `无法访问创作者中心`

**解决：** 重新保存 cookies：`python xhs_toolkit.py cookie save`

### 3. 发布失败

**可能原因：**
- 图片格式不支持（仅支持 JPG、PNG）
- 图片大小超限（建议 < 10MB）
- 内容包含敏感词
- 发布频率过高

**解决：** 检查图片和内容，适当降低发布频率。

## 📝 与原版的区别

| 功能 | 原版 | 修复版 |
|------|------|--------|
| 发布按钮识别 | ❌ 不准确 | ✅ 准确识别 |
| 编辑器支持 | ❌ 仅 Quill | ✅ Tiptap + Quill |
| 确认弹窗处理 | ❌ 未处理 | ✅ 自动处理 |
| 发布成功验证 | ❌ 不可靠 | ✅ 多重验证 |
| 页面滚动 | ❌ 无 | ✅ 自动滚动 |
| JavaScript 点击 | ❌ 普通点击 | ✅ JS 点击 |

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

如果你发现了新的问题或有改进建议，请：

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

## 📄 许可证

与原项目保持一致

## 🙏 致谢

- 原始项目：[xhs-toolkit](https://github.com/original/xhs-toolkit)
- 感谢所有贡献者

## 📮 联系方式

如有问题，请通过 Issue 联系。

# xhs-toolkit 修复说明

本仓库是对原始 xhs-toolkit 的修复版本，解决了发布功能无法正常工作的问题。

## 主要修复

### 1. 发布按钮识别问题

**问题：** 原代码使用的选择器 `[class*='publish']` 无法匹配小红书实际的发布按钮。

**修复：** 在 `src/xiaohongshu/client.py` 的 `_submit_note` 方法中：

```python
# 添加页面滚动
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

# 更新选择器优先级
publish_selectors = [
    "//button[contains(text(), '发布')]",  # 优先使用文本匹配
    ".custom-button.bg-red",  # 小红书特定的发布按钮样式
    ".publishBtn",
    "[class*='publish']",
    "button[type='submit']",
]

# 使用 JavaScript 点击
driver.execute_script("arguments[0].click();", submit_btn)
```

### 2. 编辑器选择器更新

**问题：** 小红书已从 Quill 编辑器升级到 Tiptap 编辑器，原选择器失效。

**修复：** 更新了多个文件中的编辑器选择器：

- `src/xiaohongshu/client.py`
- `src/xiaohongshu/constants.py`
- `src/xiaohongshu/components/content_filler.py`

```python
content_selectors = [
    "[contenteditable='true']",  # Tiptap 编辑器
    ".tiptap",
    ".ProseMirror",
    ".ql-editor",  # 保留旧版兼容
]
```

### 3. 确认弹窗处理

**问题：** 点击发布按钮后可能出现确认弹窗，原代码未处理。

**修复：** 添加了确认弹窗检测和处理逻辑：

```python
confirm_selectors = [
    "//button[contains(text(), '确认')]",
    "//button[contains(text(), '确定')]",
    "//div[contains(@class, 'modal')]//button[contains(text(), '确认')]",
    # ... 更多选择器
]

for selector in confirm_selectors:
    # 检测并点击确认按钮
    if confirm_btn.is_displayed() and confirm_btn.is_enabled():
        confirm_btn.click()
        break
```

### 4. 发布成功验证

**问题：** 原代码无法验证笔记是否真正发布成功。

**修复：** 添加了多重验证机制：

```python
# 1. 检查页面 URL 是否跳转到成功页面
if "publish/success" in driver.current_url:
    success = True

# 2. 检查页面上的成功提示
success_indicators = [
    "//div[contains(text(), '发布成功')]",
    "//span[contains(text(), '发布成���')]",
    # ...
]
```

## 测试结果

修复后的版本已通过多次测试：

- ✅ 图片上传成功
- ✅ 标题和内容填写正确
- ✅ 话题标签添加成功
- ✅ 发布按钮点击成功
- ✅ 页面跳转到成功页面
- ✅ 检测到"发布成功"提示

## 使用方法

```bash
# 安装依赖
pip install -r requirements.txt

# 保存 cookies
python xhs_toolkit.py cookie save

# 发布笔记
python xhs_toolkit.py publish \
  "标题" \
  "内容" \
  --topics "话题1,话题2" \
  --images "图片路径"
```

## 环境要求

- Python 3.10+
- Chrome 浏览器
- ChromeDriver（需与 Chrome 版本匹配）

## 已知问题

- 需要手动获取 cookies（通过浏览器登录）
- ChromeDriver 版本需要与 Chrome 版本严格匹配
- 发布频率过高可能触发小红书的限流

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

与原项目保持一致

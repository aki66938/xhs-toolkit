# 修复内容编辑器选择器以支持新版TipTap/ProseMirror编辑器

## 问题描述

在使用 `smart_publish_note` 工具发布笔记时，程序在"填写内容"步骤失败，错误信息：

```
❌ 任务执行失败: 填写内容失败: 无法找到内容输入框
```

### 原因分析

小红书创作者中心近期更新了内容编辑器：
- **旧版**: 使用 Quill Editor，选择器为 `.ql-editor`
- **新版**: 使用 TipTap/ProseMirror，选择器为 `.tiptap.ProseMirror`

原有代码中的选择器列表无法匹配新版编辑器。

## 修复内容

### 1. 更新内容编辑器选择器 (`src/xiaohongshu/client.py`)

```python
# 旧版选择器
content_selectors = [
    ".ql-editor",
    "[placeholder*='内容']",
    ...
]

# 新版选择器（优先使用TipTap）
content_selectors = [
    ".tiptap.ProseMirror",           # 新版TipTap编辑器
    ".ProseMirror",                   # ProseMirror编辑器
    ".tiptap",                        # TipTap容器
    "[contenteditable='true']",       # 任何可编辑元素
    ".ql-editor",                     # 旧版Quill编辑器（向后兼容）
    ...
]
```

### 2. 改进元素匹配逻辑

- 优先匹配 `contenteditable='true'` 的元素
- 使用 JavaScript (`innerHTML = ''`) 清空 contenteditable 元素
- 保留对旧版 Quill 编辑器的兼容

### 3. 修复浏览器配置路径问题 (`src/core/browser.py`)

- 移除硬编码的 `/home/seluser/google-chrome-data` 路径
- 使用系统临时目录创建用户数据目录，避免权限问题

## 测试结果

在本地环境测试通过：

```
✅ Image uploaded
✅ Title filled
✅ Found content editor: .tiptap.ProseMirror
✅ Content filled successfully!
```

## 相关信息

- 测试环境: Ubuntu 22.04 (WSL2), Python 3.13.5, Chrome
- 影响版本: v1.2.0 及更早版本
- 修复版本: 本 PR

## Checklist

- [x] 代码已测试
- [x] 向后兼容（保留旧版选择器）
- [x] 提交信息符合规范

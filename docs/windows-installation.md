# Windows 安装指南

## 已知问题

### uv 构建错误 ([Issue #7](https://github.com/aki66938/xhs-toolkit/issues/7))

在 Windows 上使用 `uv` 安装时可能遇到以下错误：

```
Failed to build `pydantic-core==2.33.2`
maturin failed: A python 3 interpreter on Linux or macOS must define abiflags in its sysconfig
```

这是由于 pydantic 2.11+ 版本依赖的 pydantic-core (2.33.2) 在 Windows 上通过 uv 构建时的兼容性问题。maturin 构建工具错误地期望 Windows Python 有 `sys.abiflags`（这是 Unix/Linux 特有的属性）。

## 解决方案

### 方案 1：使用 Windows 专用依赖文件（推荐）

使用专门为 Windows 准备的依赖文件，其中限制了 pydantic 版本：

```bash
# 使用 pip
pip install -r requirements-windows.txt

# 或使用 uv
uv pip install -r requirements-windows.txt
```

### 方案 2：使用预编译包

如果需要使用最新版本的 pydantic，可以：

1. 先安装预编译的 wheel 包：
```bash
pip install pydantic --only-binary :all:
```

2. 再安装项目：
```bash
pip install -e .
```

### 方案 3：使用 conda

使用 conda 可以避免构建问题：

```bash
conda create -n xhs python=3.10
conda activate xhs
conda install pydantic
pip install -e .
```

## ChromeDriver 配置

Windows 上的 ChromeDriver 配置示例：

```bash
# .env 文件
CHROME_PATH="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
WEBDRIVER_CHROME_DRIVER="C:\\tools\\chromedriver.exe"
```

## 其他注意事项

1. 确保 Python 版本 >= 3.10
2. 建议使用虚拟环境
3. ChromeDriver 版本需要与 Chrome 浏览器版本匹配
# 格子面积模型

一个基于 Tkinter 的小学数学面积模型工具。输入乘法算式后，程序会生成可视化格子图、分块面积和竖式计算，并用箭头把竖式中的部分积连接到对应区域。

## 功能

- 支持 `×`、`*`、`x`、`X` 作为乘号。
- 支持输入 `16×12`，自动按十位和个位拆分为格子区域。
- 支持带等号的分配律表达式，例如 `16×12=(10+6)×(10+2)`，并校验等式两边是否相等。
- 点击分组按钮可突出显示某一行，同时圈出对应的竖式部分积。
- 可将当前画布保存为 PNG 图片。

## 运行

项目使用 Python 3.10+，Tkinter 为 Python 标准库，图片保存功能需要 Pillow。

```powershell
python -m pip install -r requirements.txt
python area_grid_app.py
```

运行测试：

```powershell
python -m unittest -v
```

## 从源码构建 Windows 程序

仓库保留了工程原有的 `.spec` 打包配置。它们都指向当前 `area_grid_app.py`，不能用来还原历史版本源码。构建当前箭头直连版：

```powershell
python -m pip install -r requirements-dev.txt
pyinstaller --clean --noconfirm "格子面积模型-箭头直连版.spec"
```

生成的 `build/` 和 `dist/` 目录包含机器相关的打包缓存和生成文件，已被 `.gitignore` 排除。

## 版本

当前仓库版本：**1.0.0**（首次上传 GitHub，基于已有箭头直连版源码）。完整迭代记录见 [CHANGELOG.md](CHANGELOG.md)。

历史迭代根据工程内已有的打包产物名称和文件时间整理。历史源码快照不可用，因此只为当前源码创建版本标签。

## 使用范围

长和宽必须是正整数，最大为 200。保存 PNG 使用屏幕截取方式，请保持程序画布可见。当前主要面向 Windows；其他系统需要自行安装 Tk 支持，并验证字体和屏幕截取功能。

仓库不包含本机打包日志、可执行程序、缓存和临时截图。本次上传使用 GitHub 的匿名提交邮箱，避免公开本机 Git 配置里的个人邮箱。

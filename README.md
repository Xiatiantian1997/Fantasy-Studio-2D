# Fantasy Studio 2D｜幻真画室主程序

> **产品定位更新（2026-11-08）**：我们要做的是**自己的一套简洁中文本地创作软件**，以 ComfyUI 为生成引擎，以 [Fantasy Studio 3D](https://github.com/Xiatiantian1997/Fantasy-Studio-3D) 为未来人体姿势/结构模块。用户通过画风、人物、动作、素材等入口操作，不必直接接触节点图或 Blender 专业界面。
>
> **[软件产品方案](docs/product-plan.md)** · **[统一操作界面原型（HTML 源码）](prototypes/studio-shell.html)** · **[3D 对应仓库](https://github.com/Xiatiantian1997/Fantasy-Studio-3D)**
>
> ⚠️ **当前可运行代码仍是下面的本地画室 v1**。界面原型是独立文件，支持选项切换和导出配置，但还不具备实际生图、3D 查看和素材检索。**尚未提供独立 exe 安装包**；保留当前安装脚本和原有功能，先实机验证后逐步升级。

---

# 本地画室 v1｜Windows 2D 生图器

这是一个**简洁中文前端 + ComfyUI 本地 GPU 后端**的项目。专为动漫插画、真人写真和 COS 主题图设计，支持文生图、图生图、LoRA、常用尺寸和保存结果。

## 适用设备

- Windows 10/11 x64 + NVIDIA RTX 显卡，目标测试设备：**RTX 3060 Ti 8GB**。
- **优先解压到非 C 盘**，例如 `D:\AI\LocalStudio_v1`。程序会拒绝从 `C:\` 安装。
- 首次安装需要互联网；生成过程可以完全在本机进行。
- 需要预留约 **30 GB 起**的磁盘空间；下载程序/模型时还会有临时占用，实际用量随版本变化。

## 最简单的三步

1. 将整个 `LocalStudio_v1` 文件夹解压到 `D:\AI\` 或其它非 C 盘目录。
2. **双击 `01_安装.cmd`**：脚本从 ComfyUI 官方发行渠道下载 NVIDIA 便携版，再让你选择动漫模型 / 真人模型。两个模型各约 6.94 GB，安装过程中计算 SHA256 校验。
3. **双击 `02_启动.cmd`**：会打开浏览器访问 `http://127.0.0.1:7865`。不要关闭启动窗口；关闭后生成服务会停止。

想在以后追加另一种模型：双击 `03_添加模型.cmd`。已经校验正确的模型会自动跳过。

## 文件放在哪里？

```text
LocalStudio_v1/
├── 01_安装.cmd              安装环境和模型
├── 02_启动.cmd              打开画室
├── 03_添加模型.cmd          单独补模型
├── app/                     中文界面 / API 控制器
├── runtime/ComfyUI_windows_portable/
│   ├── ComfyUI/models/checkpoints/   大型绘图模型
│   └── ComfyUI/models/loras/         可选 LoRA
├── output/                  所有生成图片
├── input/                   ComfyUI 使用的上传素材
├── temp/                    生成过程的临时数据
├── cache/                   HuggingFace/PyTorch 缓存
└── downloads/               下载过程中的临时归档
```

不会主动安装系统级 Python，不会主动改 Windows 注册表或添加全局 PATH。`TEMP`、PyTorch、HuggingFace 等主要缓存会指向本文件夹；操作系统、浏览器或驱动仍可能在 C 盘产生少量系统级文件，无法保证绝对零写入。

## 初版功能

- **文生图**：主题提示词、负面提示词、图片尺寸、步数、CFG、种子。
- **参考图重绘（img2img）**：选择 JPG、PNG、WebP，控制改动幅度。上传文件保存在本机的 ComfyUI 输入目录中。
- **切换模型**：安装了两个模型后，切换“动漫插画 / 真人写真”会优先选择对应模型，也可以手动选择。
- **LoRA**：把 `.safetensors` LoRA 放进 `runtime/ComfyUI_windows_portable/ComfyUI/models/loras/`，启动后点击刷新。
- **保存**：结果在安装根目录的 `output/` 下，UI 也提供图片保存入口。
- **停止**：停止按钮向 ComfyUI 发送中断请求，当前步骤可能需要一点时间才能停止。

## 模型选择与来源

- **动漫**：Animagine XL 4.0（官方 Hugging Face 模型库）
  https://huggingface.co/cagliostrolab/animagine-xl-4.0
- **真人**：RealVisXL V5.0（官方 Hugging Face 模型库）
  https://huggingface.co/SG161222/RealVisXL_V5.0
- **后端**：ComfyUI Windows Portable NVIDIA
  https://github.com/Comfy-Org/ComfyUI
- **解压工具**：如系统没有 7-Zip，则脚本从 7-Zip 官方网站下载免安装的 `7zr.exe`。
  https://www.7-zip.org/download.html

模型由原作者分别授权；本安装包**不包含** ComfyUI 程序和模型权重。用户需要遵守各自的模型许可、使用限制和平台规则。

## 常见问题

**1. 网页显示“后端启动中”**

首次启动要加载 PyTorch，等后端启动后点“刷新”。如果持续失败，看启动窗口中 ComfyUI 的错误日志、显卡驱动、系统可用内存。

**2. 下载失败 / 网络连接不到 Hugging Face**

再次运行安装程序尝试续传，或使用官方模型页面手动下载相同文件，放入 `checkpoints` 文件夹后重新打开。不要从未知第三方链接下载安装程序或权重。

**3. 显存不足 / 生成时间长**

初版已启用 ComfyUI `--lowvram` 模式，优先减少显存不足的情况。先尝试 `768 × 1152` 或 `1152 × 768`。同时关闭游戏和其它 GPU 应用。

**4. 能从手机/平板操作吗？**

初版为了安全，**只监听电脑自身的 `127.0.0.1`**，不能直接从平板打开。后续可以增加带认证的局域网模式；不要把没有身份验证的 ComfyUI 或本地画室直接暴露到公网。

**5. “局部重绘”在哪里？**

v1 仅实现整图的 img2img，还没有画笔蒙版、局部 inpaint、姿势约束和自动修脸。这些应当作为后续功能，不能把整图重绘当成已经实现了精准局部修改。

## 技术说明

UI 使用原生 HTML/CSS/JS，后端桥接使用 Python 标准库，不额外安装 Web 框架或 Node.js。启动器默认 ComfyUI 为 `127.0.0.1:8190`，画室为 `127.0.0.1:7865`。生成图通过 ComfyUI 官方核心节点 API 发送，节点关系可在 `app/workflows.py` 检查。

**验证状态**：代码已在当前环境下进行 Python 单元测试和 Mock API 测试，但这里没有你的 NVIDIA 显卡，无法代替 Windows + RTX 3060 Ti 上的真实安装与出图验收。

> 当前 GitHub 首版以项目源码包形式保存，运行前请阅读安装说明。
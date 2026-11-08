# 幻真画室｜Fantasy Studio

**只做一套自己的本地创作软件。** 没有需要用户选择的旧版、新版，也不用重复安装。原有功能直接保留，未来功能直接合入同一入口。

## 一个软件，两个内部技术仓库

| 模块 | GitHub | 用途 |
| --- | --- | --- |
| 主程序 / 唯一用户入口 | [Fantasy-Studio-2D](https://github.com/Xiatiantian1997/Fantasy-Studio-2D) | 中文界面、2D 生图、画风、素材、作品 |
| 3D 人体支持模块 | [Fantasy-Studio-3D](https://github.com/Xiatiantian1997/Fantasy-Studio-3D) | Blender 人体、姿势与导出 |
| 独立人脸研究（不属于另一版本） | [body](https://github.com/Xiatiantian1997/body) | 保留人脸结构研究 |

用户只打开「幻真画室」。ComfyUI 和 Blender 是内部引擎，不必自己操作节点图、骨骼权重和专业建模界面。

## 当前功能状态

- **已写入源代码**：中文界面、文生图、整图 img2img、Checkpoint/LoRA 选择、种子、尺寸、采样设置、停止与保存结果。
- **已合并入主界面**：2D 绘画、3D 人体、素材库、作品四个导航入口。其中 2D 保留已有功能，其他入口明确标注规划中。
- **尚未完成**：可重复的三套画风配方、ControlNet 姿势控制、精确局部重绘、素材数据库、图生文、AI 自主审图、可操作的 3D 模型与桌面 exe。
- **验证限制**：曾做过 Python 单元测试及模拟 API 测试，但未在你的 Windows RTX 3060 Ti 上完成 GPU 实机安装/出图验收。统一导航也待实际浏览器验收。

不把设计稿、演示 HTML 或技术接口称为实际完成的功能。

## 安装与启动（同一套程序）

适用 Windows 10/11 x64 + NVIDIA RTX，目标 RTX 3060 Ti 8GB。放在非 C 盘，例如 D:\AI\FantasyStudio\studio-2d。

1. 双击 01_安装.cmd：从官方渠道下载 ComfyUI 便携环境，并选择基础模型。
2. 双击 02_启动.cmd：浏览器打开 http://127.0.0.1:7865 ，进入幻真画室。
3. 要添加模型时双击 03_添加模型.cmd。

首次安装需要联网；运行需要预留至少约 30 GB 磁盘空间，未来模型和素材库会额外占空间。安装器禁止将项目直接安装到 C 盘；浏览器与 Windows 仍可能在 C 盘产生系统缓存。

现有安装器、启动器和后端保持兼容，不需要另外安装所谓“旧版本”。

## 项目数据存放

建议非 C 盘统一放在 D:\AI\FantasyStudio：
- studio-2d：主程序，包含 app、runtime、input、output、temp、cache、downloads。
- studio-3d：后续 Blender 姿势与模型模块。
- materials：完整原始图、精选参考与分级私人资料。
- exports：后续 3D 输出的结构控制包。

大型模型、私人原图、敏感人体资料不提交公开 GitHub。默认只监听 127.0.0.1，不要把无认证的本地服务暴露到公网。

## 三种画风目标

- 幻真动漫：漂亮的 2D 动漫脸、立体渐变、精致线条。
- 半写实插画：自然体积和光影，但保留插画美感。
- 数字油画：真实笔触层次、色块和虚实关系，而不是照片滤镜。

当前只有基础 Checkpoint/LoRA 选择；三种画风仍需要在 GPU 上实际挑选模型和测试稳定配方。真人写真可作为后期实验，不妨碍当前主要的 2D 目标。

## 统一实施顺序

先让现有程序在用户电脑上稳定生成 → 验证三画风 → 素材检索与局部修改 → 接入已验证的 3D 姿势导出 → 作品与人物一致性 → 有必要时再封装 Windows exe。

**真实运行界面始终是 app/web/index.html。** prototypes/studio-shell.html 仅保存早期设计示意，不是另一套软件，也不是第二个安装包。

详细方案：[统一产品设计](docs/product-plan.md) ｜ [3D 模块](https://github.com/Xiatiantian1997/Fantasy-Studio-3D)

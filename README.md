# 幻真画室｜2D 绘画模块

> **这是「幻真画室」的 2D 技术仓库，不再承担整个软件的总控职责。** 总体界面、统一启动、素材索引、作品历史和 2D/3D 交接归属 [Fantasy-Studio 总控](https://github.com/Xiatiantian1997/Fantasy-Studio-)；3D 建模归属 [Fantasy-Studio-3D](https://github.com/Xiatiantian1997/Fantasy-Studio-3D)。

用户最终只有一套「幻真画室」。**两个技术模块独立开发，不等于两套产品或两个版本。**

## 本仓库专门负责什么

- ComfyUI 生成任务与模型管理，checkpoint / LoRA / 提示词 / 参数 / 采样；
- 文生图、图生图、后续精准局部重绘与姿势控制；
- **幻真动漫、半写实插画、数字油画**三种真正经模型验证的画风配方；
- 读取总控提供的允许访问的素材引用；
- 将 3D 控制包映射到与当前 checkpoint 匹配的 ControlNet 工作流；
- 把生成的图片、种子和实际工作流元数据回传给总控。

**不负责**：管理全局收藏与私人资料、制作可编辑人体网格、代替 Blender 控制骨骼、维护总体软件导航。

## 已写代码与未完成

| 部分 | 状态 |
| --- | --- |
| Python 后端、HTML 开发界面、ComfyUI 连接 | 已编写 |
| 文生图、整图 img2img、单 LoRA、结果预览保存、停止 | 已编写 |
| 独立开发测试用安装器与启动器 | 已编写 |
| 三种风格稳定配方 | 尚未在真实模型上验证 |
| ControlNet 深度/法线/姿势输入 | 尚未实现 |
| 精准 inpaint、图生文、批量审图 | 尚未实现或需另行集成 |
| 用户 Windows RTX 3060 Ti 实机生成验收 | **尚未完成** |

“已编写代码”不等于在用户电脑上运行成功。

## 目前怎样测试 2D

在 **Windows 10/11、NVIDIA RTX（目标 RTX 3060 Ti 8GB）** 上，将仓库复制到非 C 盘，例如 `D:\AI\FantasyStudio\studio-2d`。

- `01_安装.cmd`：下载 ComfyUI NVIDIA 便携版与所选模型；
- `02_启动.cmd`：启动 2D 开发服务并在浏览器打开 `http://127.0.0.1:7865`；
- `03_添加模型.cmd`：补充模型。

默认 ComfyUI `127.0.0.1:8190`；避免把未经认证的服务开放到公网。首次安装需要联网，项目及缓存优先留在非 C 盘。模型/贴图/私有素材不存到公开 GitHub。

**这套脚本是现有 2D 功能的开发与回归测试入口，先保留。** 待总控入口实际连接成功且通过测试后，再决定怎样迁移；不会让用户维护“旧版/新版”。

目前 `app/web/index.html` 中曾加入的 3D/素材/作品导航只是早期 UI 过渡页面，并未真正实现这些模块。**今后正式统一界面以总控仓库为唯一设计来源**；`prototypes/studio-shell.html` 为保留的历史草稿，不继续作为权威设计稿。

## 与其他模块交接

- 现有本地 API：`GET /api/status`、`GET /api/models`、`POST /api/upload`、`POST /api/generate`、`GET /api/job?id=...`、`POST /api/interrupt`。
- 未来 3D 接口采用 [Fantasy-Studio-3D 的导出规范](https://github.com/Xiatiantian1997/Fantasy-Studio-3D/blob/main/docs/interface-v0.1.md) 产生的控制包；2D 消费并转换为 ControlNet 实际输入。
- 主控负责跨模块状态/任务追踪、素材权限、作品版本与单一用户入口。

详细职责见 [总控职责规范](https://github.com/Xiatiantian1997/Fantasy-Studio-/blob/main/docs/responsibilities.md)（总控目前为私人仓库，需拥有相应访问权限）。

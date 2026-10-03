# Minecraft 粒子图片函数包生成器

本程序由Copilot-GPT3.5协助开发，如有问题请提交Issue！
Windows 桌面程序：将 PNG、GIF 和 APNG 转成 Minecraft Java Edition Datapack ZIP。界面使用 PySide6；动画解析、粒子模拟、性能预设、风险预测、版本命令和 ZIP 构建分别位于独立模块。

## 项目架构

```text
ParticleGenerator/
├── main.py                         # QApplication 入口
├── app_info.py                     # 软件名称和版本号
├── build.py                        # 自动生成图标并构建独立 EXE
├── ui/
│   ├── main_window.py              # 图片导入、参数设置和导出界面
│   └── preview.py                  # 独立图片预览和粒子模拟组件
├── core/
│   ├── image_parser.py             # PNG/GIF/APNG 读取、缩放和透明像素过滤
│   ├── particle_model.py           # local-space 粒子和 Pivot 数据模型
│   ├── transform.py                # 缩放、旋转、执行位置偏移流水线
│   ├── rotation.py                 # Euler 旋转数学
│   ├── coordinate_system.py        # 世界/执行者/玩家朝向坐标转换
│   ├── renderer.py                 # 模型到 Minecraft 函数命令的渲染
│   ├── particle_generator.py       # 兼容旧调用的模型生成入口
│   ├── datapack_builder.py         # pack.mcmeta、函数文件和 ZIP
│   ├── performance.py              # 低/中/高分辨率和资源预算
│   └── prediction.py               # 命令数、文件大小和执行风险预测
│   ├── app_config.py               # AppData 用户配置
│   ├── app_logging.py              # 轮转错误日志
│   └── resource_paths.py           # 源码/打包资源路径检查
├── version/
│   ├── base.py                     # 版本适配器接口
│   ├── registry.py                 # 支持版本注册表
│   ├── mc1204.py                   # 1.20.4 命令语法及元数据
│   ├── mc1205.py                   # 1.20.5/1.20.6 适配器
│   └── mc121x.py                   # 1.21.x 适配器
├── minecraft/
│   ├── mc1204_renderer.py          # 1.20.4 粒子语法
│   └── mc1205_renderer.py          # 1.20.5+ 粒子语法
├── editor/
│   ├── viewport.py                 # 可旋转/平移/缩放的 3D 模型视图
│   ├── camera.py                   # 轨道相机
│   └── gizmo.py                    # XYZ 坐标 Gizmo
├── resources/
│   └── app_icon.ico                # 构建脚本生成并嵌入的程序图标
├── build/
│   └── ParticleGenerator.spec      # PyInstaller 单文件配置
└── requirements.txt
```

处理过程为：`图片 → ParsedImage → ParticleModel（局部坐标）→ 可视化编辑 → Transform → MinecraftRenderer → DatapackBuilder → ZIP`。图片左下角是默认 Pivot，向右为 +X、向上为 +Y。模型本身不保存 Minecraft 命令；只有预测/导出时才由版本渲染器生成函数文本。添加新版本时，在 `version/` 注册元数据适配器，并在 `minecraft/` 注册对应命令渲染器。

## 本地运行

普通用户直接运行 `build\dist\ParticleGenerator.exe`，无需安装 Python。开发者仅在构建机器上需要 Windows 10/11 和 Python 3.10 或更新版本：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

## 一键打包独立 EXE

PyInstaller 不支持从其他操作系统交叉构建 Windows EXE。在 Windows 构建机完成依赖安装后执行：

```powershell
python build.py
```

脚本会自动生成应用图标，再按 PyInstaller spec 构建单文件 GUI 程序；软件版本为 **1.3.0**。生成物位于 `build\dist\ParticleGenerator.exe`。PySide6、Pillow 和图标会随程序打包，目标电脑无需安装 Python 或其他运行环境。第一次启动可能需要稍候解压运行时文件。

用户配置保存在 `%APPDATA%\Minecraft Particle Image Generator\config.json`；滚动日志保存在 `%LOCALAPPDATA%\Minecraft Particle Image Generator\logs\application.log`。

## 当前支持范围

- Datapack：Minecraft Java Edition 1.20.4、1.20.5、1.20.6，以及 1.21 至 1.21.11 的已登记版本；所有支持版本均使用 `function/` 目录，1.21.9 及以上使用 `min_format`/`max_format` 元数据。
- 粒子：`minecraft:dust`、`minecraft:flame`、`minecraft:cloud`、`minecraft:end_rod`
- 透明度为 0 的像素会忽略；非零 Alpha 均作为可见像素。非 Dust 粒子不具备逐像素 RGB 颜色；Dust 大小范围为 0.01–4。
- 所有支持版本的函数路径均为 `data/<namespace>/function/<name>.mcfunction`。
- 3D 视口支持左键旋转、右键/中键平移和滚轮缩放，并显示网格、XYZ 轴与 Pivot；变换、粒子大小、Alpha、Pivot 和朝向模式均可在界面编辑。
- 朝向模式包括固定世界方向、继承函数执行者方向、继承最近玩家视角。前两种无需 `with block`；模型位置使用执行上下文的相对坐标，视角模式通过 `execute rotated as @p` 覆盖方向。
- 局部点经过 Pivot、XYZ 缩放、Euler XYZ 旋转和执行位置偏移后，渲染为 Minecraft `~` 或 `^` 坐标；普通函数调用位置就是默认左下角 Pivot 的锚点。
- 动画播放使用临时实体标签保持启动者执行位置/朝向；从玩家执行 start/stop 函数。Dust 等粒子命令不支持逐粒子 Alpha 或 Sprite 旋转，Alpha 用于模型预览与隐藏完全透明粒子。
- 对静态模型，执行 `/function <namespace>:<name>` 时，当前函数执行位置就是所选 Pivot 锚点；左下角 Pivot 是默认值。需要明确指定玩家执行上下文时，可用 `/execute as @p at @s run function <namespace>:<name>`。不要使用 `with block` 定位；它只用于给宏函数传方块 NBT 数据。
- 低性能模式将图像缩至最多 128×128 并使用区域像素合并；中性能模式最多 500,000 像素；高性能模式最多 1,000,000 像素。动画最多 120 帧，并设置总像素预算以控制内存。
- 动画帧自动按 GIF/APNG 时长循环。生成后运行 `/function <namespace>:<name>/animation/start` 开始播放，运行 `/function <namespace>:<name>/animation/stop` 停止播放。
- 执行风险以单帧命令数和函数文本大小估算；高风险导出会要求确认。粒子模拟是用于布局/色彩预览的近似渲染，并非游戏客户端截图。

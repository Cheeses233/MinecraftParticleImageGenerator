[English](README.md) | [简体中文](README_CN.md)

# Minecraft Particle Image Generator

[![GitHub Stars](https://img.shields.io/github/stars/Cheeses233/MinecraftParticleImageGenerator?style=flat-square)](https://github.com/Cheeses233/MinecraftParticleImageGenerator/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/Cheeses233/MinecraftParticleImageGenerator?style=flat-square)](https://github.com/Cheeses233/MinecraftParticleImageGenerator/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/Cheeses233/MinecraftParticleImageGenerator?style=flat-square)](https://github.com/Cheeses233/MinecraftParticleImageGenerator/issues)
[![GitHub Releases](https://img.shields.io/github/v/release/Cheeses233/MinecraftParticleImageGenerator?style=flat-square)](https://github.com/Cheeses233/MinecraftParticleImageGenerator/releases)

**A Minecraft Java Edition particle image datapack generator.**

Convert PNG, GIF, and APNG images into Minecraft Java Edition Datapack ZIP files.

The application is built as a Windows desktop application using **PySide6**.  
Image parsing, particle simulation, performance presets, risk prediction, Minecraft version adapters, and Datapack generation are separated into independent modules.

If you encounter any problems, please submit an Issue!

---

## 🔗 Project Links

| Resource | Link |
|-|-|
| ⭐ Star this project | https://github.com/Cheeses233/MinecraftParticleImageGenerator |
| 🍴 Fork this project | https://github.com/Cheeses233/MinecraftParticleImageGenerator/fork |
| 🐛 Report an Issue | https://github.com/Cheeses233/MinecraftParticleImageGenerator/issues |
| 📦 Releases | https://github.com/Cheeses233/MinecraftParticleImageGenerator/releases |

---

# ✨ Features

## Image to Minecraft Particle Model

The processing pipeline:

```

Image
↓
ParsedImage
↓
ParticleModel (Local Space)
↓
Visual Editing
↓
Transform
↓
Minecraft Renderer
↓
Datapack Builder
↓
ZIP Package

```

Unlike traditional pixel-to-command converters, this project uses a **particle model workflow**.

The particle model itself does not store Minecraft commands.

Commands are generated only during export through version-specific renderers.

---

# 🏗️ Project Architecture

```

ParticleGenerator/
├── main.py                         # QApplication entry point
├── app_info.py                     # Application name and version
├── build.py                        # Generate icon and build standalone EXE
│
├── ui/
│   ├── main_window.py              # Image import, settings and export UI
│   └── preview.py                  # Image preview and particle simulation
│
├── core/
│   ├── image_parser.py             # PNG/GIF/APNG loading and processing
│   ├── particle_model.py           # Local-space particle model and Pivot system
│   ├── transform.py                # Scale, rotation and position pipeline
│   ├── rotation.py                 # Euler rotation mathematics
│   ├── coordinate_system.py        # World/executor/player coordinate conversion
│   ├── renderer.py                 # Particle model renderer
│   ├── particle_generator.py       # Legacy-compatible generation entry
│   ├── datapack_builder.py         # Datapack and ZIP generation
│   ├── performance.py              # Performance presets and budgets
│   ├── prediction.py               # Command/file size prediction
│   ├── app_config.py               # User configuration
│   ├── app_logging.py              # Rotating application logs
│   └── resource_paths.py           # Resource path handling
│
├── version/
│   ├── base.py                     # Version adapter interface
│   ├── registry.py                 # Version registry
│   ├── mc1204.py                   # Minecraft 1.20.4 adapter
│   ├── mc1205.py                   # Minecraft 1.20.5/1.20.6 adapter
│   └── mc121x.py                   # Minecraft 1.21.x adapter
│
├── minecraft/
│   ├── mc1204_renderer.py          # 1.20.4 particle syntax
│   └── mc1205_renderer.py          # 1.20.5+ particle syntax
│
├── editor/
│   ├── viewport.py                 # 3D particle model viewport
│   ├── camera.py                   # Orbit camera
│   └── gizmo.py                    # XYZ transformation gizmo
│
├── resources/
│   └── app_icon.ico
│
├── build/
│   └── ParticleGenerator.spec
│
└── requirements.txt

```

---

# 🎨 Particle Model System

## Local Coordinate System

All particles are stored using local coordinates.

The model does **not** store Minecraft world coordinates.

Default coordinate system:

```

```
      +Y

      ↑
```

-X  ←   Pivot   → +X

```
      +Z
```

```

The default Pivot is:

```

Bottom-left corner of the image

```

The bottom-left pixel is always treated as the origin point.

---

# 🧩 Visual Editing System

The editor works similarly to BlockBench.

Supported editing:

## Transform

- Position offset
- X/Y/Z rotation
- X/Y/Z scale

## Particle Properties

- Particle size
- Alpha
- Color
- Pivot position
- Facing mode

## 3D Viewport

Supports:

- Left mouse button: rotate camera
- Right/middle mouse button: move camera
- Mouse wheel: zoom

Displays:

- Grid
- XYZ axis
- Pivot point
- Particle model preview

---

# 🧭 Minecraft Coordinate Conversion

The transformation pipeline:

```

Particle Local Space

↓

Pivot Transform

↓

Scale

↓

Euler Rotation

↓

Executor Position

↓

Minecraft World Position

````

This allows:

- Moving the model
- Rotating the model
- Scaling the model
- Following executor direction

---

# 👁️ Facing Modes

Supported modes:

## Fixed World Direction

The particle image keeps the same world orientation.

---

## Executor Direction

The model follows the function executor's rotation.

Example:

```mcfunction
execute as @p at @s run function namespace:name
````

---

## Player View Direction

The model follows the nearest player's viewing direction.

Implemented using:

```mcfunction
execute rotated as @p
```

---

# 📦 Datapack Output

Generated datapack structure:

```
ParticlePack
│
├── pack.mcmeta
│
└── data
    └── namespace
        └── function
            ├── load.mcfunction
            └── draw.mcfunction
```

All supported versions use:

```
data/<namespace>/function/
```

---

# 🎮 Supported Minecraft Versions

Currently supported:

* Minecraft Java Edition 1.20.4
* Minecraft Java Edition 1.20.5
* Minecraft Java Edition 1.20.6
* Minecraft Java Edition 1.21.x
* Minecraft Java Edition 1.21.11 registered versions

Version support is handled through adapters.

Adding a new Minecraft version only requires:

```
version/
minecraft/
```

adapter implementation.

---

# ✨ Supported Particles

Current particles:

* `minecraft:dust`
* `minecraft:flame`
* `minecraft:cloud`
* `minecraft:end_rod`

Notes:

* Transparent pixels are ignored.
* Dust supports RGB colors.
* Non-Dust particles cannot display per-pixel RGB colors.
* Dust size range:

```
0.01 - 4
```

---

# 🎞️ Animation Support

Supported:

* GIF
* APNG

Features:

* Frame extraction
* Frame timing
* Loop playback
* Animation function generation

Start animation:

```mcfunction
/function <namespace>:<name>/animation/start
```

Stop animation:

```mcfunction
/function <namespace>:<name>/animation/stop
```

---

# ⚙️ Performance Optimization

Three performance modes:

## Low Performance Mode

* Maximum resolution: 128×128
* Pixel merging enabled

Recommended for servers.

---

## Balanced Mode

* Maximum 500,000 pixels

Default mode.

---

## High Quality Mode

* Maximum 1,000,000 pixels

Maximum visual quality.

---

# 📊 Risk Prediction

Before exporting, the program estimates:

* Particle count
* Function file size
* Execution risk

High-risk exports require confirmation.

The prediction is based on:

* Command count
* Generated file size
* Frame complexity

---

# 🖥️ Running Locally

## Requirements

Developers need:

* Windows 10/11
* Python 3.10+

Create environment:

```powershell
py -3 -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt

python main.py
```

---

# 📦 Build Standalone EXE

Windows EXE must be built on Windows.

Run:

```powershell
python build.py
```

The build script will:

* Generate application icon
* Run PyInstaller
* Package dependencies
* Create standalone GUI application

Output:

```
build\dist\ParticleGenerator.exe
```

The final application does not require:

* Python
* Python packages
* Additional runtime installation

---

# 📁 User Data

Configuration:

```
%APPDATA%\Minecraft Particle Image Generator\config.json
```

Logs:

```
%LOCALAPPDATA%\Minecraft Particle Image Generator\logs\application.log
```

---

# 🗺️ Roadmap

## v1.4.x

Planned:

* More particle types
* Improved optimization
* Better preview rendering

---

## Future Versions

Planned:

* Advanced BlockBench-style editor
* More animation tools
* Particle effect templates
* Skill effect creation
* RPG-style particle systems

---

# 🤝 Contributing

Contributions are welcome!

You can:

* Submit Issues
* Create Forks
* Submit Pull Requests
* Share suggestions

---

# 📜 License

License: TBD

---

# ❤️ Acknowledgements

Thanks to:

* Minecraft Datapack creators
* Particle effect creators
* Test users
* Everyone who provides feedback

Create images.
Bring them into Minecraft.

这样更符合国际开源项目习惯。

# Aura Color Picker

A minimal screen color picker widget for **KDE Plasma 6**, inspired by Hyprpicker.
Click the widget, the screen freezes, a magnifier lens follows your cursor, click again and the color is copied to your clipboard with a notification.

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Plasma 6](https://img.shields.io/badge/KDE%20Plasma-6.0%2B-1d99f3)

## Features

- Frozen-screen picking with a circular pixel-grid magnifier
- Live HEX preview next to the cursor
- Scroll wheel to change zoom
- Copies to clipboard and shows a notification with a color swatch
- Multiple output formats (configurable):

| Format | Example |
|---|---|
| HEX | `#1E66F5` |
| HEX Raw | `1E66F5` |
| RGB | `rgb(30, 102, 245)` |
| RGBA | `rgba(30, 102, 245, 1.0)` |
| QML | `Qt.rgba(0.12, 0.40, 0.96, 1.0)` |
| Raw values | `30, 102, 245` |

## Controls

| Action | Result |
|---|---|
| Left click | Pick color |
| Right click / `Esc` | Cancel |
| Mouse wheel | Zoom in / out |

## Requirements

- KDE Plasma **6.0+**
- `python3`
- `spectacle` (screen capture)
- `g++` and Qt6 development headers (the lens is compiled once on first run and cached)
  - Arch: `qt6-base`
  - Debian/Ubuntu: `qt6-base-dev`, `build-essential`, `pkg-config`
  - Fedora: `qt6-qtbase-devel`, `gcc-c++`, `pkgconf`
- Clipboard: `wl-clipboard` (recommended on Wayland), or `xclip`, or Klipper (fallback)
- `libnotify` (`notify-send`) for notifications

## Installation

```bash
git clone https://github.com/ahmed-x86/aura_color_picker.git
cd aura_color_picker
kpackagetool6 -t Plasma/Applet -i .
```

To update an existing install:

```bash
kpackagetool6 -t Plasma/Applet -u .
```

Then right click your panel or desktop, choose **Add Widgets**, and search for **Aura Color Picker**.
If it does not show up, restart the shell: `plasmashell --replace &`

To uninstall:

```bash
kpackagetool6 -t Plasma/Applet -r com.ahmedx86.auracolorpicker
```

## Configuration

Right click the widget, **Configure Aura Color Picker**, then choose the color format.

## Troubleshooting

Run the backend directly to see what is failing:

```bash
python3 contents/scripts/hypr_lens.py 0
```

- **First click takes a few seconds**: the lens is being compiled. This happens once.
- **Build failed notification**: install the Qt6 dev packages above. The compiler output is in `~/.cache/auracolorpicker/build.log`.
- **Nothing is copied**: install `wl-clipboard`.

## Project structure

```
aura_color_picker/
├── contents
│   ├── config      # widget settings schema and config pages
│   ├── scripts     # hypr_lens.py: screenshot, lens, clipboard, notification
│   └── ui          # QML: widget, backend, icon
├── LICENSE
└── metadata.json
```

## License

Copyright (C) 2026 ahmed-x86

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

See [LICENSE](LICENSE) for the full text.

#!/usr/bin/env python3
"""Aura Color Picker backend: freeze screen -> lens picker -> clipboard + notification.

Usage: hypr_lens.py [format_index]
Log of any build failure: ~/.cache/auracolorpicker/build.log
"""
import hashlib
import os
import shutil
import subprocess
import sys

CPP_CODE = r"""
#include <QApplication>
#include <QGuiApplication>
#include <QScreen>
#include <QWidget>
#include <QPixmap>
#include <QImage>
#include <QPainter>
#include <QPainterPath>
#include <QMouseEvent>
#include <QWheelEvent>
#include <QKeyEvent>
#include <QCursor>
#include <QPoint>
#include <QRectF>
#include <QColor>
#include <QPen>
#include <QFont>
#include <iostream>

// NOTE: no Q_OBJECT here on purpose. Q_OBJECT needs moc, and we compile with plain g++.
class LensWidget : public QWidget {
    QPixmap pixmap;
    QImage img;
    QPoint cursorPos;
    int zoom;
    int gridCount;
    int lensRadius;

public:
    explicit LensWidget(const QImage &image) : img(image) {
        pixmap = QPixmap::fromImage(img);
        zoom = 10;
        gridCount = 15;
        lensRadius = (gridCount * zoom) / 2;

        setWindowFlags(Qt::FramelessWindowHint | Qt::WindowStaysOnTopHint);
        setMouseTracking(true);
        setFocusPolicy(Qt::StrongFocus);
        setCursor(Qt::BlankCursor);
        cursorPos = QCursor::pos();
    }

protected:
    // The screenshot is in physical pixels, the widget is in logical pixels.
    QColor getPixelColor(const QPoint &pos) {
        double sx = width()  > 0 ? double(img.width())  / width()  : 1.0;
        double sy = height() > 0 ? double(img.height()) / height() : 1.0;
        int x = qBound(0, int(pos.x() * sx), img.width()  - 1);
        int y = qBound(0, int(pos.y() * sy), img.height() - 1);
        return img.pixelColor(x, y);
    }

    void mouseMoveEvent(QMouseEvent *event) override {
        cursorPos = event->pos();
        update();
    }

    void mousePressEvent(QMouseEvent *event) override {
        if (event->button() == Qt::LeftButton) {
            QColor c = getPixelColor(event->pos());
            std::cout << c.red() << " " << c.green() << " " << c.blue() << std::endl;
        }
        QApplication::quit();
    }

    void keyPressEvent(QKeyEvent *event) override {
        if (event->key() == Qt::Key_Escape) {
            QApplication::quit();
        }
    }

    void wheelEvent(QWheelEvent *event) override {
        int delta = event->angleDelta().y();
        if (delta > 0 && zoom < 24) zoom += 2;
        else if (delta < 0 && zoom > 6) zoom -= 2;
        lensRadius = (gridCount * zoom) / 2;
        update();
    }

    void paintEvent(QPaintEvent *) override {
        QPainter painter(this);
        painter.setRenderHint(QPainter::Antialiasing);
        painter.drawPixmap(rect(), pixmap);

        int cx = cursorPos.x();
        int cy = cursorPos.y();
        int r = lensRadius;
        int half = gridCount / 2;

        QPainterPath path;
        path.addEllipse(QPoint(cx, cy), r, r);

        painter.save();
        painter.setClipPath(path);

        for (int dx = -half; dx <= half; ++dx) {
            for (int dy = -half; dy <= half; ++dy) {
                QColor c = getPixelColor(QPoint(cx + dx, cy + dy));
                int rx = cx + dx * zoom - zoom / 2;
                int ry = cy + dy * zoom - zoom / 2;
                painter.fillRect(rx, ry, zoom, zoom, c);
                painter.setPen(QPen(QColor(255, 255, 255, 28), 1));
                painter.drawRect(rx, ry, zoom, zoom);
            }
        }

        QRectF centerRect(cx - zoom / 2, cy - zoom / 2, zoom, zoom);
        painter.setPen(QPen(QColor("#ffffff"), 2));
        painter.drawRect(centerRect);

        painter.restore();

        QColor centerColor = getPixelColor(cursorPos);
        painter.setPen(QPen(QColor(17, 17, 27, 220), 6));
        painter.drawEllipse(QPoint(cx, cy), r + 3, r + 3);
        painter.setPen(QPen(centerColor, 3));
        painter.drawEllipse(QPoint(cx, cy), r, r);

        QString hexStr = centerColor.name().toUpper();
        int pillW = 104, pillH = 30;
        int pillX = cx - pillW / 2;
        int pillY = cy + r + 14;
        if (pillY + pillH > height()) pillY = cy - r - pillH - 14;

        QRectF pillRect(pillX, pillY, pillW, pillH);
        painter.setPen(QPen(QColor(255, 255, 255, 45), 1));
        painter.setBrush(QColor(30, 30, 46, 235));
        painter.drawRoundedRect(pillRect, 15, 15);

        painter.setBrush(centerColor);
        painter.setPen(QPen(QColor(255, 255, 255, 130), 1));
        painter.drawEllipse(QRectF(pillX + 10, pillY + 7, 16, 16));

        painter.setPen(QColor("#cdd6f4"));
        painter.setFont(QFont("sans-serif", 10, QFont::Bold));
        painter.drawText(QRectF(pillX + 28, pillY, pillW - 34, pillH), Qt::AlignCenter, hexStr);
    }
};

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    if (argc < 2) return 1;
    QImage image(argv[1]);
    if (image.isNull()) return 2;
    LensWidget lens(image);
    QScreen *screen = QGuiApplication::screenAt(QCursor::pos());
    if (screen) lens.setScreen(screen);
    lens.showFullScreen();
    lens.activateWindow();
    lens.setFocus();
    return app.exec();
}
"""

CACHE_DIR = os.path.join(
    os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache")), "auracolorpicker"
)
RUNTIME_DIR = os.environ.get("XDG_RUNTIME_DIR") or CACHE_DIR


def notify(title, body, icon="dialog-information"):
    if shutil.which("notify-send"):
        subprocess.run(
            ["notify-send", "-a", "Aura Color Picker", "-i", icon, title, body],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )


def build_binary():
    """Compile the lens once (cached by source hash). Returns path or None."""
    os.makedirs(CACHE_DIR, mode=0o700, exist_ok=True)
    digest = hashlib.sha1(CPP_CODE.encode()).hexdigest()[:10]
    bin_path = os.path.join(CACHE_DIR, f"lens-{digest}")
    if os.path.exists(bin_path):
        return bin_path

    gxx = shutil.which("g++") or shutil.which("c++")
    if not gxx:
        notify("Aura Color Picker", "g++ not found. Install a C++ compiler (gcc-c++ / build-essential).", "dialog-error")
        return None

    flags = None
    if shutil.which("pkg-config"):
        r = subprocess.run(
            ["pkg-config", "--cflags", "--libs", "Qt6Widgets", "Qt6Gui", "Qt6Core"],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            flags = r.stdout.split()
    if flags is None:
        flags = [
            "-I/usr/include/qt6", "-I/usr/include/qt6/QtCore",
            "-I/usr/include/qt6/QtGui", "-I/usr/include/qt6/QtWidgets",
            "-lQt6Core", "-lQt6Gui", "-lQt6Widgets",
        ]

    notify("Aura Color Picker", "First run: preparing the picker (a few seconds)...")
    cpp_file = os.path.join(CACHE_DIR, "lens.cpp")
    with open(cpp_file, "w") as f:
        f.write(CPP_CODE)

    tmp_bin = bin_path + ".tmp"
    res = subprocess.run(
        [gxx, cpp_file, "-o", tmp_bin, "-std=c++17", "-fPIC", *flags],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        with open(os.path.join(CACHE_DIR, "build.log"), "w") as f:
            f.write(res.stderr)
        notify(
            "Aura Color Picker: build failed",
            "Install Qt6 dev packages (qt6-base-dev / qt6-qtbase-devel). Log: ~/.cache/auracolorpicker/build.log",
            "dialog-error",
        )
        return None
    os.replace(tmp_bin, bin_path)
    return bin_path


def take_screenshot():
    if not shutil.which("spectacle"):
        notify("Aura Color Picker", "spectacle is not installed.", "dialog-error")
        return None
    path = os.path.join(RUNTIME_DIR, "aura_freeze_screen.png")
    try:
        os.remove(path)
    except OSError:
        pass
    # -m = current monitor only (so it matches the fullscreen lens window)
    subprocess.run(
        ["spectacle", "-b", "-n", "-m", "-o", path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20,
    )
    return path if os.path.exists(path) else None


def format_color(idx, r, g, b):
    hex_ = f"#{r:02X}{g:02X}{b:02X}"
    rf, gf, bf = (f"{v / 255:.2f}" for v in (r, g, b))
    return {
        0: hex_,
        1: hex_[1:],
        2: f"rgb({r}, {g}, {b})",
        3: f"rgba({r}, {g}, {b}, 1.0)",
        4: f"Qt.rgba({rf}, {gf}, {bf}, 1.0)",
        5: f"{r}, {g}, {b}",
    }.get(idx, hex_), hex_


def copy_to_clipboard(text):
    candidates = []
    if shutil.which("wl-copy"):
        candidates.append(["wl-copy"])
    if shutil.which("xclip"):
        candidates.append(["xclip", "-selection", "clipboard"])
    for cmd in candidates:
        r = subprocess.run(cmd, input=text.encode(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0:
            return True
    for qdbus in ("qdbus6", "qdbus-qt6", "qdbus"):
        if shutil.which(qdbus):
            r = subprocess.run(
                [qdbus, "org.kde.klipper", "/klipper", "org.kde.klipper.klipper.setClipboardContents", text],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if r.returncode == 0:
                return True
    return False


def main():
    try:
        fmt = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    except ValueError:
        fmt = 0

    bin_path = build_binary()
    if not bin_path:
        sys.exit(1)

    shot = take_screenshot()
    if not shot:
        notify("Aura Color Picker", "Could not capture the screen (spectacle failed).", "dialog-error")
        sys.exit(1)

    try:
        res = subprocess.run([bin_path, shot], capture_output=True, text=True)
    finally:
        try:
            os.remove(shot)
        except OSError:
            pass

    parts = res.stdout.split()
    if len(parts) != 3:
        sys.exit(0)  # cancelled (Esc / right-click)
    r, g, b = (int(p) for p in parts)

    out, hex_ = format_color(fmt, r, g, b)
    copied = copy_to_clipboard(out)

    svg = os.path.join(RUNTIME_DIR, "auracolorpicker_swatch.svg")
    with open(svg, "w") as f:
        f.write(
            '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64">'
            f'<rect width="64" height="64" rx="20" fill="{hex_}"/></svg>'
        )
    notify("Color Picked" if copied else "Color Picked (clipboard failed)", out, svg)
    print(out)


if __name__ == "__main__":
    main()

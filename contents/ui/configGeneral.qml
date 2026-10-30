import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    property alias cfg_colorFormat: formatCombo.currentIndex

    Kirigami.FormLayout {
        QQC2.ComboBox {
            id: formatCombo
            Kirigami.FormData.label: "Color Format:"
            model: [
                "HEX (#RRGGBB)",
                "HEX Raw (RRGGBB)",
                "RGB — rgb(r, g, b)",
                "RGBA — rgba(r, g, b, 1.0)",
                "QML — Qt.rgba(r, g, b, 1.0)",
                "Raw Values — r, g, b"
            ]
        }
    }
}
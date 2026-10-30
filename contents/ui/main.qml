import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami
import "components"

PlasmoidItem {
    id: root

    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: compactRepresentation
    toolTipMainText: "Aura Color Picker"
    toolTipSubText: "Click to pick a color from screen"

    PickerBackend {
        id: pickerBackend
    }

    Plasmoid.onActivated: pickerBackend.pick(Plasmoid.configuration.colorFormat)

    compactRepresentation: Component {
        Item {
            id: compactRoot

            Kirigami.Icon {
                anchors.fill: parent
                source: Qt.resolvedUrl("icons/color-picker.svg")
                isMask: true
                color: Kirigami.Theme.textColor
                scale: mouseArea.pressed ? 0.85 : 1.0

                Behavior on scale {
                    NumberAnimation { duration: 120 }
                }
            }

            MouseArea {
                id: mouseArea
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton
                onClicked: pickerBackend.pick(Plasmoid.configuration.colorFormat)
            }
        }
    }

    fullRepresentation: Component {
        Item {}
    }
}
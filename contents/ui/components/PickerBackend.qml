import QtQuick
import org.kde.plasma.plasma5support as P5Support

Item {
    id: backend

    property bool busy: false

    P5Support.DataSource {
        id: executable
        engine: "executable"
        connectedSources: []
        onNewData: function(source, data) {
            disconnectSource(source)
            backend.busy = false
        }
    }

    function pick(formatIndex) {
        if (busy)
            return

        var scriptUrl = Qt.resolvedUrl("../../scripts/hypr_lens.py").toString()
        var scriptPath = decodeURIComponent(scriptUrl.replace("file://", ""))
        var quoted = "'" + scriptPath.replace(/'/g, "'\\''") + "'"

        busy = true
        // All the logic lives in the Python script, so this works with any /bin/sh (dash, bash...)
        executable.connectSource("python3 " + quoted + " " + (formatIndex | 0))
    }
}

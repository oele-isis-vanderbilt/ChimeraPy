import QtQuick 2.0
import pymmdt.app.pylib 1.0

Item {
    id: imageContent
    anchors.fill: parent

    Text {
        id: entryTitle
        anchors.top: parent.top
        text: qsTr(user)+"\\" + qsTr(entry_name)
        color: "white"
    }

    ContentImage {
        anchors.top: entryTitle.bottom
        height: _height
        width: _width
        image: content
    }
}

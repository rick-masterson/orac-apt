import QtQuick 2.15
import QtQuick.Controls 2.15 as QQC2

// ORAC login splash. KSplash sets `stage` on the root object as the session
// comes up (1..6); dots before the current stage are solid, the rest pulse.
Rectangle {
    id: root
    color: "#000000"

    property int stage: 0

    Image {
        anchors.fill: parent
        source: "images/background.png"
        fillMode: Image.PreserveAspectCrop
        smooth: true
    }

    // Vignette toward the bottom. Qt colours are #AARRGGBB.
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.55; color: "#00000000" }
            GradientStop { position: 1.0; color: "#AA000000" }
        }
    }

    // Breathing glow over the orb.
    Rectangle {
        width: parent.height * 0.42
        height: width
        radius: width / 2
        anchors.centerIn: parent
        color: "#b266ff"
        opacity: 0.08
        SequentialAnimation on opacity {
            loops: Animation.Infinite
            NumberAnimation { to: 0.18; duration: 1200; easing.type: Easing.InOutQuad }
            NumberAnimation { to: 0.08; duration: 1200; easing.type: Easing.InOutQuad }
        }
        SequentialAnimation on scale {
            loops: Animation.Infinite
            NumberAnimation { to: 1.08; duration: 2400; easing.type: Easing.InOutQuad }
            NumberAnimation { to: 1.0; duration: 2400; easing.type: Easing.InOutQuad }
        }
    }

    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 180
        spacing: 14

        Repeater {
            model: 5
            Rectangle {
                id: dot
                width: 10; height: 10
                radius: 5
                color: "#c084fc"
                property real pulse: 0.25
                opacity: index < root.stage - 1 ? 1.0 : pulse

                SequentialAnimation on pulse {
                    loops: Animation.Infinite
                    PauseAnimation { duration: index * 150 }
                    NumberAnimation { to: 1.0; duration: 400 }
                    NumberAnimation { to: 0.25; duration: 600 }
                }
            }
        }
    }

    QQC2.BusyIndicator {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 120
        width: 48; height: 48
        running: true
        palette.text: "#c084fc"
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 80
        text: "ORAC WORKSTATION // NEURAL CORE ONLINE"
        color: "#c084fc"
        font.family: "JetBrains Mono"
        font.pointSize: 10
        font.letterSpacing: 2
        opacity: 0.7
    }
}

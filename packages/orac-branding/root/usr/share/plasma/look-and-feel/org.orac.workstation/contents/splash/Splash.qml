import QtQuick 2.15
import QtMultimedia

// ORAC login splash. The ORAC core video plays once over the still picture
// (which stays as the fallback if the video cannot play). KSplash sets `stage`
// on the root object as the session comes up (1..6), and a slim gradient bar
// fills with it: the one status indicator.
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

    Video {
        anchors.fill: parent
        source: Qt.resolvedUrl("images/orac-core.webm")
        fillMode: VideoOutput.PreserveAspectCrop
        muted: true
        autoPlay: true
        endOfStreamPolicy: VideoOutput.KeepLastFrame
    }

    // Vignette toward the bottom. Qt colours are #AARRGGBB.
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.55; color: "#00000000" }
            GradientStop { position: 1.0; color: "#AA000000" }
        }
    }

    // The web dashboard's gradient "orac" wordmark.
    Image {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: track.top
        anchors.bottomMargin: 18
        source: "images/wordmark.png"
        smooth: true
    }

    Rectangle {
        id: track
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 120
        width: 220; height: 4
        radius: 2
        color: "#2e2440"

        Rectangle {
            height: parent.height
            radius: 2
            width: parent.width * Math.min(1, Math.max(0, root.stage) / 6)
            Behavior on width { NumberAnimation { duration: 400; easing.type: Easing.OutCubic } }
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: "#ff7a2f" }
                GradientStop { position: 0.5; color: "#e0508a" }
                GradientStop { position: 1.0; color: "#8b5cf6" }
            }
        }
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

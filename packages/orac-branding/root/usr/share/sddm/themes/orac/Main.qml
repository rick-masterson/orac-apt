// ORAC login (SDDM, Qt 6): the ORAC core loops behind a frosted glass
// panel, matching the ORAC web console's unlock screen.
import QtQuick
import QtQuick.Controls
import QtMultimedia

Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "#050308"

    readonly property color text: "#ece6f3"
    readonly property color muted: "#9a8fab"
    readonly property color border: "#2e2440"
    readonly property color red: "#f85149"

    // Still frame first, so there's never a blank screen while video loads.
    Image {
        anchors.fill: parent
        source: config.background
        fillMode: Image.PreserveAspectCrop
    }

    MediaPlayer {
        id: player
        source: Qt.resolvedUrl(config.video)
        loops: MediaPlayer.Infinite
        videoOutput: video
        Component.onCompleted: play()
    }
    VideoOutput {
        id: video
        anchors.fill: parent
        fillMode: VideoOutput.PreserveAspectCrop
    }

    Rectangle {
        anchors.fill: parent
        color: "#0c0814"
        opacity: 0.35
    }

    Text {
        id: clock
        anchors { top: parent.top; right: parent.right; margins: 28 }
        color: root.muted
        font { family: "JetBrains Mono"; pixelSize: 16 }
        function update() { text = Qt.formatDateTime(new Date(), "ddd d MMM · hh:mm") }
        Component.onCompleted: update()
        Timer { interval: 10000; running: true; repeat: true; onTriggered: clock.update() }
    }

    Rectangle {
        id: panel
        anchors.centerIn: parent
        width: Math.min(380, root.width - 32)
        height: column.implicitHeight + 56
        radius: 14
        color: Qt.rgba(20 / 255, 15 / 255, 31 / 255, 0.78)
        border { color: Qt.rgba(139 / 255, 92 / 255, 246 / 255, 0.45); width: 1 }

        Column {
            id: column
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: 28 }
            spacing: 12

            Text {
                text: "orac"
                font { family: "Inter"; pixelSize: 30; weight: Font.Bold }
                color: "#ff7a2f"
            }
            Text {
                text: "Sign in to continue."
                color: root.muted
                font { family: "Inter"; pixelSize: 14 }
            }

            component Field: TextField {
                width: column.width
                height: 40
                color: root.text
                placeholderTextColor: root.muted
                font { family: "JetBrains Mono"; pixelSize: 14 }
                leftPadding: 12
                background: Rectangle {
                    radius: 10
                    color: Qt.rgba(12 / 255, 8 / 255, 20 / 255, 0.85)
                    border { width: 1; color: parent.activeFocus ? "#ff7a2f" : root.border }
                }
            }

            Field {
                id: user
                placeholderText: "User"
                text: userModel.lastUser
                KeyNavigation.tab: password
                onAccepted: password.forceActiveFocus()
            }
            Field {
                id: password
                placeholderText: "Password"
                echoMode: TextInput.Password
                focus: true
                onAccepted: root.login()
            }

            Button {
                id: unlock
                width: column.width
                height: 40
                text: "Unlock"
                onClicked: root.login()
                contentItem: Text {
                    text: unlock.text
                    color: "#1a0b02"
                    font { family: "Inter"; pixelSize: 14; weight: Font.DemiBold }
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 10
                    opacity: unlock.down ? 0.8 : 1
                    gradient: Gradient {
                        orientation: Gradient.Horizontal
                        GradientStop { position: 0; color: "#ff7a2f" }
                        GradientStop { position: 0.55; color: "#e0508a" }
                        GradientStop { position: 1; color: "#8b5cf6" }
                    }
                }
            }

            Text {
                id: message
                width: column.width
                color: root.red
                font { family: "Inter"; pixelSize: 13 }
                wrapMode: Text.WordWrap
            }
        }
    }

    Row {
        anchors { bottom: parent.bottom; right: parent.right; margins: 24 }
        spacing: 10

        component PowerButton: Button {
            id: btn
            height: 32
            contentItem: Text {
                text: btn.text
                color: btn.hovered ? root.text : root.muted
                font { family: "JetBrains Mono"; pixelSize: 13 }
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle {
                radius: 16
                color: Qt.rgba(20 / 255, 15 / 255, 31 / 255, 0.85)
                border { width: 1; color: btn.hovered ? "#ff7a2f" : root.border }
            }
        }

        PowerButton { text: "  restart  "; visible: sddm.canReboot; onClicked: sddm.reboot() }
        PowerButton { text: "  shut down  "; visible: sddm.canPowerOff; onClicked: sddm.powerOff() }
    }

    function login() {
        message.text = "";
        sddm.login(user.text, password.text, sessionModel.lastIndex);
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            message.text = "Wrong user or password.";
            password.text = "";
            password.forceActiveFocus();
        }
    }
}

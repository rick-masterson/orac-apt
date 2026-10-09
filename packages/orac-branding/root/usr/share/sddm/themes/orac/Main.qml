import QtQuick
import QtQuick.Controls

// ORAC login screen for SDDM (Qt 6, theme API 2.0). Written for orac-branding; palette matches the
// Plymouth splash and KSplash. Colours and text come from theme.conf.
Rectangle {
    id: root
    width: 1920
    height: 1080
    color: "#000000"

    readonly property color accent: config.accent || "#c084fc"
    readonly property color glow: config.glow || "#b266ff"
    readonly property color ink: config.text || "#d6dbe1"
    readonly property string sans: config.fontFamily || "Inter"
    readonly property string mono: config.monoFamily || "JetBrains Mono"
    property bool failed: false

    Connections {
        target: sddm
        function onLoginFailed() {
            root.failed = true
            password.text = ""
            password.forceActiveFocus()
            shake.restart()
        }
    }

    Image {
        anchors.fill: parent
        source: config.background || "background.png"
        fillMode: Image.PreserveAspectCrop
        smooth: true
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.45; color: "#00000000" }
            GradientStop { position: 1.0; color: "#CC000000" }
        }
    }

    // Breathing glow behind the form.
    Rectangle {
        width: parent.height * 0.5
        height: width
        radius: width / 2
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height * 0.5 - height / 2
        color: root.glow
        opacity: 0.08
        SequentialAnimation on opacity {
            loops: Animation.Infinite
            NumberAnimation { to: 0.16; duration: 2400; easing.type: Easing.InOutQuad }
            NumberAnimation { to: 0.08; duration: 2400; easing.type: Easing.InOutQuad }
        }
    }

    Text {
        visible: config.showClock !== "false"
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 40
        color: root.ink
        opacity: 0.8
        font.family: root.mono
        font.pointSize: 14
        text: Qt.formatDateTime(clock.now, "ddd d MMM  hh:mm")
        QtObject { id: clock; property date now: new Date() }
        Timer { interval: 1000; running: true; repeat: true; onTriggered: clock.now = new Date() }
    }

    Column {
        id: form
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height * 0.5 - height / 2
        spacing: 16
        width: 360

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: config.title || "ORAC WORKSTATION"
            color: root.accent
            font.family: root.mono
            font.pointSize: 18
            font.letterSpacing: 4
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "// " + (config.tagline || "NEURAL CORE ONLINE")
            color: root.accent
            opacity: 0.7
            font.family: root.mono
            font.pointSize: 9
            font.letterSpacing: 2
            bottomPadding: 16
        }

        ComboBox {
            id: user
            width: parent.width
            model: userModel
            textRole: "name"
            currentIndex: userModel.lastIndex
            font.family: root.sans
            onActivated: password.forceActiveFocus()
        }

        TextField {
            id: password
            width: parent.width
            echoMode: TextInput.Password
            placeholderText: "Password"
            color: root.ink
            font.family: root.sans
            focus: true
            background: Rectangle {
                color: "#0d0b14"
                radius: 4
                border.width: 1
                border.color: root.failed ? "#f0526e" : (password.activeFocus ? root.accent : "#3a344e")
            }
            onTextChanged: root.failed = false
            Keys.onReturnPressed: go.clicked()
            Keys.onEnterPressed: go.clicked()
            SequentialAnimation {
                id: shake
                NumberAnimation { target: form; property: "x"; to: form.x - 12; duration: 50 }
                NumberAnimation { target: form; property: "x"; to: form.x + 12; duration: 100 }
                NumberAnimation { target: form; property: "x"; to: form.x; duration: 50 }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: root.failed || keyboard.capsLock
            text: root.failed ? "Login failed" : "Caps Lock is on"
            color: root.failed ? "#f0526e" : "#e8be6e"
            font.family: root.sans
            font.pointSize: 10
        }

        Button {
            id: go
            width: parent.width
            text: "Log in"
            font.family: root.sans
            onClicked: sddm.login(user.currentText, password.text, session.currentIndex)
            contentItem: Text {
                text: go.text
                color: "#000000"
                font: go.font
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
            background: Rectangle {
                radius: 4
                color: go.down ? Qt.darker(root.accent, 1.3) : (go.hovered ? Qt.lighter(root.accent, 1.15) : root.accent)
            }
        }
    }

    Row {
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: 40
        spacing: 12
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: "Session"
            color: root.ink
            opacity: 0.7
            font.family: root.sans
            font.pointSize: 10
        }
        ComboBox {
            id: session
            width: 220
            model: sessionModel
            textRole: "name"
            currentIndex: sessionModel.lastIndex
            font.family: root.sans
        }
    }

    Row {
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 40
        spacing: 12
        Button { text: "Sleep"; visible: sddm.canSuspend; onClicked: sddm.suspend() }
        Button { text: "Restart"; visible: sddm.canReboot; onClicked: sddm.reboot() }
        Button { text: "Shut down"; visible: sddm.canPowerOff; onClicked: sddm.powerOff() }
    }

    Text {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 40
        text: "ORAC on " + (config.base || "Shadowfetch Linux · Debian")
        color: root.ink
        opacity: 0.5
        font.family: root.mono
        font.pointSize: 9
        font.letterSpacing: 1
    }
}

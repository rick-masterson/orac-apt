// Developed with the help of Claude Code (https://claude.com/claude-code)
// Orac Living Core: background.png split into depth layers that move
// independently. A slow camera drift moves near layers further than far ones
// (parallax), the orb breathes, the glow pulses with it, and the lightning
// flickers at random.
import QtQuick
import org.kde.plasma.plasmoid

WallpaperItem {
    id: root

    Rectangle {
        anchors.fill: parent
        color: "black"
    }

    Item {
        id: scene
        anchors.fill: parent

        // Camera drift: one slow orbit every 48 s.
        property real t: 0
        NumberAnimation on t {
            from: 0; to: 2 * Math.PI; duration: 48000
            loops: Animation.Infinite
        }
        readonly property real dx: 16 * Math.cos(t)
        readonly property real dy: 11 * Math.sin(t)

        // Breathing: 0 -> 1 -> 0 every 5.2 s.
        property real breath: 0
        SequentialAnimation on breath {
            loops: Animation.Infinite
            NumberAnimation { to: 1; duration: 2600; easing.type: Easing.InOutSine }
            NumberAnimation { to: 0; duration: 2600; easing.type: Easing.InOutSine }
        }

        component Layer: Image {
            property real depth: 1
            width: scene.width; height: scene.height
            x: scene.dx * depth
            y: scene.dy * depth
            // Fit the whole image across the screen's width; its edges are
            // black, so it melts into the black above and below.
            fillMode: Image.PreserveAspectFit
            smooth: true
            asynchronous: true
            cache: true
        }

        // Far: the cube, smoke and stars.
        Layer {
            source: "../images/base.png"
            depth: 0.6
            scale: 1.06
        }

        // Bloom around everything bright, swelling with each breath.
        Layer {
            source: "../images/glow.png"
            depth: 1.1
            scale: 1.06 + 0.015 * scene.breath
            opacity: 0.25 + 0.45 * scene.breath
        }

        // Near: the orb itself.
        Layer {
            source: "../images/orb.png"
            depth: 1.8
            scale: 1.06 + 0.03 * scene.breath
        }

        // Lightning rides with the orb and flickers.
        Layer {
            id: lightning
            source: "../images/lightning.png"
            depth: 1.8
            scale: 1.06 + 0.03 * scene.breath
            opacity: 0.6
            Behavior on opacity { NumberAnimation { duration: 70 } }
        }

        Timer {
            running: true; repeat: true
            interval: 120
            onTriggered: {
                lightning.opacity = Math.random() < 0.12 ? 0.15 + Math.random() * 0.2
                                                         : 0.55 + Math.random() * 0.45;
                interval = 60 + Math.random() * 700;
            }
        }
    }
}

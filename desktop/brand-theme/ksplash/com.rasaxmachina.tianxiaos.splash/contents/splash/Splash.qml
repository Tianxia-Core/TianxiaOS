// ffp: FFP-KSPLASH-QML frontend qml
import QtQuick

Rectangle {
    id: root
    color: "#050508"

    property int stage: 0

    onStageChanged: {
        if (stage >= 1) {
            contentCard.opacity = 1.0
            contentCard.y = root.height * 0.5 - contentCard.height * 0.52
        }
    }

    Image {
        id: bgAurora
        anchors.fill: parent
        source: "images/bg-aurora.png"
        fillMode: Image.PreserveAspectCrop
        smooth: true
    }

    // Pulsing electric violet halo behind txOS emblem
    Rectangle {
        id: haloOrb
        width: 320
        height: 320
        radius: 160
        anchors.horizontalCenter: parent.horizontalCenter
        y: root.height * 0.23
        color: "#7c5cff"
        opacity: 0.16

        SequentialAnimation on opacity {
            loops: Animation.Infinite
            running: true
            NumberAnimation { from: 0.10; to: 0.24; duration: 1800; easing.type: Easing.InOutQuad }
            NumberAnimation { from: 0.24; to: 0.10; duration: 1800; easing.type: Easing.InOutQuad }
        }
    }

    // Outer double-bezel Ethereal Glass centerpiece card (matches rasaxmachina.com .tx-glass-outer)
    Rectangle {
        id: contentCard
        width: Math.min(root.width * 0.76, 1060)
        height: 450
        anchors.horizontalCenter: parent.horizontalCenter
        y: root.height * 0.5 - height * 0.48
        radius: 32
        color: "#cc0a0a14"
        border.width: 1
        border.color: "#557c5cff"
        opacity: 0.0

        Behavior on opacity {
            NumberAnimation { duration: 650; easing.type: Easing.OutCubic }
        }
        Behavior on y {
            NumberAnimation { duration: 700; easing.type: Easing.OutCubic }
        }

        Component.onCompleted: {
            opacity = 1.0
            y = root.height * 0.5 - height * 0.52
        }

        // Inner glass core bezel
        Rectangle {
            anchors.fill: parent
            anchors.margins: 8
            radius: 26
            color: "#6606060c"
            border.width: 1
            border.color: "#1affffff"

            Column {
                anchors.centerIn: parent
                spacing: 22
                width: parent.width - 64

                // txOS Icon Mark
                Image {
                    source: "images/txos-mark.png"
                    width: 96
                    height: 96
                    anchors.horizontalCenter: parent.horizontalCenter
                    smooth: true
                }

                // Canonical Dual Brand Lockup (RASA-X-MACHINA · tianxiaOS)
                Image {
                    source: "images/dual-lockup.png"
                    width: Math.min(parent.width, 820)
                    fillMode: Image.PreserveAspectFit
                    anchors.horizontalCenter: parent.horizontalCenter
                    smooth: true
                }

                // Animated Sovereign Boot Progress Rail
                Rectangle {
                    id: progressTrack
                    width: Math.min(parent.width * 0.62, 500)
                    height: 8
                    radius: 4
                    color: "#1a1a2e"
                    border.width: 1
                    border.color: "#407c5cff"
                    anchors.horizontalCenter: parent.horizontalCenter

                    Rectangle {
                        id: progressFill
                        height: parent.height
                        radius: 4
                        width: Math.max(48, parent.width * Math.min(1.0, (Math.max(1, root.stage) / 6.0)))

                        gradient: Gradient {
                            orientation: Gradient.Horizontal
                            GradientStop { position: 0.0; color: "#7c5cff" }
                            GradientStop { position: 0.5; color: "#a855f7" }
                            GradientStop { position: 1.0; color: "#22d3ee" }
                        }

                        Behavior on width {
                            NumberAnimation { duration: 520; easing.type: Easing.OutCubic }
                        }
                    }

                    // Shimmering runner when tested standalone (stage == 0)
                    Rectangle {
                        visible: root.stage === 0
                        width: parent.width * 0.68
                        height: parent.height
                        radius: 4
                        gradient: Gradient {
                            orientation: Gradient.Horizontal
                            GradientStop { position: 0.0; color: "#7c5cff" }
                            GradientStop { position: 0.5; color: "#a855f7" }
                            GradientStop { position: 1.0; color: "#22d3ee" }
                        }
                        SequentialAnimation on x {
                            loops: Animation.Infinite
                            running: root.stage === 0
                            NumberAnimation { from: 0; to: progressTrack.width * 0.32; duration: 1400; easing.type: Easing.InOutCubic }
                            NumberAnimation { from: progressTrack.width * 0.32; to: 0; duration: 1400; easing.type: Easing.InOutCubic }
                        }
                    }
                }

                // Live telemetry & Veritas seal strip
                Row {
                    anchors.horizontalCenter: parent.horizontalCenter
                    spacing: 10

                    Rectangle {
                        width: 9
                        height: 9
                        radius: 5
                        color: "#00f59b"
                        anchors.verticalCenter: parent.verticalCenter
                    }

                    Text {
                        text: "VERITAS SEALED  ·  v8.7.0 CROWNFORGE  ·  DSS-14.2 PARAMASIVA  ·  ROSENPASS PQ MESH"
                        color: "#cbd5e1"
                        font.family: "JetBrains Mono"
                        font.pixelSize: 13
                        font.weight: Font.Medium
                        font.letterSpacing: 1.4
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
            }
        }
    }

    // Footer node provenance
    Text {
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 28
        anchors.horizontalCenter: parent.horizontalCenter
        text: "rasaxmachina.com  ·  NODE: latitude-tianxia (NixOS Wayland Substrate)"
        color: "#8892b0"
        font.family: "JetBrains Mono"
        font.pixelSize: 12
        font.letterSpacing: 1.2
    }
}

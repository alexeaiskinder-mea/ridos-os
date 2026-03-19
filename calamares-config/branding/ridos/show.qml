import QtQuick 2.0

Rectangle {
    color: "#1E1B4B"
    width: 800
    height: 500

    Column {
        anchors.centerIn: parent
        spacing: 20

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "RIDOS OS"
            color: "#C4B5FD"
            font.pointSize: 36
            font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "ريدوس أو إس"
            color: "#C4B5FD"
            font.pointSize: 24
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "v1.1.0 Baghdad"
            color: "#E9D5FF"
            font.pointSize: 16
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "AI-Powered Linux for IT Professionals"
            color: "#DDD6FE"
            font.pointSize: 14
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: "نظام لينكس المدعوم بالذكاء الاصطناعي لمحترفي تقنية المعلومات"
            color: "#DDD6FE"
            font.pointSize: 12
        }
    }
}

import QtQuick 2
import com.victron.velib 1.0
import "utils.js" as Utils

MbPage {
    title: qsTr("Huawei SUN2000")
    property string settings: "com.victronenergy.settings/Settings/HuaweiSUN2000"

    model: VisibleItemModel {
                MbEditBoxIp {
                        id: modbusHost
                        description: qsTr("Modbus host IP")
                        item.bind: Utils.path(settings, "/ModbusHost")
                }

        MbEditBox {
            id: modbusPort
            description: qsTr("Modbus port")
            matchString: " 0123456789"
            numericOnlyLayout: true
            item.bind: Utils.path(settings, "/ModbusPort")

            function editTextToValue() {
                return parseInt(_editText, 10)
            }
        }

        MbEditBox {
            id: modbusUnit
            description: qsTr("Modbus unit")
            matchString: " 0123456789"
            numericOnlyLayout: true
            item.bind: Utils.path(settings, "/ModbusUnit")

            function editTextToValue() {
                return parseInt(_editText, 10)
            }
        }

                MbEditBox {
                        id: customName
                        description: qsTr("Custom Name")
                        item.bind: Utils.path(settings, "/CustomName")
                }

                MbItemOptions {
                        description: qsTr("Position")
                        bind: Utils.path(settings, "/Position")
                        possibleValues: [
                                MbOption { description: qsTr("AC Input 1"); value: 0 },
                                MbOption { description: qsTr("AC Input 2"); value: 2 },
                                MbOption { description: qsTr("AC Output"); value: 1 }
                        ]
                }

        MbEditBox {
            id: updateTimeMS
            description: qsTr("Update time(ms)")
            matchString: " 0123456789"
            numericOnlyLayout: true
            item.bind: Utils.path(settings, "/UpdateTimeMS")

            function editTextToValue() {
                return parseInt(_editText, 10)
            }
        }

                MbSpinBox {
                    description: qsTr("Power correction factor")
                    item {
                        bind: Utils.path(settings, "/PowerCorrectionFactor")
                        decimals: 3
                        step: 0.001
                    }
                }

    }
}

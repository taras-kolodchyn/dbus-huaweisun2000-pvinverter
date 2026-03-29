#!/bin/bash
set -eu

SETTINGS_SERVICE="com.victronenergy.settings"

usage() {
    cat <<'EOF'
Usage:
  configure.sh --show
  configure.sh [--host HOST] [--port PORT] [--unit UNIT] [--position POSITION]
               [--custom-name NAME] [--phase-type {auto,single-phase,three-phase}]
               [--update-ms MS] [--power-correction FACTOR]

Examples:
  sh configure.sh --host 192.168.211.50 --port 502 --unit 3
  sh configure.sh --position 2 --custom-name "Huawei SUN2000"
  sh configure.sh --show
EOF
}

dbus_get() {
    dbus -y "$SETTINGS_SERVICE" "$1" GetValue
}

dbus_set() {
    dbus -y "$SETTINGS_SERVICE" "$1" SetValue "$2" >/dev/null
}

show_settings() {
    printf 'Modbus host: %s\n' "$(dbus_get /Settings/HuaweiSUN2000/ModbusHost)"
    printf 'Modbus port: %s\n' "$(dbus_get /Settings/HuaweiSUN2000/ModbusPort)"
    printf 'Modbus unit: %s\n' "$(dbus_get /Settings/HuaweiSUN2000/ModbusUnit)"
    printf 'Phase type override: %s\n' "$(dbus_get /Settings/HuaweiSUN2000/PhaseTypeOverride)"
    printf 'Custom name: %s\n' "$(dbus_get /Settings/HuaweiSUN2000/CustomName)"
    printf 'Position: %s\n' "$(dbus_get /Settings/HuaweiSUN2000/Position)"
    printf 'Update time (ms): %s\n' "$(dbus_get /Settings/HuaweiSUN2000/UpdateTimeMS)"
    printf 'Power correction factor: %s\n' "$(dbus_get /Settings/HuaweiSUN2000/PowerCorrectionFactor)"
}

if ! command -v dbus >/dev/null 2>&1; then
    echo "ERROR: dbus command is required on Venus OS." >&2
    exit 1
fi

if [ $# -eq 0 ]; then
    usage
    exit 1
fi

show_after_update=0

while [ $# -gt 0 ]; do
    case "$1" in
        --show)
            show_settings
            exit 0
            ;;
        --host)
            dbus_set /Settings/HuaweiSUN2000/ModbusHost "$2"
            show_after_update=1
            shift 2
            ;;
        --port)
            dbus_set /Settings/HuaweiSUN2000/ModbusPort "$2"
            show_after_update=1
            shift 2
            ;;
        --unit)
            dbus_set /Settings/HuaweiSUN2000/ModbusUnit "$2"
            show_after_update=1
            shift 2
            ;;
        --position)
            dbus_set /Settings/HuaweiSUN2000/Position "$2"
            show_after_update=1
            shift 2
            ;;
        --custom-name)
            dbus_set /Settings/HuaweiSUN2000/CustomName "$2"
            show_after_update=1
            shift 2
            ;;
        --phase-type)
            case "$2" in
                auto)
                    dbus_set /Settings/HuaweiSUN2000/PhaseTypeOverride ""
                    ;;
                single-phase|three-phase)
                    dbus_set /Settings/HuaweiSUN2000/PhaseTypeOverride "$2"
                    ;;
                *)
                    echo "ERROR: --phase-type must be auto, single-phase, or three-phase" >&2
                    exit 1
                    ;;
            esac
            show_after_update=1
            shift 2
            ;;
        --update-ms)
            dbus_set /Settings/HuaweiSUN2000/UpdateTimeMS "$2"
            show_after_update=1
            shift 2
            ;;
        --power-correction)
            dbus_set /Settings/HuaweiSUN2000/PowerCorrectionFactor "$2"
            show_after_update=1
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: unknown argument: $1" >&2
            usage
            exit 1
            ;;
    esac
done

if [ "$show_after_update" -eq 1 ]; then
    show_settings
fi

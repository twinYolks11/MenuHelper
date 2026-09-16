#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="MenuHelper"
INSTALL_DIR="/opt/${APP_NAME}"
LAUNCHER="/usr/local/bin/menuhelper"
DESKTOP_FILE="/usr/share/applications/menuhelper.desktop"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR=""

cleanup() {
    if [[ -n "${BUILD_DIR}" && -d "${BUILD_DIR}" ]]; then
        rm -rf "${BUILD_DIR}"
    fi
}
trap cleanup EXIT

if [[ "${EUID}" -ne 0 ]]; then
    exec sudo --preserve-env=PATH "${BASH_SOURCE[0]}" "$@"
fi

if [[ ! -f "${SCRIPT_DIR}/main.py" ]]; then
    echo "Run this script from a MenuHelper source checkout." >&2
    exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install --yes python3 python3-tk python3-venv

BUILD_DIR="$(mktemp -d -t menuhelper-build-XXXXXX)"
python3 -m venv "${BUILD_DIR}/venv"
"${BUILD_DIR}/venv/bin/python" -m pip install --upgrade pip pyinstaller

"${BUILD_DIR}/venv/bin/pyinstaller" \
    --noconfirm \
    --clean \
    --onedir \
    --windowed \
    --name "${APP_NAME}" \
    --distpath "${BUILD_DIR}/dist" \
    --workpath "${BUILD_DIR}/build" \
    --specpath "${BUILD_DIR}" \
    "${SCRIPT_DIR}/main.py"

rm -rf "${INSTALL_DIR}"
install -d -m 0755 "${INSTALL_DIR}"
cp -a "${BUILD_DIR}/dist/${APP_NAME}/." "${INSTALL_DIR}/"
chown -R root:root "${INSTALL_DIR}"
chmod -R a+rX "${INSTALL_DIR}"

cat > "${LAUNCHER}" <<EOF
#!/usr/bin/env bash
exec "${INSTALL_DIR}/${APP_NAME}" "\$@"
EOF
chmod 0755 "${LAUNCHER}"

cat > "${DESKTOP_FILE}" <<EOF
[Desktop Entry]
Type=Application
Name=Menu Helper
Comment=Plan meals and create shopping lists
Exec=${LAUNCHER}
Terminal=false
Categories=Office;Utility;
StartupNotify=true
StartupWMClass=${APP_NAME}
EOF
chmod 0644 "${DESKTOP_FILE}"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications
fi

echo "${APP_NAME} installed for all users."
echo "Launch it from the Cinnamon menu or run: ${LAUNCHER}"

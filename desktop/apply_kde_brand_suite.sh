#!/usr/bin/env bash
# ffp: FFP-KDE-BRAND-APPLIER content-pipeline bash
# SLECO-SO++ Live & Persistent Installer for RASA-X-MACHINA · tianxiaOS KDE Plasma 6 + Boot Brand Suite
set +e
set +u

SCRIPT_PATH="${0}"
SRC_DIR="${SCRIPT_PATH%/*}"
if [ "${SRC_DIR}" = "${SCRIPT_PATH}" ]; then
    SRC_DIR="."
fi

MODE="${1:---live-reload}"
THEME_SRC="${SRC_DIR}/brand-theme"
if [ ! -d "${THEME_SRC}" ] && [ -d "/var/lib/tianxia/brand-theme" ]; then
    THEME_SRC="/var/lib/tianxia/brand-theme"
fi

TARGET_USER="${TX_DESKTOP_USER:-tianxia}"
TARGET_HOME="/home/${TARGET_USER}"
TARGET_UID="$(id -u "${TARGET_USER}" 2>/dev/null || printf '1000')"

log_info() {
    printf '[tx-kde-brand] %s\n' "$1"
}

trap 'printf "[tx-kde-brand] Completed execution (mode=%s).\n" "${MODE}"' EXIT

if [ ! -d "${THEME_SRC}" ]; then
    log_info "ERROR: brand-theme directory not found at ${THEME_SRC}"
    exit 1
fi

# 1. Persist canonical brand-theme bundle in /var/lib/tianxia/brand-theme & /etc/plymouth
mkdir -p /var/lib/tianxia/brand-theme /etc/plymouth/themes/tianxiaos /usr/local/bin /usr/local/share/fonts/tianxia-brand /usr/local/share/icons/hicolor
if [ "${THEME_SRC}" != "/var/lib/tianxia/brand-theme" ]; then
    cp -rf "${THEME_SRC}/." /var/lib/tianxia/brand-theme/
    cp -f "${0}" /var/lib/tianxia/brand-theme/apply_kde_brand_suite.sh
    chmod 0755 /var/lib/tianxia/brand-theme/apply_kde_brand_suite.sh
fi
cp -rf /var/lib/tianxia/brand-theme/plymouth/tianxiaos/. /etc/plymouth/themes/tianxiaos/
cp -rf /var/lib/tianxia/brand-theme/fonts/. /usr/local/share/fonts/tianxia-brand/
cp -rf /var/lib/tianxia/brand-theme/icons/hicolor/. /usr/local/share/icons/hicolor/

if [ -f "${SRC_DIR}/tx-os-banner" ]; then
    cp -f "${SRC_DIR}/tx-os-banner" /usr/local/bin/tx-os-banner
    cp -f "${SRC_DIR}/tx-os-banner" /var/lib/tianxia/bin/tx-os-banner
    chmod 0755 /usr/local/bin/tx-os-banner /var/lib/tianxia/bin/tx-os-banner
fi

if [ -f "${SRC_DIR}/install_desktop_suite.sh" ]; then
    bash "${SRC_DIR}/install_desktop_suite.sh" --install-host
fi

if [ ! -d "${TARGET_HOME}" ]; then
    log_info "No desktop home at ${TARGET_HOME}; system-level assets staged."
    exit 0
fi

# 2. Populate user fonts, icons, wallpapers, color-schemes, Plasma theme & QML KSplash
mkdir -p \
    "${TARGET_HOME}/.local/share/fonts/tianxia-brand" \
    "${TARGET_HOME}/.local/share/icons/hicolor" \
    "${TARGET_HOME}/.local/share/icons/breeze-dark/apps/48" \
    "${TARGET_HOME}/.local/share/icons/breeze-dark/apps/scalable" \
    "${TARGET_HOME}/.local/share/wallpapers/TianxiaEtherealSpace" \
    "${TARGET_HOME}/.local/share/color-schemes" \
    "${TARGET_HOME}/.local/share/plasma/desktoptheme/TianxiaEtherealGlass" \
    "${TARGET_HOME}/.local/share/ksplash/Themes/com.rasaxmachina.tianxiaos.splash" \
    "${TARGET_HOME}/.local/share/plasma/look-and-feel/com.rasaxmachina.tianxiaos.desktop" \
    "${TARGET_HOME}/.local/share/konsole" \
    "${TARGET_HOME}/.config/gtk-3.0" \
    "${TARGET_HOME}/.config/gtk-4.0" \
    "${TARGET_HOME}/.config/foot" \
    "${TARGET_HOME}/.config/xsettingsd"

cp -rf /var/lib/tianxia/brand-theme/fonts/. "${TARGET_HOME}/.local/share/fonts/tianxia-brand/"
cp -rf /var/lib/tianxia/brand-theme/icons/hicolor/. "${TARGET_HOME}/.local/share/icons/hicolor/"
if [ -f /run/current-system/sw/share/icons/hicolor/index.theme ]; then
    cp -f /run/current-system/sw/share/icons/hicolor/index.theme "${TARGET_HOME}/.local/share/icons/hicolor/index.theme"
    cp -f /run/current-system/sw/share/icons/hicolor/index.theme /usr/local/share/icons/hicolor/index.theme
fi

# Mirror scalable & 48px PNGs into user breeze-dark override so KIconLoader finds every custom icon immediately
for svg_file in "${TARGET_HOME}/.local/share/icons/hicolor/scalable/apps/"*.svg; do
    [ -e "${svg_file}" ] || continue
    base_svg="${svg_file##*/}"
    cp -f "${svg_file}" "${TARGET_HOME}/.local/share/icons/breeze-dark/apps/scalable/${base_svg}"
done
for png_file in "${TARGET_HOME}/.local/share/icons/hicolor/48x48/apps/"*.png; do
    [ -e "${png_file}" ] || continue
    base_png="${png_file##*/}"
    cp -f "${png_file}" "${TARGET_HOME}/.local/share/icons/breeze-dark/apps/48/${base_png}"
done

cp -rf /var/lib/tianxia/brand-theme/wallpapers/TianxiaEtherealSpace/. "${TARGET_HOME}/.local/share/wallpapers/TianxiaEtherealSpace/"
cp -f "${TARGET_HOME}/.local/share/icons/hicolor/256x256/apps/rxm-logo.png" "${TARGET_HOME}/.face"
ln -sfn "${TARGET_HOME}/.face" "${TARGET_HOME}/.face.icon"
cp -f /var/lib/tianxia/brand-theme/color-schemes/TianxiaEtherealDark.colors "${TARGET_HOME}/.local/share/color-schemes/TianxiaEtherealDark.colors"
cp -rf /var/lib/tianxia/brand-theme/desktoptheme/TianxiaEtherealGlass/. "${TARGET_HOME}/.local/share/plasma/desktoptheme/TianxiaEtherealGlass/"
cp -rf /var/lib/tianxia/brand-theme/ksplash/com.rasaxmachina.tianxiaos.splash/. "${TARGET_HOME}/.local/share/ksplash/Themes/com.rasaxmachina.tianxiaos.splash/"
cp -rf /var/lib/tianxia/brand-theme/ksplash/com.rasaxmachina.tianxiaos.splash/. "${TARGET_HOME}/.local/share/plasma/look-and-feel/com.rasaxmachina.tianxiaos.desktop/"

# Update look-and-feel metadata Id so both KSplash and LookAndFeel resolve cleanly
{
    printf '%s\n' '{'
    printf '%s\n' '    "KPlugin": {'
    printf '%s\n' '        "Authors": [{ "Name": "RASA-X-MACHINA" }],'
    printf '%s\n' '        "Comment": "Ethereal Glass on Deep Space Global Theme for tianxiaOS",'
    printf '%s\n' '        "Id": "com.rasaxmachina.tianxiaos.desktop",'
    printf '%s\n' '        "License": "LicenseRef-Proprietary",'
    printf '%s\n' '        "Name": "RASA-X-MACHINA · tianxiaOS",'
    printf '%s\n' '        "Website": "https://rasaxmachina.com"'
    printf '%s\n' '    },'
    printf '%s\n' '    "X-Plasma-APIVersion": "2"'
    printf '%s\n' '}'
} > "${TARGET_HOME}/.local/share/plasma/look-and-feel/com.rasaxmachina.tianxiaos.desktop/metadata.json"

# GTK 3/4, xsettingsd, Foot & Konsole parity
cp -f /var/lib/tianxia/brand-theme/gtk/settings.ini "${TARGET_HOME}/.config/gtk-3.0/settings.ini"
cp -f /var/lib/tianxia/brand-theme/gtk/settings.ini "${TARGET_HOME}/.config/gtk-4.0/settings.ini"
cp -f /var/lib/tianxia/brand-theme/gtk/gtk.css "${TARGET_HOME}/.config/gtk-3.0/gtk.css"
cp -f /var/lib/tianxia/brand-theme/gtk/gtk.css "${TARGET_HOME}/.config/gtk-4.0/gtk.css"
cp -f /var/lib/tianxia/brand-theme/foot/foot.ini "${TARGET_HOME}/.config/foot/foot.ini"
cp -f /var/lib/tianxia/brand-theme/konsole/TianxiaEthereal.colorscheme "${TARGET_HOME}/.local/share/konsole/TianxiaEthereal.colorscheme"
cp -f /var/lib/tianxia/brand-theme/konsole/tianxiaOS.profile "${TARGET_HOME}/.local/share/konsole/tianxiaOS.profile"

{
    printf '%s\n' 'Net/ThemeName "Breeze-Dark"'
    printf '%s\n' 'Net/IconThemeName "breeze-dark"'
    printf '%s\n' 'Gtk/CursorThemeName "breeze_cursors"'
    printf '%s\n' 'Gtk/FontName "Plus Jakarta Sans,  10"'
    printf '%s\n' 'Xft/Antialias 1'
    printf '%s\n' 'Xft/Hinting 1'
    printf '%s\n' 'Xft/HintStyle "hintslight"'
    printf '%s\n' 'Xft/RGBA "rgb"'
} > "${TARGET_HOME}/.config/xsettingsd/xsettingsd.conf"

{
    printf '%s\n' '[Desktop Entry]'
    printf '%s\n' 'DefaultProfile=tianxiaOS.profile'
    printf '%s\n' ''
    printf '%s\n' '[MainWindow]'
    printf '%s\n' 'MenuBar=Disabled'
} > "${TARGET_HOME}/.config/konsolerc"

{
    printf '%s\n' '[General]'
    printf 'LogoPath=%s/.local/share/icons/hicolor/512x512/apps/tianxiaos-logo.png\n' "${TARGET_HOME}"
    printf '%s\n' 'Website=https://rasaxmachina.com'
    printf '%s\n' 'Variant=v8.7.0 Crownforge · RASA-X-MACHINA Sovereign Substrate'
    printf '%s\n' 'UseOSReleaseVersion=false'
    printf '%s\n' 'Version=8.7.0 (NixOS 26.11 Wayland)'
} > "${TARGET_HOME}/.config/kcm-about-distrorc"

# 3. Write KDE Plasma 6 configuration keys via kwriteconfig6
run_user() {
    sudo -u "${TARGET_USER}" \
        HOME="${TARGET_HOME}" \
        XDG_RUNTIME_DIR="/run/user/${TARGET_UID}" \
        WAYLAND_DISPLAY="wayland-0" \
        DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/${TARGET_UID}/bus" \
        "$@"
}

KW="$(command -v kwriteconfig6 2>/dev/null || printf '/run/current-system/sw/bin/kwriteconfig6')"
if [ -x "${KW}" ]; then
    # Fonts & Icons & ColorScheme in kdeglobals (Zero Inter/Roboto/Arial!)
    run_user "${KW}" --file kdeglobals --group General --key ColorScheme "TianxiaEtherealDark"
    run_user "${KW}" --file kdeglobals --group General --key AccentColor "124,92,255"
    run_user "${KW}" --file kdeglobals --group General --key font "Plus Jakarta Sans,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
    run_user "${KW}" --file kdeglobals --group General --key menuFont "Plus Jakarta Sans,10,-1,5,500,0,0,0,0,0,0,0,0,0,0,1"
    run_user "${KW}" --file kdeglobals --group General --key toolBarFont "Space Grotesk,10,-1,5,500,0,0,0,0,0,0,0,0,0,0,1"
    run_user "${KW}" --file kdeglobals --group General --key smallestReadableFont "Plus Jakarta Sans,9,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"
    run_user "${KW}" --file kdeglobals --group General --key fixed "JetBrains Mono,10,-1,5,500,0,0,0,0,0,0,0,0,0,0,1"
    run_user "${KW}" --file kdeglobals --group WM --key activeFont "Space Grotesk,10,-1,5,700,0,0,0,0,0,0,0,0,0,0,1"
    run_user "${KW}" --file kdeglobals --group WM --key activeBackground "10,10,18"
    run_user "${KW}" --file kdeglobals --group WM --key activeBlend "124,92,255"
    run_user "${KW}" --file kdeglobals --group WM --key activeForeground "241,245,249"
    run_user "${KW}" --file kdeglobals --group WM --key inactiveBackground "7,7,12"
    run_user "${KW}" --file kdeglobals --group WM --key inactiveBlend "7,7,12"
    run_user "${KW}" --file kdeglobals --group WM --key inactiveForeground "136,146,172"
    run_user "${KW}" --file kdeglobals --group Icons --key Theme "breeze-dark"
    run_user "${KW}" --file kdeglobals --group KDE --key LookAndFeelPackage "com.rasaxmachina.tianxiaos.desktop"
    run_user "${KW}" --file kdeglobals --group KDE --key widgetStyle "Breeze"

    # Disable KWallet first-use modal nag (so Sovereign Aethervault handles secrets cleanly without KWallet popups)
    run_user "${KW}" --file kwalletrc --group Wallet --key "Enabled" "false"
    run_user "${KW}" --file kwalletrc --group Wallet --key "First Use" "false"
    rm -f "${TARGET_HOME}/.config/Trolltech.conf"
    run_user "${KW}" --file plasmarc --group Theme --key name "TianxiaEtherealGlass"

    # KSplash QML Boot/Session Splash
    run_user "${KW}" --file ksplashrc --group KSplash --key Engine "KSplashQML"
    run_user "${KW}" --file ksplashrc --group KSplash --key Theme "com.rasaxmachina.tianxiaos.splash"

    # Lockscreen Wallpaper
    run_user "${KW}" --file kscreenlockerrc --group Daemon --key Autolock "false"
    run_user "${KW}" --file kscreenlockerrc --group Greeter --group Wallpaper --group org.kde.image --group General --key Image "file://${TARGET_HOME}/.local/share/wallpapers/TianxiaEtherealSpace/contents/images/1920x1080.png"

    # Disable idle screen dimming (prevents 30% dimmed screenshots!)
    run_user "${KW}" --file powerdevilrc --group AC --group Display --key dimDisplayWhenIdle "false"
    run_user "${KW}" --file powerdevilrc --group AC --group Display --key DimDisplayWhenIdle "false"
    run_user "${KW}" --file powerdevilrc --group AC --group Display --key turnOffDisplayWhenIdle "false"
    run_user "${KW}" --file powerdevilrc --group Battery --group Display --key dimDisplayWhenIdle "false"
    run_user "${KW}" --file powerdevilrc --group Battery --group Display --key DimDisplayWhenIdle "false"
    run_user "${KW}" --file powerdevilrc --group Battery --group Display --key turnOffDisplayWhenIdle "false"

    # Floating Always-Visible Translucent Glass Navigation Panel (.tx-nav parity)
    run_user "${KW}" --file plasmashellrc --group PlasmaViews --group "Panel 2" --key floating "1"
    run_user "${KW}" --file plasmashellrc --group PlasmaViews --group "Panel 2" --key panelLengthMode "0"
    run_user "${KW}" --file plasmashellrc --group PlasmaViews --group "Panel 2" --key panelOpacity "2"
    run_user "${KW}" --file plasmashellrc --group PlasmaViews --group "Panel 2" --key panelVisibility "0"
    run_user "${KW}" --file plasmashellrc --group PlasmaViews --group "Panel 2" --group Defaults --key thickness "48"

    # KWin compositor effects + window icon rule so Wayland foot/python windows carry txOS emblem
    run_user "${KW}" --file kwinrc --group Plugins --key blurEnabled "true"
    run_user "${KW}" --file kwinrc --group Desktops --key Number "2"
    run_user "${KW}" --file kwinrc --group Desktops --key Name_1 "01 · SOVEREIGN OPS"
    run_user "${KW}" --file kwinrc --group Desktops --key Name_2 "02 · MESH & COCKPIT"
    run_user "${KW}" --file kwinrulesrc --group General --key count "1"
    run_user "${KW}" --file kwinrulesrc --group General --key rules "1"
    run_user "${KW}" --file kwinrulesrc --group 1 --key Description "tianxiaOS Terminal & Python Tools Branded Icon"
    run_user "${KW}" --file kwinrulesrc --group 1 --key wmclass "(foot|tianxiaos-terminal|tk|Toplevel)"
    run_user "${KW}" --file kwinrulesrc --group 1 --key wmclassmatch "3"
    run_user "${KW}" --file kwinrulesrc --group 1 --key desktopfile "tx-sovereign-tui"
    run_user "${KW}" --file kwinrulesrc --group 1 --key desktopfilerule "2"
fi

chown -R "${TARGET_USER}:users" "${TARGET_HOME}/.local" "${TARGET_HOME}/.config" 2>/dev/null || true
fc-cache -f /usr/local/share/fonts/tianxia-brand "${TARGET_HOME}/.local/share/fonts/tianxia-brand" 2>/dev/null || true
run_user fc-cache -f 2>/dev/null || true

if [ "${MODE}" = "--boot-sync" ]; then
    log_info "Boot sync completed."
    exit 0
fi

# 4. Live Wayland KDE Plasma 6 session apply (zero reboot required!)
if [ -S "/run/user/${TARGET_UID}/wayland-0" ]; then
    log_info "Applying live Ethereal Glass theme, wallpaper, txOS Start Button & floating panel on wayland-0..."

    # Rebuild KDE service/icon cache
    if command -v kbuildsycoca6 >/dev/null 2>&1; then
        run_user kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
    fi

    # Apply BreezeDark first then TianxiaEtherealDark so plasma-apply-colorscheme writes all [Colors:*] blocks into kdeglobals!
    run_user plasma-apply-colorscheme BreezeDark >/dev/null 2>&1 || true
    run_user plasma-apply-colorscheme TianxiaEtherealDark >/dev/null 2>&1 || true
    run_user plasma-apply-desktoptheme breeze-dark >/dev/null 2>&1 || true
    run_user plasma-apply-desktoptheme TianxiaEtherealGlass >/dev/null 2>&1 || true
    run_user plasma-apply-wallpaperimage "${TARGET_HOME}/.local/share/wallpapers/TianxiaEtherealSpace/contents/images/1920x1080.png" >/dev/null 2>&1 || true

    # Wake display from DPMS Off & idle 30% dimming via kscreen-doctor + ScreenSaver SimulateUserActivity
    run_user kscreen-doctor --dpms on >/dev/null 2>&1 || true
    run_user qdbus org.freedesktop.ScreenSaver /ScreenSaver SimulateUserActivity >/dev/null 2>&1 || true
    run_user qdbus org.kde.Solid.PowerManagement /org/kde/Solid/PowerManagement/Actions/BrightnessControl setBrightness 10000 >/dev/null 2>&1 || true
    systemctl --user -M "${TARGET_USER}@" restart plasma-powerdevil.service >/dev/null 2>&1 || true
    sleep 1
    run_user kscreen-doctor --dpms on >/dev/null 2>&1 || true
    run_user qdbus org.freedesktop.ScreenSaver /ScreenSaver SimulateUserActivity >/dev/null 2>&1 || true
    killall -HUP xsettingsd >/dev/null 2>&1 || true

    # Update Plasma Panel: txOS Start Button + Pinned Sovereign App Dock + Always Visible Floating Bar
    JS_PAYLOAD='
var allPanels = panels();
for (var i = 0; i < allPanels.length; i++) {
    var p = allPanels[i];
    p.floating = true;
    p.hiding = "none";
    p.lengthMode = "fill";
    p.opacity = "translucent";
    p.height = 48;
    var wlist = p.widgets();
    var hasIconTasks = false;
    for (var j = 0; j < wlist.length; j++) {
        var w = wlist[j];
        if (w.type === "org.kde.plasma.kickoff") {
            w.currentConfigGroup = ["General"];
            w.writeConfig("icon", "tianxiaos-start");
            w.writeConfig("favorites", [
                "tx-control-center-gui.desktop",
                "tx-cockpit-gui.desktop",
                "tx-vault-gui.desktop",
                "tx-topology-gui.desktop",
                "tx-sovereign-tui.desktop",
                "tx-ledger-tui.desktop",
                "org.kde.konsole.desktop",
                "org.kde.dolphin.desktop"
            ]);
            w.reloadConfig();
        }
        if (w.type === "org.kde.plasma.windowlist") {
            w.remove();
        }
        if (w.type === "org.kde.plasma.icontasks") {
            hasIconTasks = true;
            w.currentConfigGroup = ["General"];
            w.writeConfig("launchers", [
                "applications:tx-control-center-gui.desktop",
                "applications:tx-cockpit-gui.desktop",
                "applications:tx-vault-gui.desktop",
                "applications:tx-topology-gui.desktop",
                "applications:tx-ledger-tui.desktop",
                "applications:org.kde.konsole.desktop",
                "applications:org.kde.dolphin.desktop"
            ]);
            w.reloadConfig();
        }
    }
    if (!hasIconTasks) {
        var it = p.addWidget("org.kde.plasma.icontasks");
        it.currentConfigGroup = ["General"];
        it.writeConfig("launchers", [
            "applications:tx-control-center-gui.desktop",
            "applications:tx-cockpit-gui.desktop",
            "applications:tx-vault-gui.desktop",
            "applications:tx-topology-gui.desktop",
            "applications:tx-ledger-tui.desktop",
            "applications:org.kde.konsole.desktop",
            "applications:org.kde.dolphin.desktop"
        ]);
        it.reloadConfig();
        p.currentConfigGroup = ["General"];
        var ord = p.readConfig("AppletOrder", "");
        if (ord.indexOf(";" + it.id) !== -1) {
            var cleaned = ord.replace(";" + it.id, "");
            p.writeConfig("AppletOrder", cleaned.replace("3;4;", "3;4;" + it.id + ";"));
        }
    }
}
var ds = desktops();
for (var k = 0; k < ds.length; k++) {
    var d = ds[k];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    d.writeConfig("Image", "file://'"${TARGET_HOME}"'/.local/share/wallpapers/TianxiaEtherealSpace/contents/images/1920x1080.png");
    d.reloadConfig();
}
'
    run_user qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "${JS_PAYLOAD}" >/dev/null 2>&1 || true

    # Reconfigure KWin & restart plasma-plasmashell.service cleanly so every theme/font/panel widget renders crisp
    run_user qdbus org.kde.KWin /KWin reconfigure >/dev/null 2>&1 || true
    systemctl --user -M "${TARGET_USER}@" restart plasma-plasmashell.service >/dev/null 2>&1 || true
    sleep 4
    run_user kscreen-doctor --dpms on >/dev/null 2>&1 || true
    log_info "Live Plasma 6 reload complete."
fi

exit 0

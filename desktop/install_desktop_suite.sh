#!/usr/bin/env bash
# ffp: FFP-DESKTOP-INSTALLER content-pipeline bash
# SLECO-SO++ Installer for TianxiaOS GTK4/Libadwaita GUIs, 9 Rust TUIs & 13 .desktop Launchers
set +e
set +u

SCRIPT_PATH="${0}"
SRC_DIR="${SCRIPT_PATH%/*}"
if [ "${SRC_DIR}" = "${SCRIPT_PATH}" ]; then
    SRC_DIR="."
fi

MODE="${1:---local-gen}"
LOCAL_APPS_DIR="${SRC_DIR}/applications"
mkdir -p "${LOCAL_APPS_DIR}"

write_wrapper() {
    local dest="$1"
    local js_name="$2"
    local ffp_id="$3"
    {
        printf '%s\n' '#!/usr/bin/env bash'
        printf '# ffp: %s frontend bash\n' "${ffp_id}"
        printf '%s\n' 'set +e'
        printf '%s\n' 'set +u'
        printf 'exec /var/lib/tianxia/bin/tx-gjs-run.sh "/var/lib/tianxia/bin/%s" "$@"\n' "${js_name}"
    } > "${dest}"
    chmod 0755 "${dest}"
}

write_desktop_entry() {
    local out_file="$1"
    local name="$2"
    local comment="$3"
    local exec_cmd="$4"
    local icon="$5"
    local categories="$6"
    local wm_class="$7"
    {
        printf '%s\n' '[Desktop Entry]'
        printf '%s\n' 'Version=1.5'
        printf '%s\n' 'Type=Application'
        printf 'Name=%s\n' "${name}"
        printf 'Comment=%s\n' "${comment}"
        printf 'Exec=%s\n' "${exec_cmd}"
        printf 'Icon=%s\n' "${icon}"
        printf '%s\n' 'Terminal=false'
        printf 'Categories=%s\n' "${categories}"
        printf 'StartupWMClass=%s\n' "${wm_class}"
        printf '%s\n' 'Keywords=Tianxia;Sovereign;RasaXMachina;Security;Mesh;TUI;GUI;'
    } > "${out_file}"
    chmod 0644 "${out_file}"
}

generate_all_desktop_files() {
    local dir="$1"
    mkdir -p "${dir}"

    write_desktop_entry "${dir}/tx-control-center-gui.desktop" \
        "tianxiaOS Control Center" \
        "RASA-X-MACHINA · 14 Mahavidya Domains, Build Law Seal & 1-Click Sovereign Matrix" \
        "/usr/local/bin/tx-control-center-gui" \
        "tx-app-control-center" \
        "System;Settings;Utility;" \
        "com.rasaxmachina.TianxiaControlCenter"

    write_desktop_entry "${dir}/tx-vault-gui.desktop" \
        "tianxiaOS Aethervault & GDPR++" \
        "Zero-Knowledge Vault Health, Live SecretShield Scrubber & <50ms Cryptoshred Verifier" \
        "/usr/local/bin/tx-vault-gui" \
        "tx-app-vault" \
        "System;Security;" \
        "com.rasaxmachina.TianxiaVault"

    write_desktop_entry "${dir}/tx-topology-gui.desktop" \
        "tianxiaOS Mesh & Murua Topology" \
        "5-Node Sovereign Mesh, Rosenpass PQ Transit, Thermal Readout & Murua Tracer" \
        "/usr/local/bin/tx-topology-gui" \
        "tx-app-topology" \
        "Network;System;Monitor;" \
        "com.rasaxmachina.TianxiaTopology"

    write_desktop_entry "${dir}/tx-cockpit-gui.desktop" \
        "tianxiaOS Sovereign Cockpit PWA" \
        "RASA-X-MACHINA · Dedicated Sovereign Cockpit (:8081) Wayland Chromeless Dashboard" \
        "/usr/local/bin/tx-cockpit-gui" \
        "tx-app-cockpit" \
        "Network;System;" \
        "TianxiaCockpitPWA"

    write_desktop_entry "${dir}/tx-sovereign-tui.desktop" \
        "tianxiaOS Sovereign Suite (9-App TUI)" \
        "Full 9-Tab Raw-Terminal Sovereign TUI (Overview, Scour, Miner, Ledger, DSS-14, Models, Tracer)" \
        "foot -T \"tianxiaOS Sovereign Suite (9-App TUI)\" /usr/local/bin/tianxia tui --app overview" \
        "tx-app-tui" \
        "System;Monitor;ConsoleOnly;" \
        "tianxiaos-terminal"

    write_desktop_entry "${dir}/tx-scour-tui.desktop" \
        "tianxiaOS Scour Intelligence TUI" \
        "Real-Time ArXiv, GitHub, DeFiLlama, Threat & x402 Merged Signal Feed" \
        "foot -T \"tianxiaOS Scour Intelligence TUI\" /usr/local/bin/tianxia tui --app scour" \
        "tx-app-scour" \
        "Network;System;ConsoleOnly;" \
        "tianxiaos-terminal"

    write_desktop_entry "${dir}/tx-miner-tui.desktop" \
        "tianxiaOS Opportunity Miner TUI" \
        "SFI Priority Matrix (Rank=P+C+A+E+F) & B2B Vacancy-to-Sprint Pipeline" \
        "foot -T \"tianxiaOS Opportunity Miner TUI\" /usr/local/bin/tianxia tui --app miner" \
        "tx-app-miner" \
        "Office;Finance;ConsoleOnly;" \
        "tianxiaos-terminal"

    write_desktop_entry "${dir}/tx-ledger-tui.desktop" \
        "tianxiaOS TetraLedger 4-Way TUI" \
        "4-Way Cryptographic Settlement (Payfac, Web3 Base L2, SQLite WAL, Open Banking)" \
        "foot -T \"tianxiaOS TetraLedger 4-Way TUI\" /usr/local/bin/tianxia tui --app ledger" \
        "tx-app-ledger" \
        "Finance;System;ConsoleOnly;" \
        "tianxiaos-terminal"

    write_desktop_entry "${dir}/tx-dss14-tui.desktop" \
        "tianxiaOS DSS-14.2 Domains TUI" \
        "14 Mahavidya Domains & Dasavidyayana NL PARAMASIVA Release Gate" \
        "foot -T \"tianxiaOS DSS-14.2 Domains TUI\" /usr/local/bin/tianxia tui --app dss14" \
        "tx-app-dss14" \
        "System;Security;ConsoleOnly;" \
        "tianxiaos-terminal"

    write_desktop_entry "${dir}/tx-etamanga-tui.desktop" \
        "tianxiaOS Etamanga & x402 TUI" \
        "Base L2 Efemera (EFM) Contracts, x402 Micropayment Gateway & Multi-Fiat Compliance" \
        "foot -T \"tianxiaOS Etamanga & x402 TUI\" /usr/local/bin/tianxia tui --app etamanga" \
        "tx-app-etamanga" \
        "Finance;Network;ConsoleOnly;" \
        "tianxiaos-terminal"

    write_desktop_entry "${dir}/tx-fortress-tui.desktop" \
        "tianxiaOS Faery Fortress TUI" \
        "Cgroup v2 Containment, Wayland virtwl Gate, Rosenpass PQ & SecretShield Posture" \
        "foot -T \"tianxiaOS Faery Fortress TUI\" /usr/local/bin/tianxia tui --app fortress" \
        "tx-app-fortress" \
        "Security;System;ConsoleOnly;" \
        "tianxiaos-terminal"

    write_desktop_entry "${dir}/tx-models-tui.desktop" \
        "tianxiaOS Sovereign LLM Swarm TUI" \
        "Constructal Sine-Meander Router & 10 Local Quantized Sovereign Models" \
        "foot -T \"tianxiaOS Sovereign LLM Swarm TUI\" /usr/local/bin/tianxia tui --app models" \
        "tx-app-models" \
        "Development;Science;ConsoleOnly;" \
        "tianxiaos-terminal"

    write_desktop_entry "${dir}/tx-tracer-tui.desktop" \
        "tianxiaOS Murua Consignment TUI" \
        "Bayesian Untracked Consignment Tracer & UPU 2IPD Corridor Engine" \
        "foot -T \"tianxiaOS Murua Consignment TUI\" /usr/local/bin/tianxia tui --app tracer" \
        "tx-app-tracer" \
        "Network;Utility;ConsoleOnly;" \
        "tianxiaos-terminal"
}

generate_all_desktop_files "${LOCAL_APPS_DIR}"
write_wrapper "${SRC_DIR}/tx-control-center-gui" "tx-control-center-gui.js" "FFP-WRAP-CONTROL-GUI"
write_wrapper "${SRC_DIR}/tx-vault-gui" "tx-vault-gui.js" "FFP-WRAP-VAULT-GUI"
write_wrapper "${SRC_DIR}/tx-topology-gui" "tx-topology-gui.js" "FFP-WRAP-TOPOLOGY-GUI"
write_wrapper "${SRC_DIR}/tx-cockpit-gui" "tx-cockpit-gui.js" "FFP-WRAP-COCKPIT-GUI"

if [ "${MODE}" = "--install-host" ]; then
    mkdir -p /var/lib/tianxia/bin /usr/local/bin /usr/local/share/applications /root/.local/share/applications

    cp -f "${SRC_DIR}/tx-gjs-run.sh" /var/lib/tianxia/bin/tx-gjs-run.sh
    chmod 0755 /var/lib/tianxia/bin/tx-gjs-run.sh

    for js in tx-control-center-gui.js tx-vault-gui.js tx-topology-gui.js tx-cockpit-gui.js; do
        cp -f "${SRC_DIR}/${js}" "/var/lib/tianxia/bin/${js}"
        chmod 0755 "/var/lib/tianxia/bin/${js}"
    done

    for gui in tx-control-center-gui tx-vault-gui tx-topology-gui tx-cockpit-gui; do
        cp -f "${SRC_DIR}/${gui}" "/var/lib/tianxia/bin/${gui}"
        cp -f "${SRC_DIR}/${gui}" "/usr/local/bin/${gui}"
        chmod 0755 "/var/lib/tianxia/bin/${gui}" "/usr/local/bin/${gui}"
    done

    for tui_bin in tx-sovereign-tui tx-scour-tui tx-miner-tui tx-ledger-tui tx-dss14-tui tx-etamanga-tui tx-fortress-tui tx-models-tui tx-tracer-tui; do
        ln -sfn /usr/local/bin/tianxia "/usr/local/bin/${tui_bin}"
        ln -sfn /var/lib/tianxia/bin/tianxia "/var/lib/tianxia/bin/${tui_bin}"
    done

    generate_all_desktop_files "/usr/local/share/applications"
    generate_all_desktop_files "/root/.local/share/applications"
    if [ -d "/home/tianxia" ]; then
        mkdir -p /home/tianxia/.local/share/applications
        generate_all_desktop_files "/home/tianxia/.local/share/applications"
        chown -R tianxia:users /home/tianxia/.local/share/applications 2>/dev/null || true
    fi

    rm -f /dev/shm/tx_gjs_runtime_env.sh
    printf '[install_desktop_suite] Installed 4 GTK4/Adw GUIs, 9 Rust TUI entrypoints & 13 .desktop launchers.\n'
fi

exit 0

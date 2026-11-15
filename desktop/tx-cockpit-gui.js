// ffp: FFP-GUI-COCKPIT-LAUNCHER frontend javascript
// Sovereign Cockpit PWA Launcher & Native Status Bridge (GTK4 + Libadwaita)
// Launches http://127.0.0.1:8081 in a chromeless Wayland window or presents a GTK4 fallback cockpit.

import GLib from 'gi://GLib';
import Gio from 'gi://Gio';
import Gdk from 'gi://Gdk?version=4.0';
import Gtk from 'gi://Gtk?version=4.0';
import Adw from 'gi://Adw?version=1';
import System from 'system';

function resolveCockpitUrl() {
    const envUrl = GLib.getenv('TX_COCKPIT_URL');
    if (envUrl) return envUrl;
    const candidates = ['http://127.0.0.1:8081'];
    try {
        const ts = Gio.Subprocess.new(
            ['tailscale', 'ip', '-4'],
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE
        );
        const [, out] = ts.communicate_utf8(null, null);
        const ip = (out || '').split('\n')[0].trim();
        if (ip) candidates.unshift(`http://${ip}:8081`);
    } catch (_e) {}
    for (const url of candidates) {
        try {
            const p = Gio.Subprocess.new(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-m', '1', `${url}/`],
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE
            );
            const [, code] = p.communicate_utf8(null, null);
            if ((code || '').trim() === '200') return url;
        } catch (_e) {}
    }
    return candidates[0];
}

const COCKPIT_URL = resolveCockpitUrl();

function probeCockpitHttp() {
    try {
        const proc = Gio.Subprocess.new(
            ['curl', '-sS', '-m', '2', `${COCKPIT_URL}/api/status`],
            Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE
        );
        const [, stdout] = proc.communicate_utf8(null, null);
        if (proc.get_successful() && stdout) {
            return { ok: true, body: stdout.trim() };
        }
    } catch (_e) {
        // Handled cleanly
    }
    return { ok: false, body: '' };
}

function findChromelessBrowser() {
    const candidates = [
        '/run/current-system/sw/bin/chromium',
        'chromium',
    ];
    for (const c of candidates) {
        if (GLib.find_program_in_path(c)) {
            return c;
        }
    }
    return null;
}

const args = ARGV || [];
if (args.includes('--check')) {
    const probe = probeCockpitHttp();
    const browser = findChromelessBrowser() || 'gtk4-fallback';
    print(`SELF_TEST_OK: tx-cockpit-gui url=${COCKPIT_URL} api_200=${probe.ok} launcher=${browser}`);
    System.exit(0);
}

const browserBin = findChromelessBrowser();
if (browserBin && !args.includes('--native')) {
    try {
        Gio.Subprocess.new(
            [
                browserBin,
                '--no-first-run',
                '--no-default-browser-check',
                '--password-store=basic',
                '--ozone-platform=wayland',
                `--app=${COCKPIT_URL}`,
                '--class=TianxiaCockpitPWA',
            ],
            Gio.SubprocessFlags.NONE
        );
        System.exit(0);
    } catch (_e) {
        // Fall through to native GTK4/Libadwaita Cockpit window
    }
}

Adw.init();
const app = new Adw.Application({
    application_id: 'com.rasaxmachina.TianxiaCockpit',
    flags: Gio.ApplicationFlags.NON_UNIQUE,
});

app.connect('activate', () => {
    Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK);
    const css = new Gtk.CssProvider();
    css.load_from_string(`
        window, .background { background-color: #080808; color: #f8fafc; }
        headerbar { background-color: #0a0a12; color: #c084fc; border-bottom: 1px solid #7c5cff; }
        .cockpit-pre { background-color: #0a0a12; border: 1px solid #a855f7; border-radius: 10px; padding: 14px; font-family: monospace; color: #22d3ee; }
    `);
    const disp = Gdk.Display.get_default();
    if (disp) {
        Gtk.StyleContext.add_provider_for_display(disp, css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION);
    }

    const win = new Adw.ApplicationWindow({
        application: app,
        title: `tianxiaOS Sovereign Cockpit (${COCKPIT_URL}) · RASA-X-MACHINA`,
        default_width: 820,
        default_height: 560,
    });
    const tv = new Adw.ToolbarView();
    tv.add_top_bar(new Adw.HeaderBar());

    const box = new Gtk.Box({
        orientation: Gtk.Orientation.VERTICAL,
        spacing: 14,
        margin_top: 18,
        margin_bottom: 18,
        margin_start: 18,
        margin_end: 18,
    });
    const probe = probeCockpitHttp();
    const lbl = new Gtk.Label({
        xalign: 0,
        wrap: true,
        selectable: true,
        label: `Sovereign Cockpit Endpoint: ${COCKPIT_URL}/api/status (${probe.ok ? '200 OK' : 'OFFLINE'})\n\n${probe.body}`,
    });
    lbl.add_css_class('cockpit-pre');

    const openBtn = new Gtk.Button({ label: `Open ${COCKPIT_URL} via xdg-open` });
    openBtn.connect('clicked', () => {
        try {
            Gio.Subprocess.new(['xdg-open', COCKPIT_URL], Gio.SubprocessFlags.NONE);
        } catch (_e) {}
    });

    box.append(lbl);
    box.append(openBtn);
    tv.set_content(box);
    win.set_content(tv);
    win.present();
});

app.run([]);

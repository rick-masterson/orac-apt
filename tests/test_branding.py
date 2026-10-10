"""packaging/orac-branding: pin the two theme defects found when packaging it.

The Plymouth script shipped in the theme zip called Sprite.SetScale and Plymouth.GetTime, neither
of which exists in Plymouth's script plugin, so its progress bar and background animation never
moved; its password sprites were function locals, which vanish on return. (It also called
Plymouth.SetMessageFunction, first recorded here as nonexistent too. It is a valid alias for
SetDisplayMessageFunction, defined in Plymouth's script-lib-plymouth.script; corrected 2026-09-25.)
The KSplash QML assigned a bare `letterSpacing`, which is not a Text property, so the whole splash
failed to load. Neither is visible without booting.
"""
import os
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "packages" / "orac-branding" / "root" / "usr" / "share"
SCRIPT = ROOT / "plymouth" / "themes" / "orac" / "orac.script"
SPLASH = ROOT / "plasma" / "look-and-feel" / "org.orac.workstation" / "contents" / "splash" / "Splash.qml"

# Plymouth's script plugin (src/plugins/splash/script/script-lib-*.c): the callbacks a
# theme can register, and the Sprite methods. A Sprite has no scale; its Image does.
PLYMOUTH_SETTERS = {
    "SetRefreshFunction", "SetBootProgressFunction", "SetRootMountedFunction",
    "SetKeyboardInputFunction", "SetUpdateStatusFunction", "SetDisplayNormalFunction",
    "SetDisplayPasswordFunction", "SetDisplayQuestionFunction", "SetDisplayPromptFunction",
    "SetDisplayMessageFunction", "SetHideMessageFunction", "SetQuitFunction",
    "SetSystemUpdateFunction", "SetValidateInputFunction", "SetDisplayHotplugFunction",
    "SetRefreshRate", "GetMode", "GetCapslockState",
    "SetMessageFunction",  # alias of SetDisplayMessageFunction (script-lib-plymouth.script)
}
SPRITE_METHODS = {"SetImage", "GetImage", "SetX", "SetY", "SetZ", "GetX", "GetY", "GetZ",
                  "SetPosition", "SetOpacity", "GetOpacity"}


class TestPlymouthScript(unittest.TestCase):
    def setUp(self):
        self.src = SCRIPT.read_text(encoding="utf-8")
        self.code = "\n".join(line.split("#", 1)[0] for line in self.src.splitlines())

    def test_only_real_plymouth_callbacks(self):
        used = set(re.findall(r"\bPlymouth\.(\w+)", self.code))
        self.assertTrue(used, "script registers no callbacks")
        self.assertEqual(used - PLYMOUTH_SETTERS, set())

    def test_progress_and_messages_are_wired(self):
        for setter in ("SetBootProgressFunction", "SetDisplayMessageFunction", "SetDisplayPasswordFunction"):
            self.assertIn(f"Plymouth.{setter}(", self.code)

    def test_sprites_are_never_scaled(self):
        for call in re.findall(r"\.sprite\.(\w+)\(", self.code):
            self.assertIn(call, SPRITE_METHODS)
        self.assertNotIn("SetScale", self.code)

    def test_braces_balance(self):
        self.assertEqual(self.code.count("{"), self.code.count("}"))
        self.assertEqual(self.code.count("("), self.code.count(")"))

    def test_every_image_ships(self):
        for name in re.findall(r'Image\("([^"]+)"\)', self.code):
            self.assertTrue((SCRIPT.parent / name).is_file(), name)


class TestSplashQml(unittest.TestCase):
    def test_letter_spacing_is_a_font_property(self):
        src = SPLASH.read_text(encoding="utf-8")
        self.assertNotRegex(src, r"(?m)^\s*letterSpacing\s*:")

    def test_qml_loads_without_errors(self):
        try:
            from PyQt6.QtCore import QUrl
            from PyQt6.QtGui import QGuiApplication
            from PyQt6.QtQuick import QQuickView
        except ImportError:
            self.skipTest("PyQt6 with QtQuick is not installed")
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
        view = QQuickView()
        view.setSource(QUrl.fromLocalFile(str(SPLASH)))
        self.assertEqual([e.toString() for e in view.errors()], [])
        self.assertIsNotNone(view.rootObject())
        view.rootObject().setProperty("stage", 3)
        del app


class TestLookAndFeel(unittest.TestCase):
    """Plasma 6 finds a look-and-feel only by its metadata.json; metadata.desktop is ignored."""

    def test_metadata_json_names_the_package(self):
        import json
        meta = json.loads((SPLASH.parents[2] / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["KPlugin"]["Id"], "org.orac.workstation")
        self.assertEqual(meta["KPackageStructure"], "Plasma/LookAndFeel")


class TestTerminalBanner(unittest.TestCase):
    """The fastfetch banner and orac-terminal-theme: a user's own config must survive apply/revert."""

    CONFIG = ROOT / "orac" / "fastfetch" / "config.jsonc"
    TOOL = ROOT.parent / "bin" / "orac-terminal-theme"

    def test_config_points_at_the_packaged_logo(self):
        import json
        text = "\n".join(l for l in self.CONFIG.read_text(encoding="utf-8").splitlines()
                         if not l.lstrip().startswith("//"))
        logo = Path(json.loads(text)["logo"]["source"])
        self.assertEqual(logo, Path("/usr/share/orac/fastfetch/logo.txt"))
        self.assertTrue((ROOT / logo.relative_to("/usr/share")).is_file())

    def test_apply_then_revert_restores_the_users_config(self):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as home:
            cfg = Path(home, ".config", "fastfetch", "config.jsonc")
            cfg.parent.mkdir(parents=True)
            cfg.write_text("users own banner\n")
            tool = Path(home, "tool.sh")
            tool.write_text(re.sub(r"(?m)^src=.*$", f"src={self.CONFIG}", self.TOOL.read_text()))
            env = {"HOME": home, "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
            run = lambda *a: subprocess.run(["sh", str(tool), *a], env=env, check=True, capture_output=True)
            run("apply")
            self.assertEqual(cfg.read_bytes(), self.CONFIG.read_bytes())
            run("apply")  # re-applying must not replace the backup with ORAC's own config
            run("revert")
            self.assertEqual(cfg.read_text(), "users own banner\n")


class TestLoginMessage(unittest.TestCase):
    """postinst/postrm take over /etc/motd only while it is Shadowfetch's stock copy, and give it back."""

    PKG = ROOT.parent.parent.parent
    STOCK = "Shadowfetch Linux \"Umbra\"\n"

    def setUp(self):
        import tempfile
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "etc").mkdir()
        (self.root / "usr/share/shadowfetch").mkdir(parents=True)
        (self.root / "usr/share/shadowfetch/motd").write_text(self.STOCK)
        # Stub the tools the scripts call, so nothing touches the real system.
        stubs = self.root / "stubs"
        stubs.mkdir()
        (stubs / "update-alternatives").write_text("#!/bin/sh\nexit 0\n")
        (stubs / "update-alternatives").chmod(0o755)
        self.env = {"DPKG_ROOT": str(self.root), "PATH": f"{stubs}:/usr/bin:/bin"}
        self.motd = self.root / "etc/motd"
        self.backup = self.root / "etc/motd.pre-orac"

    def tearDown(self):
        self._tmp.cleanup()

    def script(self, name, *args):
        import subprocess
        subprocess.run(["sh", str(self.PKG / "DEBIAN" / name), *args], env=self.env, check=True,
                       capture_output=True)

    def test_stock_motd_is_replaced_and_restored_on_remove(self):
        self.motd.write_text(self.STOCK)
        self.script("postinst", "configure", "")
        self.assertEqual(os.readlink(self.motd), "/usr/share/orac/motd")
        self.assertEqual(self.backup.read_text(), self.STOCK)
        self.script("postinst", "configure", "1.2.0-1")  # upgrade: idempotent
        self.assertEqual(self.backup.read_text(), self.STOCK)
        self.script("postrm", "remove")
        self.assertFalse(self.motd.is_symlink())
        self.assertEqual(self.motd.read_text(), self.STOCK)
        self.assertFalse(self.backup.exists())

    def test_hand_edited_motd_is_left_alone(self):
        self.motd.write_text("my own message\n")
        self.script("postinst", "configure", "")
        self.assertFalse(self.motd.is_symlink())
        self.assertEqual(self.motd.read_text(), "my own message\n")
        self.assertFalse(self.backup.exists())
        self.script("postrm", "remove")
        self.assertEqual(self.motd.read_text(), "my own message\n")

    def test_missing_motd_is_created_and_removed(self):
        self.script("postinst", "configure", "")
        self.assertEqual(os.readlink(self.motd), "/usr/share/orac/motd")
        self.script("postrm", "purge")
        self.assertFalse(self.motd.exists() or self.motd.is_symlink())

    def test_orac_motd_ships(self):
        self.assertIn("ORAC WORKSTATION", (ROOT / "orac" / "motd").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()


class TestBootTheme(unittest.TestCase):
    """orac-boot-theme: GRUB and SDDM drop-ins sort after Shadowfetch's and are removed on revert."""

    TOOL = ROOT.parent / "sbin" / "orac-boot-theme"

    def run_tool(self, root, *args):
        import subprocess
        env = {"DPKG_ROOT": root, "PATH": os.environ.get("PATH", "/usr/bin:/bin")}
        return subprocess.run(["sh", str(self.TOOL), *args], env=env, check=True,
                              capture_output=True, text=True).stdout

    def test_apply_then_revert_in_a_scratch_root(self):
        import tempfile
        with tempfile.TemporaryDirectory() as root:
            self.run_tool(root, "apply")
            grub = Path(root, "etc/default/grub.d/99-orac.cfg").read_text()
            sddm = Path(root, "etc/sddm.conf.d/99-orac.conf").read_text()
            self.assertIn("GRUB_THEME=/usr/share/grub/themes/orac/theme.txt", grub)
            self.assertIn("Current=orac", sddm)
            self.assertIn("CursorTheme=Orac", sddm)
            # Drop-ins load in name order; ORAC's must come after Shadowfetch's 10-shadowfetch.
            self.assertGreater("99-orac.cfg", "10-shadowfetch.cfg")
            self.assertIn("boot menu:  orac", self.run_tool(root, "status"))
            self.run_tool(root, "revert")
            self.assertFalse(Path(root, "etc/default/grub.d/99-orac.cfg").exists())
            self.assertFalse(Path(root, "etc/sddm.conf.d/99-orac.conf").exists())

    def test_drop_ins_point_at_shipped_themes(self):
        text = self.TOOL.read_text()
        for theme in re.findall(r"/usr/share/grub/themes/[\w.-]+/theme\.txt", text):
            self.assertTrue((ROOT / Path(theme).relative_to("/usr/share")).is_file(), theme)
        self.assertTrue((ROOT / "sddm" / "themes" / "orac" / "metadata.desktop").is_file())
        self.assertTrue((ROOT / "icons" / "Orac" / "index.theme").is_file())


class TestGrubTheme(unittest.TestCase):
    THEME = ROOT / "grub" / "themes" / "orac" / "theme.txt"

    def test_every_image_ships(self):
        for name in re.findall(r'desktop-image:\s*"([^"]+)"', self.THEME.read_text()):
            self.assertTrue((self.THEME.parent / name).is_file(), name)

    def test_every_font_is_built(self):
        # GRUB matches fonts by the name embedded in the .pf2 (grub-mkfont -n).
        embedded = set()
        for pf2 in self.THEME.parent.glob("*.pf2"):
            data = pf2.read_bytes()
            i = data.index(b"NAME") + 8
            embedded.add(data[i:data.index(b"\0", i)].decode())
        for font in re.findall(r'font\s*[=:]\s*"([^"]+)"', self.THEME.read_text()):
            self.assertIn(font, embedded)


class TestSddmTheme(unittest.TestCase):
    DIR = ROOT / "sddm" / "themes" / "orac"

    def test_metadata_and_config_files_ship(self):
        meta = (self.DIR / "metadata.desktop").read_text()
        self.assertIn("QtVersion=6", meta)
        for key in ("MainScript", "ConfigFile", "Screenshot"):
            name = re.search(rf"^{key}=(.+)$", meta, re.M).group(1)
            self.assertTrue((self.DIR / name).is_file(), name)
        for name in re.findall(r"^\w+=(.+)$", (self.DIR / "theme.conf").read_text(), re.M):
            self.assertTrue((self.DIR / name).is_file(), name)


class TestCursors(unittest.TestCase):
    DIR = ROOT / "icons" / "Orac" / "cursors"

    def test_core_cursors_are_valid_xcursor_files(self):
        for name in ("left_ptr", "default", "pointer", "text", "wait", "watch"):
            path = (self.DIR / name).resolve()
            self.assertTrue(path.is_file(), name)
            self.assertEqual(path.read_bytes()[:4], b"Xcur", name)

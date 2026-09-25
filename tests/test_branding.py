"""packaging/orac-branding: pin the two theme defects found when packaging it.

The Plymouth script shipped in the theme zip called Sprite.SetScale, Plymouth.GetTime and
Plymouth.SetMessageFunction -- none exist in Plymouth's script plugin -- so its progress bar
and status line never moved. The KSplash QML assigned a bare `letterSpacing`, which is not a
Text property, so the whole splash failed to load. Neither is visible without booting.
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
    "SetRefreshRate", "GetMode",
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


if __name__ == "__main__":
    unittest.main()

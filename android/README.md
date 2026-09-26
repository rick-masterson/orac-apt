# ORAC theme for Android

Version 1.1.0. Made from the desktop `orac-branding` package, so the phone matches the workstation, with energy
drawn from the aether added: lightning, currents of light and sparks converging on each orb. Nothing here
needs root or an app from an unknown source.

## Wallpapers

1. Open an image from `wallpapers/` (for example in Files or Google Photos) and choose **Set as wallpaper**, for
   the home screen, the lock screen or both. They are 1440×3200; Android scales them to any phone.
2. Android 12 or newer: in **Wallpaper & style**, choose **Wallpaper colors**. The system accents (quick settings,
   buttons, keyboard) then turn ORAC purple. Samsung calls this **Color palette**.
3. Turn on **Dark theme** (Settings > Display). The wallpapers are drawn on black.

## Terminal (optional, for the Termux app)

The same colours, login banner and system banner as the desktop terminal. Install Termux from F-Droid or its
GitHub releases (the Google Play build is out of date). Then, in Termux:

```sh
termux-setup-storage                 # allow access to Downloads
pkg install unzip fastfetch
cd ~ && unzip ~/storage/downloads/orac-android-theme-1.1.0.zip
sh orac-android-theme-1.1.0/termux/install.sh
```

Open a new Termux session to see the ORAC banner, and run `fastfetch` for the system banner.

To undo: your old colours are kept as `~/.termux/colors.properties.bak`, and the old banner as
`$PREFIX/etc/motd.bak`.

## Not included

- **Boot animation:** changing it needs a rooted phone.
- **App icons:** an icon pack is a separate installable app. Ask if you want one.

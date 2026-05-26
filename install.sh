#!/usr/bin/env bash
set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo $0"
    exit 1
fi

# Detect theme dir: /boot/grub on Debian/Ubuntu/Arch, /boot/grub2 on Fedora/RHEL/openSUSE
if [ -d /boot/grub ]; then
    THEME_DIR=/boot/grub/themes
elif [ -d /boot/grub2 ]; then
    THEME_DIR=/boot/grub2/themes
else
    echo "Could not find /boot/grub or /boot/grub2. Is GRUB installed?"
    exit 1
fi
THEME_PATH="$THEME_DIR/Razer/theme.txt"

mkdir -p "$THEME_DIR"
rm -rf "$THEME_DIR/Razer"
cp -r ./Razer "$THEME_DIR/"
echo "Installed theme to: $THEME_DIR/Razer"

GRUB_DEFAULT=/etc/default/grub
# Strip any previous values we manage
for k in GRUB_THEME GRUB_GFXMODE GRUB_GFXPAYLOAD_LINUX GRUB_TIMEOUT GRUB_TIMEOUT_STYLE GRUB_TERMINAL GRUB_TERMINAL_OUTPUT; do
    sed -i "/^${k}=/d; /^#${k}=/d" "$GRUB_DEFAULT"
done

# Append our settings. GRUB_GFXMODE lists multiple resolutions so GRUB picks
# the first one the firmware supports. GRUB_TERMINAL_OUTPUT=gfxterm is the
# critical line - without it GRUB stays in text mode and ignores the theme.
{
    echo "GRUB_THEME=\"$THEME_PATH\""
    echo 'GRUB_GFXMODE="1920x1080,1366x768,1024x768,auto"'
    echo 'GRUB_GFXPAYLOAD_LINUX="keep"'
    echo 'GRUB_TIMEOUT="10"'
    echo 'GRUB_TIMEOUT_STYLE="menu"'
    echo 'GRUB_TERMINAL_OUTPUT="gfxterm"'
} >> "$GRUB_DEFAULT"

# Regenerate grub.cfg. Order matters: update-grub on Debian/Ubuntu;
# grub2-mkconfig on Fedora/RHEL (both BIOS and UEFI paths); grub-mkconfig
# on Arch and other distros that ship the original tool name.
regenerated=0
if command -v update-grub >/dev/null 2>&1; then
    update-grub
    regenerated=1
elif command -v grub2-mkconfig >/dev/null 2>&1; then
    [ -f /boot/grub2/grub.cfg ] && grub2-mkconfig -o /boot/grub2/grub.cfg && regenerated=1
    for cfg in /boot/efi/EFI/*/grub.cfg; do
        [ -f "$cfg" ] && grub2-mkconfig -o "$cfg" && regenerated=1
    done
elif command -v grub-mkconfig >/dev/null 2>&1; then
    grub-mkconfig -o /boot/grub/grub.cfg
    regenerated=1
fi
[ "$regenerated" -eq 0 ] && echo "WARNING: could not find update-grub / grub-mkconfig / grub2-mkconfig"

echo ""
echo "=== /etc/default/grub now contains ==="
grep -E '^GRUB_' "$GRUB_DEFAULT"
echo ""
echo "=== theme path baked into grub.cfg ==="
for cfg in /boot/grub/grub.cfg /boot/grub2/grub.cfg /boot/efi/EFI/*/grub.cfg; do
    [ -f "$cfg" ] && echo "[$cfg]" && grep -iE '(set theme|gfxmode|terminal_output)' "$cfg" | head -5
done
echo ""
echo "Now reboot. If you still see text mode after reboot:"
echo "  1. Edit /etc/default/grub and lower GRUB_GFXMODE to e.g. 1024x768"
echo "  2. Confirm there is NO line forcing GRUB_TERMINAL=console"
echo "  3. Re-run: sudo $0"

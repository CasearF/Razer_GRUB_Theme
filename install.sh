#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RAZER_SRC="$SCRIPT_DIR/Razer"
DEFAULT_FILE=/etc/default/grub

usage() {
    cat <<EOF
Usage: $0 [command]

Commands:
  install            Install the Razer theme bundled with this repo and activate it
  switch | select    Pick from themes already installed under the GRUB themes dir
  remove | disable   Disable the active theme (theme files stay on disk)
  status             Show the current theme + list installed themes
  help | -h          Show this help

With no command, an interactive menu is shown.
EOF
}

require_root() {
    if [ "$EUID" -ne 0 ]; then
        echo "Please run as root: sudo $0 $*" >&2
        exit 1
    fi
}

# Sets THEME_DIR, GRUB_CFG, REGEN_CMD based on the distro layout
detect_paths() {
    if [ -d /boot/grub ]; then
        THEME_DIR=/boot/grub/themes
        GRUB_CFG=/boot/grub/grub.cfg
    elif [ -d /boot/grub2 ]; then
        THEME_DIR=/boot/grub2/themes
        GRUB_CFG=/boot/grub2/grub.cfg
    else
        echo "Neither /boot/grub nor /boot/grub2 found. Is GRUB installed?" >&2
        exit 1
    fi

    if command -v update-grub >/dev/null 2>&1; then
        REGEN_CMD=(update-grub)
    elif command -v grub2-mkconfig >/dev/null 2>&1; then
        REGEN_CMD=(grub2-mkconfig -o "$GRUB_CFG")
    elif command -v grub-mkconfig >/dev/null 2>&1; then
        REGEN_CMD=(grub-mkconfig -o "$GRUB_CFG")
    else
        echo "No update-grub / grub-mkconfig / grub2-mkconfig found." >&2
        exit 1
    fi
}

regenerate_grub() {
    echo "Regenerating $GRUB_CFG..."
    "${REGEN_CMD[@]}"
    # Fedora/RHEL UEFI systems also have a real grub.cfg under /boot/efi
    if command -v grub2-mkconfig >/dev/null 2>&1; then
        for cfg in /boot/efi/EFI/*/grub.cfg; do
            [ -f "$cfg" ] && [ "$cfg" != "$GRUB_CFG" ] && grub2-mkconfig -o "$cfg"
        done
    fi
}

# Replace (or add) KEY="VAL" in /etc/default/grub
set_default_var() {
    local key="$1" val="$2"
    sed -i "/^${key}=/d; /^#${key}=/d" "$DEFAULT_FILE"
    echo "${key}=\"${val}\"" >> "$DEFAULT_FILE"
}

unset_default_var() {
    local key="$1"
    sed -i "/^${key}=/d" "$DEFAULT_FILE"
}

current_theme_path() {
    [ -f "$DEFAULT_FILE" ] || return
    grep -E '^[[:space:]]*GRUB_THEME=' "$DEFAULT_FILE" | head -1 \
        | sed -E 's/^[^=]*=//; s/^"(.*)"$/\1/; s/^'\''(.*)'\''$/\1/'
}

# Populates the THEMES array with absolute paths of every installed theme
# (directories under $THEME_DIR that contain a theme.txt).
collect_themes() {
    THEMES=()
    [ -d "$THEME_DIR" ] || return
    for d in "$THEME_DIR"/*/; do
        [ -f "${d}theme.txt" ] || continue
        THEMES+=("${d%/}")
    done
}

action_install() {
    if [ ! -d "$RAZER_SRC" ]; then
        echo "Cannot find $RAZER_SRC. Run this from the repo root." >&2
        exit 1
    fi

    mkdir -p "$THEME_DIR"
    rm -rf "$THEME_DIR/Razer"
    cp -r "$RAZER_SRC" "$THEME_DIR/"
    echo "Installed theme files to $THEME_DIR/Razer"

    set_default_var GRUB_THEME              "$THEME_DIR/Razer/theme.txt"
    set_default_var GRUB_GFXMODE            "1920x1080,1366x768,1024x768,auto"
    set_default_var GRUB_GFXPAYLOAD_LINUX   "keep"
    set_default_var GRUB_TIMEOUT            "10"
    set_default_var GRUB_TIMEOUT_STYLE      "menu"
    set_default_var GRUB_TERMINAL_OUTPUT    "gfxterm"
    unset_default_var GRUB_TERMINAL

    regenerate_grub
    echo ""
    echo "Done. Reboot to see the Razer theme."
}

action_switch() {
    collect_themes
    if [ ${#THEMES[@]} -eq 0 ]; then
        echo "No themes installed under $THEME_DIR/" >&2
        exit 1
    fi

    local current
    current="$(current_theme_path)"

    echo "Installed themes:"
    local i=0
    for t in "${THEMES[@]}"; do
        i=$((i + 1))
        local marker=""
        [ "${t}/theme.txt" = "$current" ] && marker="  (current)"
        printf "  %d) %s%s\n" "$i" "$(basename "$t")" "$marker"
    done

    read -r -p "Pick a theme [1-${#THEMES[@]}]: " choice
    if [[ ! "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt ${#THEMES[@]} ]; then
        echo "Invalid choice." >&2
        exit 1
    fi

    local selected="${THEMES[$((choice - 1))]}/theme.txt"
    set_default_var GRUB_THEME           "$selected"
    set_default_var GRUB_GFXMODE         "1920x1080,1366x768,1024x768,auto"
    set_default_var GRUB_TERMINAL_OUTPUT "gfxterm"
    unset_default_var GRUB_TERMINAL

    regenerate_grub
    echo "Activated: $selected"
}

action_remove() {
    unset_default_var GRUB_THEME
    regenerate_grub
    echo "Theme disabled. GRUB will boot without a theme on next reboot."
    echo "Theme files under $THEME_DIR/ were left intact."
}

action_status() {
    local current
    current="$(current_theme_path)"
    if [ -n "$current" ]; then
        echo "Active theme: $current"
        [ -f "$current" ] || echo "  WARNING: file does not exist on disk."
    else
        echo "No theme is active."
    fi

    collect_themes
    if [ ${#THEMES[@]} -gt 0 ]; then
        echo "Installed themes:"
        for t in "${THEMES[@]}"; do
            echo "  - $(basename "$t")"
        done
    else
        echo "No themes installed under $THEME_DIR/."
    fi
}

interactive_menu() {
    echo "=== Razer GRUB Theme Installer ==="
    echo "  1) Install Razer theme        (copies & activates ./Razer)"
    echo "  2) Switch theme               (pick from installed themes)"
    echo "  3) Remove current theme       (disable, keep files)"
    echo "  4) Status                     (show active + installed themes)"
    echo "  5) Quit"
    read -r -p "Choice [1-5]: " c
    case "$c" in
        1) action_install ;;
        2) action_switch  ;;
        3) action_remove  ;;
        4) action_status  ;;
        5) exit 0 ;;
        *) echo "Invalid choice." >&2; exit 1 ;;
    esac
}

main() {
    local cmd="${1:-}"

    # status / help don't need root
    case "$cmd" in
        status)
            detect_paths
            action_status
            return
            ;;
        help|-h|--help)
            usage
            return
            ;;
    esac

    require_root "$@"
    detect_paths

    case "$cmd" in
        install)        action_install ;;
        switch|select)  action_switch  ;;
        remove|disable) action_remove  ;;
        "")             interactive_menu ;;
        *)
            echo "Unknown command: $cmd" >&2
            usage
            exit 1
            ;;
    esac
}

main "$@"

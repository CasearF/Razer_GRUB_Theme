#!/usr/bin/env bash
set -e

cp -r ./Razer /boot/grub/themes/

sed -i '/GRUB_THEME=/d' /etc/default/grub
sed -i '/GRUB_GFXMODE=/d' /etc/default/grub
sed -i '/GRUB_TIMEOUT=/d' /etc/default/grub
sed -i '/GRUB_TIMEOUT_STYLE=/d' /etc/default/grub

echo "GRUB_THEME=\"/boot/grub/themes/Razer/theme.txt\"" >> /etc/default/grub
echo 'GRUB_GFXMODE="auto"' >> /etc/default/grub
echo 'GRUB_TIMEOUT="10"' >> /etc/default/grub
echo 'GRUB_TIMEOUT_STYLE="menu"' >> /etc/default/grub

sudo grub-mkconfig -o /boot/grub/grub.cfg

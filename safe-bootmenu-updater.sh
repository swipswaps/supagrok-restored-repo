#!/bin/bash
set -euo pipefail
echo '▶ Backing up grub.cfg...'
cp -av /boot/grub2/grub.cfg "/boot/grub2/grub.cfg.bak.$(date +%s)"
echo '▶ Regenerating GRUB config...'
grub2-mkconfig -o /boot/grub2/grub.cfg
echo '✅ You can now reboot safely.'

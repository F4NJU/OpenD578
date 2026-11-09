#!/usr/bin/env python3
"""Build independent bench alpha. Requires zig executable, not firmware inputs."""
import argparse,subprocess,shutil,hashlib,json
from pathlib import Path
r=Path(__file__).resolve().parents[1];p=r/'firmware/experiments/audio_alpha'
a=argparse.ArgumentParser();a.add_argument('--zig',default=shutil.which('zig'));args=a.parse_args()
if not args.zig:raise SystemExit('Fournir --zig /chemin/zig (build vérifié avec Zig 0.14.1)')
subprocess.run([args.zig,'cc','-target','thumb-freestanding-eabi','-mcpu=cortex_m4','-ffreestanding','-fno-builtin','-nostdlib','-Oz','-Wl,--entry=Reset_Handler','-Wl,-T,'+str(p/'link.ld'),str(p/'main.c'),str(r/'firmware/hal/audio_control.c'),'-o',str(p/'audio_alpha.elf')],check=True)
subprocess.run([args.zig,'objcopy','-O','binary',str(p/'audio_alpha.elf'),str(p/'audio_alpha.bin')],check=True)
for suffix in ['elf','bin']:shutil.copy2(p/('audio_alpha.'+suffix),r/'browser-bench/samples'/('audio_alpha.'+suffix))
(p/'build.json').write_text(json.dumps({'target':'thumb Cortex-M4 soft-float','compiler':subprocess.check_output([args.zig,'version'],text=True).strip(),'loadAddress':'0x08006000','scope':'bench control firmware; RF not initialized; hardware not qualified','binaryBytes':(p/'audio_alpha.bin').stat().st_size,'binarySHA256':hashlib.sha256((p/'audio_alpha.bin').read_bytes()).hexdigest()},indent=2)+'\n')
print(p/'audio_alpha.bin')

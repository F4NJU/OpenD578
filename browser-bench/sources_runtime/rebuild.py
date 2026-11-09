#!/usr/bin/env python3
"""Rebuild the provided source with an activated Emscripten 4.0.15 SDK and CMake."""
import argparse,importlib.util,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);args=p.parse_args()
source=args.source.resolve();os.chdir(source)
spec=importlib.util.spec_from_file_location('upstream_build',source/'build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
b.patchUnicorn();b.generateConstants()
build_dir=source/'unicorn/build'
subprocess.run(['emcmake','cmake','-S',str(source/'unicorn'),'-B',str(build_dir),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_C_FLAGS_RELEASE=-O2 -g','-DBUILD_SHARED_LIBS=OFF','-DUNICORN_ARCH=arm','-DUNICORN_BUILD_TESTS=OFF','-DUNICORN_INSTALL=OFF','-DUNICORN_FUZZ=OFF','-DUNICORN_LEGACY_STATIC_ARCHIVE=ON'],check=True)
subprocess.run(['emmake','cmake','--build',str(build_dir),'--target','unicorn_archive','-j4'],check=True)
(source/'dist').mkdir(exist_ok=True)
methods=['ccall','getValue','setValue','addFunction','removeFunction','writeArrayToMemory']
cmd=['emcc','-Os','-g2',str(build_dir/'libunicorn.a'),'-s',f'EXPORTED_FUNCTIONS={b.EXPORTED_FUNCTIONS}','-s',f'EXPORTED_RUNTIME_METHODS={methods}','-s','ALLOW_TABLE_GROWTH=1','-s','ALLOW_MEMORY_GROWTH=1','-s','MODULARIZE=1','-s','SINGLE_FILE=1','-s','WASM_BIGINT=1','-s',"EXPORT_NAME='MUnicorn'",'--post-js','src/constants_arm.js','--post-js','src/unicorn-wrapper.js','-o','dist/unicorn_arm.js']
subprocess.run(cmd,check=True)
print(source/'dist/unicorn_arm.js')

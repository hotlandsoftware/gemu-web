#!/usr/bin/env python3
"""
gemu web build — compiles GEMU to WebAssembly with Emscripten.

Reuses gemu-src/configure (imported as a module) for the generated .inc
tables, so machine/device/romdb data stays in sync with the native build.
gemu-src is never written to; all output goes to web/build and web/dist.

Usage:
  python build.py [--debug] [--target-list=chip8]
"""

import argparse
import importlib.machinery
import importlib.util
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

WEB_DIR  = os.path.dirname(os.path.abspath(__file__))
GEMU_SRC = os.path.normpath(os.path.join(WEB_DIR, '..', 'gemu-src'))
EMCC     = os.environ.get('EMCC', '/usr/lib/emscripten/emcc')

BUILD_DIR = os.path.join(WEB_DIR, 'build')
OBJ_DIR   = os.path.join(BUILD_DIR, 'obj')
DIST_DIR  = os.path.join(WEB_DIR, 'dist')

# Web replacements for native-only core sources:
#   vnc.c     → vnc_stub.c   (sockets + OpenSSL; no VNC in a browser)
#   monitor.c → monitor_web.c (wraps it; JS command queue instead of stdin)
CORE_EXCLUDE = {'core/src/vnc.c', 'core/src/monitor.c'}

WEB_SRC = ['src/vnc_stub.c', 'src/web_glue.c', 'src/monitor_web.c']

INC_DIRS = ['core/include', 'cpu', 'vga', 'audio',
            'hardware', 'hardware/machine', 'hardware/device', 'src']


def load_configure():
    # configure has no .py extension, so name the loader explicitly
    loader = importlib.machinery.SourceFileLoader(
        'gemu_configure', os.path.join(GEMU_SRC, 'configure'))
    spec = importlib.util.spec_from_loader('gemu_configure', loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--debug', action='store_true')
    p.add_argument('--target-list', default='chip8')
    args = p.parse_args()

    targets = [t.strip() for t in args.target_list.split(',') if t.strip()]

    cfg = load_configure()
    for t in targets:
        if t not in cfg.FAMILY_SRC:
            sys.exit(f'unknown family {t!r}. Valid: {", ".join(cfg.FAMILY_SRC)}')

    os.makedirs(OBJ_DIR, exist_ok=True)
    os.makedirs(DIST_DIR, exist_ok=True)

    # generate_data globs data/machine/*.xml relative to cwd
    os.chdir(GEMU_SRC)
    cfg.generate_data(BUILD_DIR, targets, False)

    srcs = [s for s in cfg.CORE_SRC if s not in CORE_EXCLUDE]
    for t in targets:
        for s in cfg.FAMILY_SRC[t]:
            if s not in srcs:
                srcs.append(s)
    srcs.append('src/main.c')

    inc = [f'-I{os.path.join(GEMU_SRC, d)}' for d in INC_DIRS]
    inc += [f'-I{BUILD_DIR}',                      # generated/*.inc
            f'-I{os.path.join(GEMU_SRC, "core/src")}']  # monitor_web.c includes monitor.c

    defs = [f'-DHAVE_{t.upper()}' for t in targets]
    defs += ['-Dnanosleep=gemu_web_nanosleep']     # see web_glue.c
    defs += ['-D_GNU_SOURCE']  # musl: strcasecmp & friends via string.h

    opt = '-O0 -g' if args.debug else '-O2'
    cflags = (f'{opt} -std=gnu11 -Wall -Wextra -Wno-unused-parameter '
              '-sUSE_SDL=2').split() + inc + defs

    ldflags = [
        '-sUSE_SDL=2',
        '-sASYNCIFY',
        '-sASYNCIFY_STACK_SIZE=131072',
        '-sALLOW_MEMORY_GROWTH',
        '-sFORCE_FILESYSTEM',
        '-sMODULARIZE',
        '-sEXPORT_NAME=createGemu',
        '-sINVOKE_RUN=0',
        '-sENVIRONMENT=web',
        '-sEXPORTED_FUNCTIONS=_main,_gemu_web_monitor_input,_malloc,_free',
        '-sEXPORTED_RUNTIME_METHODS=callMain,FS,ccall,cwrap',
    ]
    if args.debug:
        ldflags += ['-sASSERTIONS=2', '-g']

    # web shims live under web/src/, gemu sources under gemu-src/
    all_srcs = [('gemu', s) for s in srcs] + [('web', s) for s in WEB_SRC]

    def compile_entry(entry):
        origin, src = entry
        base = WEB_DIR if origin == 'web' else GEMU_SRC
        path = os.path.join(base, src)
        obj = os.path.join(OBJ_DIR, f'{origin}_' + src.replace('/', '_') + '.o')
        cmd = [EMCC] + cflags + ['-c', '-o', obj, path]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f'FAIL {src}\n{r.stderr}', file=sys.stderr)
            return None
        if r.stderr.strip():
            print(f'-- {src}\n{r.stderr.strip()}', file=sys.stderr)
        print(f'CC {src}')
        return obj

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as ex:
        objs = list(ex.map(compile_entry, all_srcs))
    if None in objs:
        sys.exit('compilation failed')

    out = os.path.join(DIST_DIR, 'gemu-chip8.js')
    print(f'LINK {out}')
    r = subprocess.run([EMCC] + ldflags + ['-o', out] + objs,
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f'link failed:\n{r.stderr}')
    if r.stderr.strip():
        print(r.stderr.strip(), file=sys.stderr)

    wasm = out.replace('.js', '.wasm')
    print(f'\nOK: {out} ({os.path.getsize(out)//1024} KB) + '
          f'{wasm} ({os.path.getsize(wasm)//1024} KB)')


if __name__ == '__main__':
    main()

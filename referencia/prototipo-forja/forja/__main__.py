"""python -m forja spec.py [mais.py ...] [--out pasta] [--sem-gif]

Runs each spec file. A spec builds Model objects; every Model found at module level is
built (a list named `serie` is built as an evolution series)."""
import argparse
import os
import runpy
import sys
import time

from .build import build, build_series
from .core import Model, ForjaError


def main(argv=None):
    ap = argparse.ArgumentParser(prog="forja")
    ap.add_argument("specs", nargs="+")
    ap.add_argument("--out", default="out")
    ap.add_argument("--sem-gif", action="store_true")
    ap.add_argument("--raios", type=int, default=40)
    a = ap.parse_args(argv)
    code = 0
    for spec in a.specs:
        t0 = time.time()
        try:
            ns = runpy.run_path(spec, run_name="__forja__")
        except ForjaError as e:
            print(f"ERRO  {os.path.basename(spec)}: {e}")
            code = 1
            continue
        serie = ns.get("serie")
        done = set()
        if isinstance(serie, (list, tuple)) and serie:
            build_series(list(serie), a.out, gifs=not a.sem_gif, rays=a.raios)
            done = {id(m) for m in serie}
        for v in ns.values():
            if isinstance(v, Model) and id(v) not in done:
                build(v, a.out, gifs=not a.sem_gif, rays=a.raios)
                done.add(id(v))
        print(f"      ({time.time() - t0:.1f}s)")
    return code


if __name__ == "__main__":
    sys.exit(main())

"""spec 与 impl 各带不带默认值时的八种读数。

跑法：PYTHONPATH=src .venv/bin/python repro/spec-default-args.py
"""

import warnings

from pluggy import HookimplMarker
from pluggy import HookspecMarker
from pluggy import PluginManager

hookspec = HookspecMarker("proj")
hookimpl = HookimplMarker("proj")

seen: list = []


def spec_class(spec_src):
    ns = {"hookspec": hookspec}
    exec(f"class Spec:\n    @hookspec\n    def hi{spec_src}:\n        pass", ns, ns)
    return ns["Spec"]


def impl_class(impl_src):
    ns = {"hookimpl": hookimpl, "seen": seen}
    exec(
        f"class P:\n    @hookimpl\n    def hi{impl_src}:\n"
        "        seen.append({k: v for k, v in locals().items() if k != 'self'})"
        "\n        return 'ran'",
        ns,
        ns,
    )
    return ns["P"]


CASES = [
    ("(self, a, b)", "(self, a, b)"),
    ("(self, a, b=1)", "(self, a, b)"),
    ("(self, a, b)", "(self, a, b=9)"),
    ("(self, a, b=1)", "(self, a, b=9)"),
]

for spec_src, impl_src in CASES:
    for call_kwargs in ({"a": 1, "b": 2}, {"a": 1}):
        pm = PluginManager("proj")
        pm.add_hookspecs(spec_class(spec_src))
        del seen[:]
        try:
            pm.register(impl_class(impl_src)())
            verdict = "register OK"
        except Exception as e:
            print(
                f"spec hi{spec_src:16} impl hi{impl_src:16} "
                f"call hi({', '.join(f'{k}={v}' for k, v in call_kwargs.items())}) "
                f"-> {type(e).__name__}: {str(e).splitlines()[-1].strip()}"
            )
            continue
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                r = pm.hook.hi(**call_kwargs)
            got = seen[0] if seen else None
            warn = [str(x.message).split("\n")[0] for x in w]
            print(
                f"spec hi{spec_src:16} impl hi{impl_src:16} "
                f"call hi({', '.join(f'{k}={v}' for k, v in call_kwargs.items())}) "
                f"-> {verdict}, ret={r!r}, impl-bound-locals={got}, warnings={warn}"
            )
        except Exception as e:
            print(
                f"spec hi{spec_src:16} impl hi{impl_src:16} "
                f"call hi({', '.join(f'{k}={v}' for k, v in call_kwargs.items())}) "
                f"-> {verdict}, then {type(e).__name__}: {e}"
            )

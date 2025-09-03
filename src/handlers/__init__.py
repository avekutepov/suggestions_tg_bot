import importlib
import pkgutil

def register_all(bot):
    print("[handlers] scanning...")
    for m in pkgutil.iter_modules(__path__):
        name = m.name
        if name.startswith("_"):
            continue
        print(f"[handlers] import {name}")
        module = importlib.import_module(f"{__name__}.{name}")
        fn = getattr(module, "register_handlers", None)
        if callable(fn):
            print(f"[handlers] register {name}.register_handlers")
            fn(bot)
        else:
            print(f"[handlers] skip {name} (no register_handlers)")
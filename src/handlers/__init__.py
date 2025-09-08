import importlib
import logging

ORDER = ["start", "criteria", "intake", "new_user", "moderation", "misc", "reports"]

def register_all(bot):
    for name in ORDER:
        mod = importlib.import_module(f"{__name__}.{name}")
        fn = getattr(mod, "register_handlers", None)
        if callable(fn):
            logging.info("[handlers] register %s.register_handlers", name)
            fn(bot)

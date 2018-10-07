import importlib
from enso import config


def installed():
    retereat_spec = importlib.util.find_spec('enso.contrib._retreat')
    if retereat_spec is not None:
        return True
    return False


def start():
    if not config.RETREAT_DISABLE and installed():
        import enso.contrib._retreat
        return enso.contrib._retreat.start()


def stop():
    if not config.RETREAT_DISABLE and installed():
        import enso.contrib._retreat
        return enso.contrib._retreat.stop()


def is_locked():
    if not config.RETREAT_DISABLE and installed():
        import enso.contrib._retreat
        return enso.contrib._retreat.is_locked()


def take_break():
    if not config.RETREAT_DISABLE and installed():
        import enso.contrib._retreat
        return enso.contrib._retreat.take_break()


def delay():
    if not config.RETREAT_DISABLE and installed():
        import enso.contrib._retreat
        return enso.contrib._retreat.delay()


def skip():
    if not config.RETREAT_DISABLE and installed():
        import enso.contrib._retreat
        return enso.contrib._retreat.skip()


def options():
    if not config.RETREAT_DISABLE and installed():
        import enso.contrib._retreat
        return enso.contrib._retreat.options()


def about():
    if not config.RETREAT_DISABLE and installed():
        import enso.contrib._retreat
        return enso.contrib._retreat.about()
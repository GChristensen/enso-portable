from win32event import OpenEvent
from win32event import SetEvent
from win32api import CloseHandle

def cmd_delay_break(ensoapi):
    """Delay Angelic Retreat Break"""
    try:
        evt = OpenEvent(2, 0, "@@__ANGELIC_RETREAT_DELAY_EVENT__@@")
        SetEvent(evt)
        CloseHandle(evt)
    except:
        pass

def cmd_skip_break(ensoapi):
    """Skip Angelic Retreat Break"""
    try:
        evt = OpenEvent(2, 0, "@@__ANGELIC_RETREAT_SKIP_EVENT__@@")
        SetEvent(evt)
        CloseHandle(evt)
    except:
        pass

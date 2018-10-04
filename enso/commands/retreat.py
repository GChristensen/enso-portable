from enso import retreat


def cmd_delay_break(ensoapi):
    """Delay Enso Retreat break"""
    retreat.delay()


def cmd_skip_break(ensoapi):
    """Skip Enso Retreat break"""
    retreat.skip()


def cmd_take_break(ensoapi):
    """Take break (Enso Retreat)"""
    retreat.take_break()


def cmd_retreat(ensoapi, action):
    """Take Enso Retreat action"""
    vars(retreat)[action]()

cmd_retreat.valid_args = ["start", "stop", "options", "about"]
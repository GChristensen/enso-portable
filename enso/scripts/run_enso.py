#!/usr/bin/env python3

# Enso launcher. Works unmodified on Windows (invoked by run-enso.exe,
# which hardcodes this path) and on Linux (X11 only; run directly with
# `python3 enso/scripts/run_enso.py`, see README.linux.md at the
# repository root for prerequisites). All OS-specific behavior lives
# in launcher_utils.py.

import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                os.path.pardir)))

import launcher_utils as lu

lu.preflight()

import enso
from enso import config
from enso.user import import_package_by_path

lu.platform_bootstrap()
lu.bootstrap_sys_path()


def process_options(argv):
    parser = lu.create_option_parser()
    lu.add_platform_options(parser)
    opts, args = parser.parse_args(argv)
    return opts, args


def main(argv = None):
    opts, args = process_options(argv)
    config.ENSO_IS_QUIET = opts.quiet
    config.DEBUG = opts.debug

    lu.configure_logging(opts)

    lu.configure_init_files()

    lu.start_platform_extras(opts)

    user_lib_index = os.path.join(config.ENSO_USER_DIR, "lib")
    import_package_by_path(user_lib_index)

    # Retreat is an enso.config.PLUGINS entry now; it starts on the init event
    # and stops via its own atexit handler.
    enso.run()

    lu.stop_platform_extras()

    logging.shutdown()

    lu.platform_shutdown_delay()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
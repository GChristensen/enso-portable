from enso.providers import ProviderUnavailableError

class PlatformUnsupportedError(ProviderUnavailableError):
    """
    Exception that should be raised by a submodule of this package if
    it can't be used because the host is running an unsupported
    platform.
    """

    pass

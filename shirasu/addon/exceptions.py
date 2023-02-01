class AddonError(Exception):
    """
    Errors when loading addons.
    """


class DuplicateAddonError(AddonError):
    """
    Raises when addon name is duplicate.
    """


class LoadAddonError(AddonError):
    """
    Raises when failing to load addon.
    """

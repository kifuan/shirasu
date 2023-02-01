from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .addon import Addon


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


class NoSuchAddonError(AddonError):
    """
    Raises when attempting to get an addon which is not existed.
    """

# -*- coding: utf-8 -*-
"""Contribute the PartDesignUpgrade commands to the Part Design workbench.

The addon defines no workbench of its own: this manipulator adds its buttons to
Part Design's own "Part Design Helper Features" toolbar and to the Part Design
menu, so they sit next to the stock PartDesign tools and the user never has to
switch workbench.

A manipulator runs every time a workbench is activated. The targets used here
only exist in Part Design, and an operation whose target cannot be found is
skipped silently, so the same list is harmless in every other workbench.
"""

_COMMANDS = [
    "PartDesignUpgrade_Pipe",
    "PartDesignUpgrade_SubtractPipe",
    "PartDesignUpgrade_FaceRib",
    "PartDesignUpgrade_Cut",
    "PartDesignUpgrade_AutoMirror",
    "PartDesignUpgrade_Weight",
]

# Stock Part Design toolbar the buttons are appended to (FreeCAD >= 1.0).
_TOOLBAR = "Part Design Helper Features"

# Stock Part Design command: it identifies the menu the buttons are appended to.
_MENU_ANCHOR = "PartDesign_Body"


class PartDesignUpgradeManipulator:
    """Add the PartDesignUpgrade buttons to the Part Design workbench."""

    def modifyToolBars(self):
        return [{"append": name, "toolBar": _TOOLBAR} for name in _COMMANDS]

    def modifyMenuBar(self):
        return [{"append": name, "menuItem": _MENU_ANCHOR} for name in _COMMANDS]

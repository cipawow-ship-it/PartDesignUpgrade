# -*- coding: utf-8 -*-
"""PartDesignUpgrade GUI init.

The addon is not a workbench: there is no Gui.addWorkbench call here and no
<workbench> item in package.xml. The commands are contributed to the Part Design
workbench by a workbench manipulator, so they appear in Part Design's own tools
without forcing the user to switch workbench.
"""

import FreeCADGui as Gui

from . import commands  # noqa: F401  (registers the PartDesignUpgrade_* commands)
from . import collision_core
from . import collision_dock
from .Manipulator import PartDesignUpgradeManipulator

Gui.addWorkbenchManipulator(PartDesignUpgradeManipulator())

# Report dock of the collision detector: it shows "no collision" or the
# colliding pairs with their overlap volumes. It is created hidden and only
# while the detector is on, so it never shows up on a plain restart.
collision_dock.set_report_callback(collision_core)

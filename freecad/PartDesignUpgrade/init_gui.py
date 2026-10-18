# -*- coding: utf-8 -*-
"""PartDesignUpgrade GUI init.

The addon is not a workbench: there is no Gui.addWorkbench call here and no
<workbench> item in package.xml. The commands are contributed to the Part Design
workbench by a workbench manipulator, so they appear in Part Design's own tools
without forcing the user to switch workbench.
"""

import FreeCADGui as Gui

from . import commands  # noqa: F401  (registers the PartDesignUpgrade_* commands)
from .Manipulator import PartDesignUpgradeManipulator

Gui.addWorkbenchManipulator(PartDesignUpgradeManipulator())

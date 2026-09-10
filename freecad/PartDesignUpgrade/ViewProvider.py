# -*- coding: utf-8 -*-
"""ViewProvider for pipe features."""

import os

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class FormsViewProvider:
    """Minimal view provider that makes the feature selectable and editable."""

    def __init__(self, vobj):
        vobj.Proxy = self
        self.Object = vobj.Object

    def getIcon(self):
        t = getattr(getattr(self, "Object", None), "Proxy", None)
        if getattr(t, "Type", "") in ("AdditivePipeFeature", "PipeFeature"):
            return "PartDesign_AdditivePipe"
        if getattr(t, "Type", "") == "SubtractivePipeFeature":
            return "PartDesign_SubtractivePipe"
        if getattr(t, "Type", "") in ("AdditiveRibFeature", "RibFeature"):
            return os.path.join(_ROOT, "Resources", "Icons", "Rib_icon.svg")
        if getattr(t, "Type", "") == "SubtractiveRibFeature":
            return os.path.join(_ROOT, "Resources", "Icons", "RibCut_icon.svg")
        if getattr(t, "Type", "") in ("FaceRibFeature", "AdditiveFaceRibFeature"):
            return os.path.join(_ROOT, "Resources", "Icons", "FaceRib_icon.png")
        return os.path.join(_ROOT, "Resources", "Icons", "PartDesignUpgrade.svg")

    def attach(self, vobj):
        self.Object = vobj.Object
        self.claimChildren = []

    def updateData(self, obj, prop):
        pass

    def onChanged(self, vobj, prop):
        pass

    def doubleClicked(self, vobj):
        self.edit()
        return True

    def edit(self, vobj=None, mode=0):
        self.setEdit(mode)
        return True

    def setEdit(self, mode=0):
        import FreeCADGui as Gui
        sel = Gui.Selection.getSelection()
        if not sel:
            return
        obj = sel[0]
        if not hasattr(obj, "Proxy") or not hasattr(obj.Proxy, "Type"):
            return
        Gui.Selection.clearSelection()

    def unsetEdit(self, vobj, mode=0):
        import FreeCADGui as Gui
        Gui.Control.closeDialog()

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
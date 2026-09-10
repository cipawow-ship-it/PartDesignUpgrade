# -*- coding: utf-8 -*-
import os

import FreeCAD
import FreeCADGui as Gui

from .translations import tr as _tr

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _icon(name):
    return os.path.join(_ROOT, "Resources", "Icons", name)


class _BaseCommand:
    def __init__(self, resources):
        self._resources = resources

    def GetResources(self):
        return self._resources

    def IsActive(self):
        return FreeCAD.ActiveDocument is not None


class _PipeCommand(_BaseCommand):
    def __init__(self):
        super().__init__({
            "MenuText": _tr("Create Pipe"),
            "ToolTip": _tr("Create a parametric pipe sweeping a profile along a sketch or edge path"),
            "Pixmap": _icon("Pipe_icon.png"),
            "StatusTip": _tr("Create a pipe along a selected sketch or edges"),
        })

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        for se in Gui.Selection.getSelectionEx():
            obj = se.Object
            if obj is None:
                continue
            if obj.TypeId == "PartDesign::Body":
                return True
            if "Sketch" in obj.TypeId:
                return True
            if any(n.startswith("Edge") for n in se.SubElementNames):
                return True
        return False

    def Activated(self):
        from .pipe_core import create_pipe
        create_pipe()


class _SubtractPipeCommand(_BaseCommand):
    def __init__(self):
        super().__init__({
            "MenuText": _tr("Subtractive Pipe"),
            "ToolTip": _tr("Remove a pipe from the body: sweep a profile along a path and subtract it"),
            "Pixmap": _icon("PipeCut_icon.png"),
            "StatusTip": _tr("Subtract a pipe-shaped volume from the selected body"),
        })

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        for se in Gui.Selection.getSelectionEx():
            obj = se.Object
            if obj is None:
                continue
            if obj.TypeId == "PartDesign::Body":
                return True
            if "Sketch" in obj.TypeId:
                return True
            if any(n.startswith("Edge") for n in se.SubElementNames):
                return True
        return False

    def Activated(self):
        from .pipe_core import create_pipe
        create_pipe(subtractive=True)


class _FaceRibCommand(_BaseCommand):
    def __init__(self):
        super().__init__({
            "MenuText": _tr("Create Rib Between Faces"),
            "ToolTip": _tr(
                "Create a stiffening rib between two selected faces: an angled corner, "
                "or a flat face and a cylinder"),
            "Pixmap": _icon("FaceRib_icon.png"),
            "StatusTip": _tr("Create a rib between two selected faces"),
        })

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        for se in Gui.Selection.getSelectionEx():
            if se.Object is None:
                continue
            if any(n.startswith("Face") for n in (se.SubElementNames or [])):
                return True
        return False

    def Activated(self):
        from .face_rib_core import create_face_rib
        create_face_rib()


class _CutCommand(_BaseCommand):
    def __init__(self):
        super().__init__({
            "MenuText": _tr("Assembly Cut"),
            "ToolTip": _tr("Cut several PartDesign bodies at once using one sketch"),
            "Pixmap": _icon("AssemblyCut.svg"),
            "StatusTip": _tr("Cut multiple bodies with a single sketch"),
        })

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        return any("Sketch" in se.Object.TypeId for se in Gui.Selection.getSelectionEx() if se.Object)

    def Activated(self):
        from .assemblycut import assembly_cut
        assembly_cut()


class _WeightCommand(_BaseCommand):
    def __init__(self):
        super().__init__({
            "MenuText": _tr("Weight / Volume"),
            "ToolTip": _tr("Compute the volume and the weight of a body with a material density selector"),
            "Pixmap": _icon("WeightVolume.png"),
            "StatusTip": _tr("Show volume and mass of the selected body"),
        })

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        if Gui.Selection.getSelection():
            return True
        try:
            if Gui.activeBody() is not None:
                return True
        except Exception:
            pass
        return True

    def Activated(self):
        from .weight_volume import weight_volume
        weight_volume()


def _get_commands():
    return [
        ("PartDesignUpgrade_Pipe", _PipeCommand()),
        ("PartDesignUpgrade_SubtractPipe", _SubtractPipeCommand()),
        ("PartDesignUpgrade_FaceRib", _FaceRibCommand()),
        ("PartDesignUpgrade_Cut", _CutCommand()),
        ("PartDesignUpgrade_Weight", _WeightCommand()),
    ]


def register_commands():
    for name, cmd in _get_commands():
        Gui.addCommand(name, cmd)


register_commands()
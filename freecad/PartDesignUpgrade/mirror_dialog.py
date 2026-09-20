# -*- coding: utf-8 -*-
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Task panel for the "Mirror (Symmetry)" command.

The reference (plane / axis / point) starts at the centre of the body. Three
buttons snap it to the fundamental planes (or axes) and an offset spin box
moves it away from the centre. A live datum shows the reference in the 3D
view. The panel appears in the FreeCAD task view (side bar), not in a modal
dialog.
"""

from PySide6.QtWidgets import (QDoubleSpinBox, QGroupBox, QHBoxLayout,
                               QLabel, QPushButton, QRadioButton,
                               QVBoxLayout, QWidget)

from . import symmetry
from .translations import tr as _tr

_PLANES = ("XY", "XZ", "YZ")
_AXES = ("X", "Y", "Z")
_PLANE_LABELS = ("Plane XY", "Plane XZ", "Plane YZ")
_AXIS_LABELS = ("Axis X", "Axis Y", "Axis Z")
_DEFAULT_TARGET = {"plane": "XY", "axis": "X", "point": ""}
# axis movements: the two directions perpendicular to the axis
_AXIS_MOVES = {
    "X": ("Y", "Z"),
    "Y": ("X", "Z"),
    "Z": ("X", "Y"),
}
_POINT_MOVES = ("X", "Y", "Z")


class _MirrorPanel(QWidget):
    """Widget embedded in the FreeCAD task view."""

    def __init__(self, doc, body, center, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.body = body
        self.center = center
        self._kind = "plane"
        self._target = "XY"
        self._ref = None
        self._spins = []

        root = QVBoxLayout(self)

        type_box = QGroupBox(_tr("Symmetry reference"))
        tl = QHBoxLayout(type_box)
        self.rb_plane = QRadioButton(_tr("Plane"))
        self.rb_axis = QRadioButton(_tr("Axis"))
        self.rb_point = QRadioButton(_tr("Point"))
        self.rb_plane.setChecked(True)
        tl.addWidget(self.rb_plane)
        tl.addWidget(self.rb_axis)
        tl.addWidget(self.rb_point)
        root.addWidget(type_box)

        snap_box = QGroupBox(_tr("Snap to a fundamental direction"))
        sl = QHBoxLayout(snap_box)
        self.btn1 = QPushButton(_tr("Plane XY"))
        self.btn2 = QPushButton(_tr("Plane XZ"))
        self.btn3 = QPushButton(_tr("Plane YZ"))
        self._snap_buttons = (self.btn1, self.btn2, self.btn3)
        for i, b in enumerate(self._snap_buttons):
            b.setCheckable(True)
            b.clicked.connect(lambda _, i=i: self._snap(i))
            sl.addWidget(b)
        root.addWidget(snap_box)

        self.off_box = QGroupBox(_tr("Position"))
        self.off_lay = QVBoxLayout(self.off_box)
        root.addWidget(self.off_box)

        self.info = QLabel("")
        self.info.setWordWrap(True)
        root.addWidget(self.info)

        self.rb_plane.toggled.connect(lambda _v: self._sync())
        self.rb_axis.toggled.connect(lambda _v: self._sync())
        self.rb_point.toggled.connect(lambda _v: self._sync())

        self._sync()

    def _make_spin(self):
        s = QDoubleSpinBox()
        s.setRange(-1000000.0, 1000000.0)
        s.setDecimals(3)
        s.setSingleStep(1.0)
        s.setValue(0.0)
        s.valueChanged.connect(lambda _v: self._refresh())
        return s

    def _rebuild_offset(self):
        for i in reversed(range(self.off_lay.count())):
            item = self.off_lay.takeAt(i)
            lay = item.layout()
            if lay is not None:
                for j in reversed(range(lay.count())):
                    li = lay.takeAt(j)
                    w = li.widget()
                    if w is not None:
                        w.setParent(None)
                        w.deleteLater()
                self.off_lay.removeItem(item)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._spins = []
        kind = self._kind
        self.off_lay.addWidget(QLabel(_tr(
            "Distance from the body centre (mm):")))
        if kind == "plane":
            s = self._make_spin()
            self._spins = [s]
            self.off_lay.addWidget(s)
        elif kind == "axis":
            labels = _AXIS_MOVES[self._target]
            for lab in labels:
                row = QHBoxLayout()
                row.addWidget(QLabel(lab))
                s = self._make_spin()
                self._spins.append(s)
                row.addWidget(s, 1)
                self.off_lay.addLayout(row)
        else:  # point
            for lab in _POINT_MOVES:
                row = QHBoxLayout()
                row.addWidget(QLabel(lab))
                s = self._make_spin()
                self._spins.append(s)
                row.addWidget(s, 1)
                self.off_lay.addLayout(row)

    def _kind_now(self):
        if self.rb_axis.isChecked():
            return "axis"
        if self.rb_point.isChecked():
            return "point"
        return "plane"

    def _sync(self):
        kind = self._kind_now()
        if kind != self._kind or not self._spins:
            self._kind = kind
            self._target = _DEFAULT_TARGET[kind]
            self._rebuild_offset()
        seq = _PLANES if kind == "plane" else (_AXES if kind == "axis" else ())
        labels = (_PLANE_LABELS if kind == "plane"
                  else _AXIS_LABELS if kind == "axis" else ("-", "-", "-"))
        for i, b in enumerate(self._snap_buttons):
            b.setEnabled(bool(seq))
            b.setText(_tr(labels[i]) if seq else "-")
            b.setChecked(bool(seq) and seq[i] == self._target)
        self.info.setText(_tr(
            "The mirrored features are parametric: edit the body and the "
            "mirror updates."))
        self._refresh()

    def _snap(self, i):
        if self._kind == "plane":
            self._target = _PLANES[i]
        elif self._kind == "axis":
            self._target = _AXES[i]
            self._rebuild_offset()
        for j, b in enumerate(self._snap_buttons):
            b.setChecked(j == i)
        self._refresh()

    def _offset_value(self):
        kind = self._kind
        if kind == "plane":
            return self._spins[0].value()
        if kind == "axis":
            return tuple(s.value() for s in self._spins)
        return tuple(s.value() for s in self._spins)

    def _refresh(self):
        from . import auto_symmetry
        auto_symmetry.set_choice(self._kind, self._target,
                                 self._offset_value())
        self.cleanup()
        self._ref = symmetry.create_reference(
            self.body, self._kind, self._target, self.center,
            self._offset_value())
        if self._ref is not None:
            try:
                self.doc.recompute()
            except Exception:
                pass

    def cleanup(self):
        if self._ref is not None:
            name = self._ref.Name
            self._ref = None
            try:
                self.doc.removeObject(name)
                self.doc.recompute()
            except Exception:
                pass

    def apply(self):
        """Mirror the last operation of the body around the chosen reference.
        Returns True when the mirror succeeded."""
        from . import symmetry as _sym
        self.cleanup()
        self._ref = _sym.create_reference(
            self.body, self._kind, self._target, self.center,
            self._offset_value())
        if self._ref is None:
            return False
        _sym._last_choice = {
            "kind": self._kind, "target": self._target,
            "offset": self._offset_value()}
        ok = _sym.mirror_solid(self.body, self.doc, self._ref)
        return ok

    def prepare(self):
        """Create the reference datum without mirroring the body.

        The symmetry operation itself is postponed: it only happens when the
        user clicks "Mirror last operation" in the panel or enables the auto
        mirror. Returns True when the reference was created."""
        from . import symmetry as _sym
        self.cleanup()
        self._ref = _sym.create_reference(
            self.body, self._kind, self._target, self.center,
            self._offset_value())
        if self._ref is None:
            return False
        _sym._last_choice = {
            "kind": self._kind, "target": self._target,
            "offset": self._offset_value()}
        try:
            self.doc.recompute()
        except Exception:
            pass
        return True


class SymmetryTaskPanel:
    """FreeCAD task dialog shown in the side task view.

    It hosts the reference-selection panel. When the user accepts, the mirror
    is applied, the dialog closes and the non-modal symmetry panel dock is
    opened in the ComboView tab."""

    def __init__(self, doc, body, center):
        self.doc = doc
        self.body = body
        self.center = center
        self._accepted = False
        self.mirror_panel = _MirrorPanel(doc, body, center)
        self.mirror_panel.setWindowTitle(_tr("Symmetry"))
        self.form = self.mirror_panel

    def getStandardButtons(self):
        from PySide6.QtWidgets import QDialogButtonBox
        return (QDialogButtonBox.StandardButton.Ok.value
                | QDialogButtonBox.StandardButton.Cancel.value)

    def _open_dock(self, enabled=False):
        import FreeCAD
        try:
            from .symmetry_panel import show_symmetry_dock
            show_symmetry_dock(self.doc, self.body, bool(enabled))
            FreeCAD.Console.PrintMessage(
                "Symmetry panel opened.\n")
        except Exception as exc:
            import traceback
            FreeCAD.Console.PrintError(
                "Symmetry panel could not be shown: {}\n{}\n".format(
                    exc, traceback.format_exc()))

    def accept(self):
        import FreeCAD
        try:
            ok = self.mirror_panel.prepare()
        except Exception as exc:
            import traceback
            FreeCAD.Console.PrintError(
                "Symmetry apply raised: {}\n{}\n".format(
                    exc, traceback.format_exc()))
            ok = False
        FreeCAD.Console.PrintMessage(
            "Symmetry reference result: {}\n".format(ok))
        if ok:
            self._accepted = True
            # Keep the panel inert: the datum plane is live in the tree, the
            # symmetry is applied only via the panel buttons / auto mirror.
            self._open_dock(False)
            FreeCAD.Console.PrintMessage(
                "Symmetry panel requested.\n")
        else:
            self.mirror_panel.cleanup()
        import FreeCADGui
        FreeCADGui.Control.closeDialog()
        return True

    def reject(self):
        # A cancelled dialog must not silently reuse an old reference on the
        # next run: ask for a brand new symmetry plane again. The transient
        # datum created for the live preview is removed.
        symmetry._force_new_reference = True
        self.mirror_panel.cleanup()
        import FreeCADGui
        FreeCADGui.Control.closeDialog()
        return True

    def closing(self):
        if not self._accepted:
            symmetry._force_new_reference = True
        return True


def run_mirror_dialog(doc, body):
    shape = body.Shape
    if shape and not shape.isNull():
        center = shape.BoundBox.Center
    else:
        import FreeCAD
        center = FreeCAD.Vector(0, 0, 0)
    import FreeCADGui
    # Keep any mirror already executed on this body: only loose datums are
    # cleaned up, so opening the dialog again does not delete the old one.
    symmetry.reset(body, doc, remove_mirror=False)
    panel = SymmetryTaskPanel(doc, body, center)
    FreeCADGui.Control.showDialog(panel)
    doc.recompute()
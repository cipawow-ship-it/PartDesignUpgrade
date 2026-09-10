# -*- coding: utf-8 -*-
"""Task panel for the rib-between-faces feature with live preview.

Shown non-modally in FreeCAD's side Task dock, like the other panels.
"""

try:
    from PySide2 import QtWidgets
except ImportError:
    from PySide6 import QtWidgets

try:
    from .translations import tr as _tr
except ImportError:
    from translations import tr as _tr


class FaceRibPanel(object):
    """FreeCAD task panel for the rib-between-faces feature.

    Parameters
    ----------
    kind : str
        ``'corner'`` or ``'cylinder'`` (drives which fields
        are shown).
    default_l1, default_l2 : float
        Initial contact lengths.
    full_l1, full_l2 : float
        Lengths that make the rib cover the whole of each face (for the
        "full face" checkbox).
    on_change : callable(l1, l2, thickness, offset, copies, rev1, rev2, mode)
    on_finish : callable(l1, l2, thickness, offset, copies, rev1, rev2, mode)
    on_cancel : callable()
    """

    def __init__(self, kind, default_l1, default_l2, full_l1, full_l2,
                 on_change, on_finish, on_cancel):
        self._kind = kind
        self._full_l1 = float(full_l1)
        self._full_l2 = float(full_l2)
        self._on_change = on_change
        self._on_finish = on_finish
        self._on_cancel = on_cancel

        self.form = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.form)
        form = QtWidgets.QFormLayout()

        self.thick_spin = QtWidgets.QDoubleSpinBox()
        self.thick_spin.setRange(0.01, 100000.0)
        self.thick_spin.setValue(5.0)
        self.thick_spin.setDecimals(2)
        self.thick_spin.setSuffix(" mm")
        self.thick_spin.valueChanged.connect(self._changed)
        form.addRow(_tr("Thickness:"), self.thick_spin)

        self.l1_spin = QtWidgets.QDoubleSpinBox()
        self.l1_spin.setRange(0.01, 100000.0)
        self.l1_spin.setValue(float(default_l1))
        self.l1_spin.setDecimals(2)
        self.l1_spin.setSuffix(" mm")
        self.l1_spin.valueChanged.connect(self._changed)
        form.addRow(_tr("Length on face 1:"), self.l1_spin)

        self.l2_spin = QtWidgets.QDoubleSpinBox()
        self.l2_spin.setRange(0.01, 100000.0)
        self.l2_spin.setValue(float(default_l2))
        self.l2_spin.setDecimals(2)
        self.l2_spin.setSuffix(" mm")
        self.l2_spin.valueChanged.connect(self._changed)
        form.addRow(_tr("Length on face 2:"), self.l2_spin)

        self._manual = None
        self.full_cb = QtWidgets.QCheckBox(_tr("Full face length"))
        self.full_cb.toggled.connect(self._toggle_full)
        form.addRow("", self.full_cb)

        self.offset_spin = QtWidgets.QDoubleSpinBox()
        self.offset_spin.setRange(-100000.0, 100000.0)
        self.offset_spin.setValue(0.0)
        self.offset_spin.setDecimals(2)
        self.offset_spin.setSuffix(" mm")
        self.offset_spin.valueChanged.connect(self._changed)
        form.addRow(_tr("Offset:"), self.offset_spin)

        self.copies_w = QtWidgets.QWidget()
        copies_layout = QtWidgets.QHBoxLayout(self.copies_w)
        copies_layout.setContentsMargins(0, 0, 0, 0)
        self.copies_spin = QtWidgets.QSpinBox()
        self.copies_spin.setRange(1, 72)
        self.copies_spin.setValue(3)
        self.copies_spin.valueChanged.connect(self._changed)
        copies_layout.addWidget(self.copies_spin)
        form.addRow(_tr("Copies:"), self.copies_w)

        if kind != "cylinder":
            self.spacing_w = QtWidgets.QWidget()
            spacing_layout = QtWidgets.QHBoxLayout(self.spacing_w)
            spacing_layout.setContentsMargins(0, 0, 0, 0)
            self.spacing_spin = QtWidgets.QDoubleSpinBox()
            self.spacing_spin.setRange(0.01, 100000.0)
            self.spacing_spin.setValue(10.0)
            self.spacing_spin.setDecimals(2)
            self.spacing_spin.setSuffix(" mm")
            self.spacing_spin.valueChanged.connect(self._changed)
            spacing_layout.addWidget(self.spacing_spin)
            form.addRow(_tr("Spacing:"), self.spacing_w)

            self.rev1_cb = QtWidgets.QCheckBox()
            self.rev1_cb.setChecked(False)
            self.rev1_cb.toggled.connect(self._changed)
            form.addRow(_tr("Invert leg 1:"), self.rev1_cb)

            self.rev2_cb = QtWidgets.QCheckBox()
            self.rev2_cb.setChecked(False)
            self.rev2_cb.toggled.connect(self._changed)
            form.addRow(_tr("Invert leg 2:"), self.rev2_cb)

        self.angle_spin = QtWidgets.QDoubleSpinBox()
        self.angle_spin.setRange(-90.0, 90.0)
        self.angle_spin.setValue(0.0)
        self.angle_spin.setDecimals(1)
        self.angle_spin.setSuffix("°")
        self.angle_spin.valueChanged.connect(self._changed)
        form.addRow(_tr("Rotation angle (°):"), self.angle_spin)

        self.shape_combo = QtWidgets.QComboBox()
        self.shape_combo.addItem(_tr("Rectangle"), "rectangle")
        self.shape_combo.addItem(_tr("Triangle"), "triangle")
        self.shape_combo.currentIndexChanged.connect(self._changed)
        form.addRow(_tr("Shape:"), self.shape_combo)
        self.shape_combo.blockSignals(True)
        if kind in ("corner", "cylinder"):
            self.shape_combo.setCurrentIndex(1)   # triangles by default
        self.shape_combo.blockSignals(False)

        layout.addLayout(form)

        if kind == "cylinder":
            self.copies_w.setVisible(True)
            self.angle_spin.setVisible(True)
            self.angle_spin.setRange(0.0, 360.0)
            self.shape_combo.setVisible(True)
            hint = QtWidgets.QLabel(_tr(
                "The rib is a plate closing the corner between the planar\n"
                "face and the cylinder, like between two non-parallel\n"
                "surfaces.  Rectangle or Triangle profile.  Copies places N\n"
                "plates rotated around the cylinder axis.  The inner edge\n"
                "sinks into the cylinder until both its corners touch the\n"
                "cylinder surface.  Angle rotates the ribs around the axis\n"
                "to position them where wanted."))
        elif kind == "corner":
            self.copies_w.setVisible(True)
            self.copies_spin.blockSignals(True)
            self.copies_spin.setValue(1)
            self.copies_spin.blockSignals(False)
            self.angle_spin.setVisible(False)
            self.shape_combo.setVisible(True)
            hint = QtWidgets.QLabel(_tr(
                "The rib is a plate closing the angle between two non-parallel\n"
                "planar faces.  Rectangle or Triangle profile.  L1 and L2 are\n"
                "the contact lengths on faces 1 and 2, measured from the\n"
                "corner edge.  Offset slides the plate along the corner edge.\n"
                "Copies places N plates spaced with the Spacing distance."))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(hint)

        preview_group = QtWidgets.QGroupBox(_tr("Preview"))
        preview_layout = QtWidgets.QVBoxLayout(preview_group)
        self.preview_result = QtWidgets.QCheckBox(_tr("Show final result"))
        self.preview_result.toggled.connect(self._preview_result_toggled)
        preview_layout.addWidget(self.preview_result)
        self.preview_overlap = QtWidgets.QCheckBox(
            _tr("Show overlapping preview"))
        self.preview_overlap.setChecked(True)
        self.preview_overlap.toggled.connect(self._preview_overlap_toggled)
        preview_layout.addWidget(self.preview_overlap)
        layout.addWidget(preview_group)

        layout.addStretch(1)

        self._changed()

    def _toggle_full(self, checked):
        if checked:
            self._manual = (
                self.l1_spin.value(), self.l2_spin.value())
            self.l1_spin.setValue(round(self._full_l1, 3))
            self.l2_spin.setValue(round(self._full_l2, 3))
            self.l1_spin.setEnabled(False)
            self.l2_spin.setEnabled(False)
        else:
            self.l1_spin.setEnabled(True)
            self.l2_spin.setEnabled(True)
            if self._manual is not None:
                self.l1_spin.setValue(self._manual[0])
                self.l2_spin.setValue(self._manual[1])
        self._changed()

    # ---- preview mode ----
    def preview_mode(self):
        cb = getattr(self, "preview_result", None)
        return "result" if cb is not None and cb.isChecked() else "tool"

    def _exclude(self, other):
        if other.isChecked():
            other.blockSignals(True)
            other.setChecked(False)
            other.blockSignals(False)

    def _preview_overlap_toggled(self, checked):
        if checked:
            self._exclude(self.preview_result)
        self._changed()

    def _preview_result_toggled(self, checked):
        if checked:
            self._exclude(self.preview_overlap)
        self._changed()

    # ---- values ----
    def _extra_kwargs(self):
        data = self.shape_combo.currentData()
        if not data:
            data = self.shape_combo.currentText().lower()
        if self._kind == "cylinder":
            return {"shape": data, "angle": self.angle_spin.value()}
        if self._kind == "corner":
            return {"shape": data, "spacing": self.spacing_spin.value()}
        return {"shape": data}

    def _common_args(self):
        copies = (self.copies_spin.value()
                  if self._kind in ("corner", "cylinder") else 1)
        rev1 = (self.rev1_cb.isChecked()
                if hasattr(self, "rev1_cb") else False)
        rev2 = (self.rev2_cb.isChecked()
                if hasattr(self, "rev2_cb") else False)
        return (
            self.l1_spin.value(),
            self.l2_spin.value(),
            self.thick_spin.value(),
            self.offset_spin.value(),
            copies,
            rev1,
            rev2,
            self.preview_mode(),
        )

    def _changed(self, *_args):
        try:
            kwargs = self._extra_kwargs()
            self._on_change(*self._common_args(), **kwargs)
        except Exception:
            import traceback
            traceback.print_exc()

    # ---- FreeCAD task dialog interface ----
    def getStandardButtons(self):
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

    def open(self):
        return True

    def accept(self):
        try:
            kwargs = self._extra_kwargs()
            self._on_finish(*self._common_args(), **kwargs)
            return True
        except Exception:
            import traceback
            traceback.print_exc()
            return False

    def reject(self):
        try:
            self._on_cancel()
        except Exception:
            import traceback
            traceback.print_exc()
        return True

    def closed(self):
        try:
            self._on_cancel()
        except Exception:
            pass
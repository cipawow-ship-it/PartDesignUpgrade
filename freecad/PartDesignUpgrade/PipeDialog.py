# -*- coding: utf-8 -*-
"""Task panel to pick the cross-section profile for a pipe.

Shown non-modally in FreeCAD's side Task dock (like PartDesign panels), so
the 3D view stays interactive and the result can be inspected while values
are adjusted. The panel drives a live preview through a callback.
"""

try:
    from PySide2 import QtWidgets
except ImportError:
    from PySide6 import QtWidgets

try:
    from .translations import tr as _tr
except ImportError:
    from translations import tr as _tr

PROFILE_TYPES = [
    "Circle",
    "Square",
    "Triangle",
    "Pentagon",
    "Hexagon",
    "Octagon",
]

_DIM_LABELS = {
    "Circle": "Radius:",
    "Square": "Side length:",
    "Triangle": "Side length:",
    "Pentagon": "Side length:",
    "Hexagon": "Side length:",
    "Octagon": "Side length:",
}


class PipeProfilePanel(object):
    """FreeCAD task panel for pipe settings with live preview.

    Wire *on_change* to rebuild the preview, *on_finish* to create the
    feature on OK, and *on_cancel* to drop the preview on cancel.
    """

    def __init__(self, on_change, on_finish, on_cancel):
        self._on_change = on_change
        self._on_finish = on_finish
        self._on_cancel = on_cancel

        self.form = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.form)

        form = QtWidgets.QFormLayout()
        self.type_combo = QtWidgets.QComboBox()
        for name in PROFILE_TYPES:
            self.type_combo.addItem(_tr(name), name)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        self.type_combo.currentTextChanged.connect(self._changed)
        form.addRow(_tr("Profile shape:"), self.type_combo)

        self.dim_spin = QtWidgets.QDoubleSpinBox()
        self.dim_spin.setRange(0.1, 100000.0)
        self.dim_spin.setValue(5.0)
        self.dim_spin.setDecimals(2)
        self.dim_spin.setSuffix(" mm")
        self.dim_label = QtWidgets.QLabel(_tr(_DIM_LABELS[PROFILE_TYPES[0]]))
        self.dim_spin.valueChanged.connect(self._changed)
        form.addRow(self.dim_label, self.dim_spin)

        self.thick_spin = QtWidgets.QDoubleSpinBox()
        self.thick_spin.setRange(0.0, 100000.0)
        self.thick_spin.setValue(0.0)
        self.thick_spin.setDecimals(2)
        self.thick_spin.setSuffix(" mm")
        self.thick_spin.valueChanged.connect(self._changed)
        form.addRow(_tr("Wall thickness:"), self.thick_spin)

        self.rot_spin = QtWidgets.QDoubleSpinBox()
        self.rot_spin.setRange(-180.0, 180.0)
        self.rot_spin.setValue(0.0)
        self.rot_spin.setDecimals(1)
        self.rot_spin.setSuffix("\u00b0")
        self.rot_spin.valueChanged.connect(self._changed)
        form.addRow(_tr("Rotation:"), self.rot_spin)

        self.corner_combo = QtWidgets.QComboBox()
        for name in ("Right corner", "Round corner", "Transformed"):
            self.corner_combo.addItem(_tr(name), name)
        self.corner_combo.currentTextChanged.connect(self._changed)
        form.addRow(_tr("Corner transition:"), self.corner_combo)

        layout.addLayout(form)

        offset_group = QtWidgets.QGroupBox(_tr("Profile offset"))
        offset_grid = QtWidgets.QGridLayout(offset_group)
        self.off_spins = []
        for i, axis in enumerate(["X", "Y"]):
            sp = QtWidgets.QDoubleSpinBox()
            sp.setRange(-100000.0, 100000.0)
            sp.setValue(0.0)
            sp.setDecimals(3)
            sp.setSuffix(" mm")
            sp.valueChanged.connect(self._changed)
            offset_grid.addWidget(QtWidgets.QLabel(axis), 0, i)
            offset_grid.addWidget(sp, 1, i)
            self.off_spins.append(sp)
        center_btn = QtWidgets.QPushButton(_tr("Center"))
        center_btn.setToolTip(_tr("Reset the offset to 0 (profile centered on the path)"))
        center_btn.clicked.connect(self._reset_offset)
        offset_grid.addWidget(center_btn, 0, 2, 2, 1)
        layout.addWidget(offset_group)

        hint = QtWidgets.QLabel(_tr(
            "Rotation turns the cross-section around the pipe axis.\n"
            "Offset (0 = centered on the path): X moves the profile sideways,\n"
            "Y moves it up/down (both also negative).\n"
            "Wall thickness (0 = solid): hollows out the pipe, keeping the\n"
            "dimension above as the EXTERNAL size."))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(hint)

        preview_group = QtWidgets.QGroupBox(_tr("Preview"))
        preview_layout = QtWidgets.QVBoxLayout(preview_group)
        self.preview_result = QtWidgets.QCheckBox(_tr("Show final result"))
        self.preview_result.toggled.connect(self._preview_result_toggled)
        preview_layout.addWidget(self.preview_result)
        self.preview_overlap = QtWidgets.QCheckBox(_tr("Show overlapping preview"))
        self.preview_overlap.setChecked(True)
        self.preview_overlap.toggled.connect(self._preview_overlap_toggled)
        preview_layout.addWidget(self.preview_overlap)
        layout.addWidget(preview_group)

        layout.addStretch(1)

        self._changed()

    # ---- preview mode ----
    def preview_mode(self):
        """'tool' shows the swept profile alone, 'result' shows body +/- pipe."""
        return "result" if self.preview_result.isChecked() else "tool"

    def _exclude(self, other):
        # turn the other checkbox off without re-triggering the exclusivity
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
    def profile_type(self):
        return self.type_combo.currentData()

    def dimension(self):
        return self.dim_spin.value()

    def rotation(self):
        return self.rot_spin.value()

    def wall_thickness(self):
        return self.thick_spin.value()

    def corner_mode(self):
        return self.corner_combo.currentData()

    def offset(self):
        """Return the profile offset as a (lateral, vertical) tuple of mm."""
        return tuple(sp.value() for sp in self.off_spins)

    def _reset_offset(self):
        for sp in self.off_spins:
            sp.setValue(0.0)

    def _changed(self, *_args):
        try:
            self._on_change(
                self.profile_type(), self.dimension(), self.rotation(),
                self.offset(), self.corner_mode(), self.wall_thickness(),
                self.preview_mode())
        except Exception:
            import traceback
            traceback.print_exc()

    def _on_type_changed(self, *_args):
        data = self.type_combo.currentData()
        self.dim_label.setText(_tr(_DIM_LABELS.get(data, "Dimension:")))

    # ---- FreeCAD task dialog interface ----
    def getStandardButtons(self):
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

    def open(self):
        return True

    def accept(self):
        try:
            self._on_finish(
                self.profile_type(), self.dimension(), self.rotation(),
                self.offset(), self.corner_mode(), self.wall_thickness(),
                self.preview_mode())
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
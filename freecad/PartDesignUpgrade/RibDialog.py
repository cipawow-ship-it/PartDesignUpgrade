# -*- coding: utf-8 -*-
"""Task panel for rib settings with live preview.

Shown non-modally in FreeCAD's side Task dock, like the pipe panel.
"""

try:
    from PySide2 import QtWidgets
except ImportError:
    from PySide6 import QtWidgets

try:
    from .translations import tr as _tr
except ImportError:
    from translations import tr as _tr


class RibPanel(object):
    """FreeCAD task panel for rib settings with live preview.

    Parameters
    ----------
    on_change : callable(thickness, midplane, reversed, mode)
        Called whenever a value changes to rebuild the live preview.
    on_finish : callable(thickness, midplane, reversed, mode)
        Called on OK to create the feature.
    on_cancel : callable()
        Called on Cancel to drop the preview.
    """

    def __init__(self, on_change, on_finish, on_cancel):
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

        self.midplane_cb = QtWidgets.QCheckBox()
        self.midplane_cb.setChecked(True)
        self.midplane_cb.toggled.connect(self._changed)
        form.addRow(_tr("Midplane:"), self.midplane_cb)

        self.reversed_cb = QtWidgets.QCheckBox()
        self.reversed_cb.setChecked(False)
        self.reversed_cb.toggled.connect(self._changed)
        form.addRow(_tr("Reversed:"), self.reversed_cb)

        layout.addLayout(form)

        hint = QtWidgets.QLabel(_tr(
            "Thickness is applied perpendicular to the sketch plane.\n"
            "Midplane: thickness extends equally on both sides.\n"
            "Reversed: flip the normal direction."))
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

    # ---- preview mode ----
    def preview_mode(self):
        return "result" if self.preview_result.isChecked() else "tool"

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
    def thickness(self):
        return self.thick_spin.value()

    def midplane(self):
        return self.midplane_cb.isChecked()

    def reversed(self):
        return self.reversed_cb.isChecked()

    def _changed(self, *_args):
        try:
            self._on_change(
                self.thickness(), self.midplane(), self.reversed(),
                self.preview_mode())
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
            self._on_finish(
                self.thickness(), self.midplane(), self.reversed(),
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

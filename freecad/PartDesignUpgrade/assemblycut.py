# -*- coding: utf-8 -*-
import FreeCAD
import FreeCADGui as Gui
import Part

try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide6 import QtCore, QtGui, QtWidgets

try:
    from .translations import tr as _tr
except ImportError:
    from translations import tr as _tr


class _BodyRowWidget(QtWidgets.QWidget):
    def __init__(self, name, checked, dialog, parent=None):
        super().__init__(parent)
        self.dialog = dialog
        self.body_name = name

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setChecked(checked)
        self.checkbox.setMinimumWidth(20)
        self.checkbox.toggled.connect(lambda val: dialog._set_checked(name, val))
        layout.addWidget(self.checkbox)

        self.label = QtWidgets.QLabel(name)
        layout.addWidget(self.label, 1)

        up_btn = QtWidgets.QPushButton("\u25B2")
        up_btn.setFixedSize(24, 24)
        up_btn.clicked.connect(lambda: dialog._move_body(name, -1))
        layout.addWidget(up_btn)

        down_btn = QtWidgets.QPushButton("\u25BC")
        down_btn.setFixedSize(24, 24)
        down_btn.clicked.connect(lambda: dialog._move_body(name, +1))
        layout.addWidget(down_btn)


class AssemblyCutDialog(object):
    """FreeCAD task panel for Assembly Cut (side dock), like native tools."""

    def __init__(self, sketch_name, body_names, preselected_names=None, on_finish=None):
        self._on_finish = on_finish

        self.form = QtWidgets.QWidget()
        self.form.setMinimumWidth(420)
        self.form.setMinimumHeight(400)

        self.preselected_names = preselected_names or set()

        layout = QtWidgets.QVBoxLayout(self.form)

        layout.addWidget(QtWidgets.QLabel(_tr("Sketch: ") + sketch_name))
        layout.addWidget(QtWidgets.QLabel(""))
        layout.addWidget(QtWidgets.QLabel(_tr("Select bodies to cut (reorder with arrows):")))

        if preselected_names:
            pre = [n for n in body_names if n in preselected_names]
            others = [n for n in body_names if n not in preselected_names]
            self._order = pre + others
        else:
            self._order = list(body_names)

        self._checked = {n: (n in self.preselected_names) for n in self._order}

        self.list_widget = QtWidgets.QListWidget()
        layout.addWidget(self.list_widget)
        self._rebuild_list()

        btn_layout = QtWidgets.QHBoxLayout()
        select_all_btn = QtWidgets.QPushButton(_tr("Select All"))
        select_all_btn.clicked.connect(self._select_all)
        deselect_all_btn = QtWidgets.QPushButton(_tr("Deselect All"))
        deselect_all_btn.clicked.connect(self._deselect_all)
        btn_layout.addWidget(select_all_btn)
        btn_layout.addWidget(deselect_all_btn)
        layout.addLayout(btn_layout)

        mode_group = QtWidgets.QGroupBox(_tr("Mode:"))
        mode_layout = QtWidgets.QVBoxLayout(mode_group)
        self._radio_sketch = QtWidgets.QRadioButton(_tr("Independent sketches (full copy)"))
        self._radio_binder = QtWidgets.QRadioButton(_tr("Binder (linked to sketch)"))
        self._radio_binder.setChecked(True)
        mode_layout.addWidget(self._radio_sketch)
        mode_layout.addWidget(self._radio_binder)
        layout.addWidget(mode_group)

        self._info_label = QtWidgets.QLabel(_tr("Each body gets an independent copy of the sketch."))
        self._info_label.setStyleSheet("color: #555;")
        layout.addWidget(self._info_label)
        self._radio_sketch.toggled.connect(self._update_info)
        self._radio_binder.toggled.connect(self._update_info)

    def _update_info(self):
        if self._radio_binder.isChecked():
            self._info_label.setText(_tr("Each body gets a binder linked to the original sketch."))
        else:
            self._info_label.setText(_tr("Each body gets an independent copy of the sketch."))

    def _rebuild_list(self):
        self.list_widget.clear()
        for name in self._order:
            item = QtWidgets.QListWidgetItem()
            item.setSizeHint(QtCore.QSize(0, 32))
            item.setData(QtCore.Qt.UserRole, name)
            widget = _BodyRowWidget(name, self._checked.get(name, False), self)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def _move_body(self, name, direction):
        idx = self._order.index(name)
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(self._order):
            return
        self._order[idx], self._order[new_idx] = self._order[new_idx], self._order[idx]
        self._rebuild_list()

    def _set_checked(self, name, val):
        self._checked[name] = val

    def _select_all(self):
        for n in self._order:
            self._checked[n] = True
        self._rebuild_list()

    def _deselect_all(self):
        for n in self._order:
            self._checked[n] = False
        self._rebuild_list()

    def get_selected(self):
        return [n for n in self._order if self._checked.get(n, False)]

    def get_mode(self):
        if self._radio_binder.isChecked():
            return "binder"
        return "sketch"

    # ---- FreeCAD task dialog interface ----
    def getStandardButtons(self):
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

    def open(self):
        return True

    def accept(self):
        # FreeCAD never calls a Python 'closed()' on task dialogs: the OK
        # button invokes accept() and, if it returns True, the panel is
        # removed synchronously. Defer the cut with a zero-delay timer so
        # that the Assembly Cut panel is already gone when Pocket opens.
        selected = self.get_selected()
        mode = self.get_mode()
        QtCore.QTimer.singleShot(0, lambda: self._run_finish(selected, mode))
        return True

    def reject(self):
        return True

    def _run_finish(self, selected, mode):
        try:
            if self._on_finish is not None:
                self._on_finish(selected, mode)
        except Exception:
            import traceback
            traceback.print_exc()


def _find_bodies(doc):
    bodies = []
    for obj in doc.Objects:
        if obj.TypeId == "PartDesign::Body":
            bodies.append(obj)
    return bodies


def _get_selected_sketch():
    sel = Gui.Selection.getSelection()
    if not sel:
        return None
    obj = sel[0]
    if obj.TypeId == "Sketcher::SketchObject":
        return obj
    return None


def _find_intersecting_bodies(doc, sketch, bodies):
    try:
        wires = sketch.Shape.Wires
        if not wires:
            return [b.Label for b in bodies]

        largest = max(wires, key=lambda w: abs(w.Length))
        face = Part.Face(largest)
        z_axis = sketch.Placement.Rotation.multVec(FreeCAD.Vector(0, 0, 1))

        solid_pos = face.extrude(z_axis * 10000.0)
        solid_neg = face.extrude(z_axis * -10000.0)
        bb_pos = solid_pos.BoundBox
        bb_neg = solid_neg.BoundBox
    except Exception:
        return [b.Label for b in bodies]

    result = []
    for body in bodies:
        try:
            body_bb = body.Shape.BoundBox
            hit = False

            if bb_pos.intersect(body_bb):
                common = body.Shape.common(solid_pos)
                if common and common.Volume > 0:
                    hit = True

            if not hit and bb_neg.intersect(body_bb):
                common = body.Shape.common(solid_neg)
                if common and common.Volume > 0:
                    hit = True

            if hit:
                result.append(body.Label)
        except Exception:
            pass
    return result


def _create_binder_in_body(doc, src_sketch, target_body):
    binder = target_body.newObject("PartDesign::SubShapeBinder", src_sketch.Label + "_Binder")
    binder.Support = [(src_sketch, "")]
    doc.recompute()
    try:
        binder.ViewObject.Visibility = False
    except Exception:
        pass
    return binder


def _copy_sketch_into_body(doc, src_sketch, target_body):
    new_sketch = target_body.newObject("Sketcher::SketchObject", src_sketch.Label + "_Copy")
    geo_list = []
    for geo in src_sketch.Geometry:
        copied = geo.copy()
        geo_list.append(copied)
    new_sketch.addGeometry(geo_list, False)
    new_sketch.Placement = src_sketch.Placement.copy()
    doc.recompute()
    try:
        new_sketch.ViewObject.Visibility = False
    except Exception:
        pass
    return new_sketch


def _preset_pocket_dialog():
    """Preset the active PartDesign Pocket task dialog to 'Through all' + 'Symmetric'.

    The Pocket dialog (FreeCAD 1.1, ui_TaskPadPocketParameters) exposes two
    combos inside the main window:
      - 'changeMode': Dimension, Through all, To first, Up to face, Up to shape
        -> 'Through all' is index 1
      - 'sidesMode': One sided, Two sided, Symmetric
        -> 'Symmetric' is index 2
    Returns True if at least one combo was found and set.
    """
    try:
        mw = Gui.getMainWindow()
        if mw is None:
            return False

        mode_combo = None
        sides_combo = None
        for c in mw.findChildren(QtWidgets.QComboBox):
            obj_name = c.objectName()
            if obj_name == "changeMode":
                mode_combo = c
            elif obj_name == "sidesMode":
                sides_combo = c

        applied = False
        if mode_combo is not None and mode_combo.count() > 1:
            if mode_combo.currentIndex() != 1:
                mode_combo.setCurrentIndex(1)
            applied = True
        if sides_combo is not None and sides_combo.count() > 2:
            if sides_combo.currentIndex() != 2:
                sides_combo.setCurrentIndex(2)
            applied = True
        return applied
    except Exception:
        return False


class _CutProcessor(QtCore.QObject):
    def __init__(self, sketch, bodies, mode="binder"):
        super().__init__()
        self.sketch = sketch
        self.bodies = list(bodies)
        self.mode = mode
        self.current_idx = 0
        self.copies = {}
        self.waiting_for_dialog = False
        self.preset_applied = False
        self.timer = QtCore.QTimer()
        self.timer.setInterval(200)
        self.timer.timeout.connect(self._on_tick)

    def start(self):
        if not self.bodies:
            return
        doc = FreeCAD.ActiveDocument

        for body in self.bodies:
            try:
                if self.mode == "binder":
                    new_obj = _create_binder_in_body(doc, self.sketch, body)
                else:
                    new_obj = _copy_sketch_into_body(doc, self.sketch, body)
                doc.recompute()
                self.copies[body.Name] = new_obj
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    None, _tr("Assembly Cut"),
                    _tr("Error creating profile for ") + body.Label + ":\n" + str(e)
                )
                return

        self.current_idx = 0
        self._process_next()

    def _process_next(self):
        if self.current_idx >= len(self.bodies):
            doc = FreeCAD.ActiveDocument
            if doc:
                doc.recompute()
            return

        body = self.bodies[self.current_idx]
        profile = self.copies.get(body.Name)

        if profile is None:
            self.current_idx += 1
            self._process_next()
            return

        try:
            body.ViewObject.doubleClicked()
        except Exception:
            pass

        doc = FreeCAD.ActiveDocument
        if doc:
            doc.recompute()

        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(
            FreeCAD.ActiveDocument.Name,
            profile.Name
        )

        self.waiting_for_dialog = True
        self.preset_applied = False
        Gui.runCommand("PartDesign_Pocket")
        _preset_pocket_dialog()
        self.timer.start()

    def _on_tick(self):
        if not self.waiting_for_dialog:
            return

        if not self.preset_applied and _preset_pocket_dialog():
            self.preset_applied = True

        has_panel = False
        try:
            editing = Gui.ActiveDocument.getInEdit()
            has_panel = (editing is not None)
        except Exception:
            has_panel = False

        if not has_panel:
            self.timer.stop()
            self.waiting_for_dialog = False

            doc = FreeCAD.ActiveDocument
            if doc:
                doc.recompute()

            self.current_idx += 1
            QtCore.QTimer.singleShot(300, self._process_next)


_active_processor = None


def assembly_cut():
    global _active_processor

    doc = FreeCAD.ActiveDocument
    if doc is None:
        QtWidgets.QMessageBox.warning(None, _tr("Assembly Cut"), _tr("No active document."))
        return

    sketch = _get_selected_sketch()
    if sketch is None:
        QtWidgets.QMessageBox.warning(
            None, _tr("Assembly Cut"), _tr("Select a Sketch first, then run this command.")
        )
        return

    bodies = _find_bodies(doc)
    if not bodies:
        QtWidgets.QMessageBox.information(
            None, _tr("Assembly Cut"), _tr("No PartDesign::Body found in document.")
        )
        return

    body_names = [b.Label for b in bodies]
    preselected = _find_intersecting_bodies(doc, sketch, bodies)
    name_to_body = {b.Label: b for b in bodies}

    def _finish(selected_names, mode):
        global _active_processor
        if not selected_names:
            return
        selected_bodies = [name_to_body[n] for n in selected_names]
        _active_processor = _CutProcessor(sketch, selected_bodies, mode)
        _active_processor.start()

    dialog = AssemblyCutDialog(sketch.Label, body_names, preselected, _finish)
    try:
        if Gui.Control.activeDialog():
            Gui.Control.closeDialog()
    except Exception:
        pass
    Gui.Control.showDialog(dialog)
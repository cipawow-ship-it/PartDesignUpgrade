# -*- coding: utf-8 -*-
"""Compute the weight/volume of a PartDesign body or shape with a material density picker.

Shown as a FreeCAD task panel in the side dock (like PartDesign panels).
When the document has several bodies, a combo lets you choose which one to
inspect and the panel also reports the total for all of them. Each body
keeps its own material choice (independent of the others). Selecting a body
in the 3D view or the tree switches the panel to it, and a table lists every
part with its assigned material and mass.
"""

import FreeCAD
import FreeCADGui as Gui

try:
    from PySide2 import QtWidgets
except ImportError:
    from PySide6 import QtWidgets

try:
    from .translations import tr as _tr, tr_material as _tr_mat
except ImportError:
    from translations import tr as _tr, tr_material as _tr_mat

# name -> density in kg/m3
DENSITY_PRESETS = {
    # Metalli / Metals
    "Acciaio / Steel": 7900.0,
    "Acciaio inox / Stainless steel": 8000.0,
    "Ghisa / Cast iron": 7150.0,
    "Ferro / Iron": 7870.0,
    "Alluminio / Aluminium": 2700.0,
    "Ottone / Brass": 8500.0,
    "Bronzo / Bronze": 8800.0,
    "Rame / Copper": 8960.0,
    "Zinco / Zinc": 7130.0,
    "Titanio / Titanium": 4500.0,
    "Nichel / Nickel": 8908.0,
    "Piombo / Lead": 11340.0,
    "Argento / Silver": 10490.0,
    "Oro / Gold": 19300.0,
    "Tungsteno / Tungsten": 19300.0,
    # Plastiche / Plastics
    "PLA": 1240.0,
    "ABS": 1040.0,
    "PETG": 1270.0,
    "ASA": 1070.0,
    "PA12 (Nylon)": 1010.0,
    "PA6 (Nylon)": 1130.0,
    "Policarbonato (PC) / Polycarbonate": 1200.0,
    "PMMA (Plexiglass)": 1180.0,
    "POM (Delrin)": 1410.0,
    "PE-HD / HDPE": 950.0,
    "PP (Polipropilene) / Polypropylene": 900.0,
    "TPU": 1210.0,
    "PTFE (Teflon)": 2200.0,
    "PEEK": 1320.0,
    # Legno / Wood
    "Quercia / Oak": 750.0,
    "Faggio / Beech": 700.0,
    "Abete / Pino / Spruce-Pine": 450.0,
    "Balsa": 150.0,
    # Altri materiali / Other materials
    "Vetro / Glass": 2500.0,
    "Calcestruzzo / Concrete": 2400.0,
    "Marmo / Marble": 2700.0,
    "Granito / Granite": 2700.0,
    "Custom...": None,
}

_DENSITY_NAMES = list(DENSITY_PRESETS.keys())

# ---- material persistence (stored on each measured object) ----
_PROPS_GROUP = "PartDesignUpgrade"
_PROP_MATERIAL = "PDU_Material"
_PROP_DENSITY = "PDU_Density"


def _ensure_storage(obj):
    """Attach material-persistence properties to a document object if possible."""
    for ptype, name, _default in (
            ("App::PropertyString", _PROP_MATERIAL, ""),
            ("App::PropertyFloat", _PROP_DENSITY, 7900.0)):
        if hasattr(obj, name):
            continue
        try:
            obj.addProperty(ptype, name, _PROPS_GROUP)
        except Exception:
            return False
    return True


def _load_state(obj):
    """Return [material_index, custom_density] persisted on the object, or None."""
    try:
        mat = str(getattr(obj, _PROP_MATERIAL, ""))
        dens = float(getattr(obj, _PROP_DENSITY, 7900.0))
    except Exception:
        return None
    if not mat:
        return None
    if mat == "Custom...":
        return [len(_DENSITY_NAMES) - 1, dens]
    try:
        return [_DENSITY_NAMES.index(mat), dens]
    except ValueError:
        return [0, dens]


def _save_state(obj, idx, dens):
    try:
        setattr(obj, _PROP_MATERIAL, _DENSITY_NAMES[idx])
        setattr(obj, _PROP_DENSITY, dens)
    except Exception:
        pass


def _volume(obj):
    try:
        return float(obj.Shape.Volume)
    except Exception:
        return 0.0


def _candidates():
    """Return ordered [(object, label)] for the bodies/shapes to measure.

    Order: current selection (with volume) first, then the active body, then
    all other PartDesign bodies. Only if the document has no bodies at all do
    we fall back to other shapes with volume.
    """
    doc = FreeCAD.ActiveDocument
    if doc is None:
        return []

    all_objects = doc.Objects
    bodies = [o for o in all_objects if o.TypeId == "PartDesign::Body" and _volume(o) > 0]
    others = [o for o in all_objects if o.TypeId != "PartDesign::Body" and _volume(o) > 0]

    order = []
    seen = set()

    for o in Gui.Selection.getSelection():
        if _volume(o) > 0 and o not in seen:
            order.append(o)
            seen.add(o)

    try:
        active = Gui.activeBody()
        if active is not None and _volume(active) > 0 and active not in seen:
            order.append(active)
            seen.add(active)
    except Exception:
        pass

    for o in bodies:
        if o not in seen:
            order.append(o)
            seen.add(o)

    if not bodies:
        for o in others:
            if o not in seen:
                order.append(o)
                seen.add(o)

    return [(o, ("Body: " + o.Label) if o.TypeId == "PartDesign::Body" else o.Label)
            for o in order]


class WeightVolumePanel(object):
    """FreeCAD task panel (side dock) for weight/volume of one or more bodies.

    Each listed part keeps its own material choice; switching body refreshes
    the material combo with that body's stored material. A selection made in
    the 3D view / tree is mirrored into the panel while it is open.
    """

    def __init__(self, candidates):
        self._candidates = candidates
        self._state = {}       # object -> [material index in DENSITY_PRESETS, custom density]
        self._can_store = {}   # object -> True if material persists on the object
        self._loading = False

        for o, _l in candidates:
            self._can_store[o] = _ensure_storage(o)
            st = _load_state(o)
            if st is not None:
                self._state[o] = st

        self.form = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(self.form)

        self.is_body = any(o.TypeId == "PartDesign::Body" for o, _ in candidates)

        form = QtWidgets.QFormLayout()

        self.body_combo = QtWidgets.QComboBox()
        for _o, label in candidates:
            self.body_combo.addItem(label)
        self.body_combo.currentIndexChanged.connect(self._on_body_changed)
        form.addRow(_tr("Body:") if self.is_body else _tr("Object:"), self.body_combo)

        self._volume_label = QtWidgets.QLabel("")
        form.addRow(_tr("Volume:"), self._volume_label)

        self._density_combo = QtWidgets.QComboBox()
        self._density_combo.addItems([_tr_mat(n) for n in _DENSITY_NAMES])
        self._density_combo.currentTextChanged.connect(self._on_density_changed)
        form.addRow(_tr("Material:"), self._density_combo)

        self._custom_spin = QtWidgets.QDoubleSpinBox()
        self._custom_spin.setRange(1.0, 100000.0)
        self._custom_spin.setValue(7900.0)
        self._custom_spin.setDecimals(0)
        self._custom_spin.setSuffix(" kg/m\u00b3")
        self._custom_spin.setEnabled(False)
        self._custom_spin.valueChanged.connect(self._on_custom_changed)
        form.addRow(_tr("Custom density:"), self._custom_spin)

        layout.addLayout(form)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        layout.addWidget(line)

        self._mass_label = QtWidgets.QLabel("")
        self._mass_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        layout.addWidget(self._mass_label)

        self._table = QtWidgets.QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels([_tr("Part"), _tr("Material"), _tr("Mass (g)")])
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setMaximumHeight(200)
        self._table.cellClicked.connect(self._on_table_clicked)
        layout.addWidget(self._table)

        self._total_label = QtWidgets.QLabel("")
        layout.addWidget(self._total_label)

        self._export_btn = QtWidgets.QPushButton(_tr("Export CSV…"))
        self._export_btn.setToolTip(_tr("Save the part list with material and mass as a CSV file."))
        self._export_btn.clicked.connect(self._on_export)
        layout.addWidget(self._export_btn)

        layout.addStretch(1)

        if len(candidates) > 1:
            hint = QtWidgets.QLabel(_tr(
                "Each part keeps its own material. 'Total' sums every part\n"
                "with the material assigned to each one. Selecting a body in\n"
                "the 3D view (or clicking a row) selects it here."))
            hint.setWordWrap(True)
            hint.setStyleSheet("color: #888; font-size: 10px;")
            layout.addWidget(hint)

        first = self._current_object()
        if first is not None:
            st = self._state.setdefault(first, [0, 7900.0])
            self._loading = True
            self._density_combo.setCurrentIndex(st[0])
            self._custom_spin.setValue(st[1])
            self._loading = False
            self._custom_spin.setEnabled(_DENSITY_NAMES[self._density_combo.currentIndex()] == "Custom...")

        self._update()

    # ---- state ----
    def _current_object(self):
        idx = self.body_combo.currentIndex()
        if idx < 0 or idx >= len(self._candidates):
            return None
        return self._candidates[idx][0]

    def _state_of(self, obj):
        return self._state.setdefault(obj, [0, 7900.0])

    def _density_for(self, obj):
        st = self._state_of(obj)
        val = DENSITY_PRESETS[_DENSITY_NAMES[st[0]]]
        if val is None:
            return st[1]
        return val

    # ---- handlers ----
    def _on_body_changed(self, index):
        o = self._current_object()
        if o is None:
            return
        if o.TypeId == "PartDesign::Body":
            try:
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(o.Document.Name, o.Name)
            except Exception:
                pass
        st = self._state_of(o)
        self._loading = True
        self._density_combo.setCurrentIndex(min(st[0], self._density_combo.count() - 1))
        self._custom_spin.setValue(st[1])
        self._loading = False
        self._custom_spin.setEnabled(_DENSITY_NAMES[self._density_combo.currentIndex()] == "Custom...")
        self._update()

    def _on_table_clicked(self, row, _col):
        if 0 <= row < len(self._candidates) and self.body_combo.currentIndex() != row:
            self.body_combo.setCurrentIndex(row)

    def _on_density_changed(self, text):
        if not self._loading:
            o = self._current_object()
            if o is not None:
                self._state_of(o)[0] = self._density_combo.currentIndex()
                if self._can_store.get(o):
                    _save_state(o, self._density_combo.currentIndex(),
                                self._custom_spin.value())
        self._custom_spin.setEnabled(_DENSITY_NAMES[self._density_combo.currentIndex()] == "Custom...")
        self._update()

    def _on_custom_changed(self, value):
        if self._loading:
            return
        o = self._current_object()
        if o is not None:
            self._state_of(o)[1] = value
            if self._can_store.get(o):
                _save_state(o, self._density_combo.currentIndex(), value)
        self._update()

    def _on_export(self):
        import csv, os
        if not self._candidates:
            return
        doc = FreeCAD.ActiveDocument
        try:
            default_dir = FreeCAD.getUserAppDataDir()
        except Exception:
            default_dir = os.path.expanduser("~")
        base = doc.Name if doc else "BOM"
        default_path = os.path.join(default_dir or "", base + "_BOM.csv")
        path, _f = QtWidgets.QFileDialog.getSaveFileName(
            self.form, _tr("Export BOM as CSV"), default_path,
            _tr("CSV files (*.csv)"))
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write("\ufeff")
                w = csv.writer(fh, delimiter=";")
                w.writerow([
                    _tr("Part"), _tr("Material"), _tr("Mass (g)"),
                    _tr("Volume (cm\u00b3)"), _tr("Density (kg/m\u00b3)")])
                for co, label in self._candidates:
                    vol_cm3 = _volume(co) / 1000.0
                    density = self._density_for(co)
                    mass_g = vol_cm3 * density / 1000.0
                    w.writerow([
                        label,
                        _tr_mat(_DENSITY_NAMES[self._state_of(co)[0]]),
                        "{:.3f}".format(mass_g),
                        "{:.3f}".format(vol_cm3),
                        "{:.4g}".format(density)])
                if len(self._candidates) > 1:
                    total_v = sum(_volume(co) for co, _ in self._candidates) / 1000.0
                    total_g = sum(_volume(co) * 1e-6 * self._density_for(co)
                                  for co, _ in self._candidates)
                    w.writerow(["", _tr("Total"), "{:.3f}".format(total_g),
                                "{:.3f}".format(total_v), ""])
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self.form, _tr("Export BOM as CSV"),
                _tr("Unable to write file:\n{}").format(e))
            return
        QtWidgets.QMessageBox.information(
            self.form, _tr("Export BOM as CSV"),
            _tr("BOM exported to:\n{}").format(path))

    # ---- selection observer (3D view / tree -> panel) ----
    def addSelection(self, docname, objname, subname, pnt):
        try:
            self._on_external_selection(docname, objname)
        except Exception:
            pass

    def clearSelection(self, docname):
        pass

    def setSelection(self, docname):
        pass

    def _on_external_selection(self, docname, objname):
        target = None
        for i, (o, _l) in enumerate(self._candidates):
            if getattr(o, "Name", None) == objname:
                target = i
                break
        if target is None:
            # a feature of a body was selected: switch to its owning body
            for i, (o, _l) in enumerate(self._candidates):
                if o.TypeId != "PartDesign::Body":
                    continue
                try:
                    if o.Document.Name != docname:
                        continue
                    for f in o.Group:
                        if getattr(f, "Name", None) == objname:
                            target = i
                            break
                except Exception:
                    pass
                if target is not None:
                    break
        if target is not None and self.body_combo.currentIndex() != target:
            self.body_combo.setCurrentIndex(target)

    # ---- display ----
    def _update(self, *_):
        o = self._current_object()
        if o is None:
            return
        volume = _volume(o)
        density = self._density_for(o)

        self._volume_label.setText(
            "{:.1f} mm\u00b3  =  {:.4f} cm\u00b3".format(volume, volume / 1000.0))

        mass_g = volume * 1e-6 * density
        self._mass_label.setText(
            _tr("Mass: {:.3f} g   ({:.6f} kg)").format(mass_g, mass_g / 1000.0))

        self._table.setRowCount(len(self._candidates))
        for i, (co, label) in enumerate(self._candidates):
            mat = _DENSITY_NAMES[self._state_of(co)[0]]
            m = _volume(co) * 1e-6 * self._density_for(co)
            self._table.setItem(i, 0, QtWidgets.QTableWidgetItem(label))
            self._table.setItem(i, 1, QtWidgets.QTableWidgetItem(_tr_mat(mat)))
            self._table.setItem(i, 2, QtWidgets.QTableWidgetItem("{:.3f}".format(m)))
        self._table.selectRow(self.body_combo.currentIndex())

        if len(self._candidates) > 1:
            total_volume = sum(_volume(co) for co, _ in self._candidates)
            total_g = sum(_volume(co) * 1e-6 * self._density_for(co)
                          for co, _ in self._candidates)
            self._total_label.setText(
                _tr("Total ({} parts): {:.3f} g   ({:.3f} cm\u00b3)").format(
                    len(self._candidates), total_g, total_volume / 1000.0))
        else:
            self._total_label.setText("")

    # ---- FreeCAD task dialog interface ----
    def getStandardButtons(self):
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

    def open(self):
        try:
            Gui.Selection.addObserver(self)
        except Exception:
            pass
        return True

    def _detach_observer(self):
        try:
            Gui.Selection.removeObserver(self)
        except Exception:
            pass

    def accept(self):
        self._detach_observer()
        return True

    def reject(self):
        self._detach_observer()
        return True

    def closed(self):
        self._detach_observer()


def weight_volume():
    candidates = _candidates()
    if not candidates:
        QtWidgets.QMessageBox.warning(
            None,
            _tr("Weight / Volume"),
            _tr("Select a PartDesign body or a shape with volume first."))
        return

    panel = WeightVolumePanel(candidates)

    try:
        if Gui.Control.activeDialog():
            Gui.Control.closeDialog()
    except Exception:
        pass
    Gui.Control.showDialog(panel)
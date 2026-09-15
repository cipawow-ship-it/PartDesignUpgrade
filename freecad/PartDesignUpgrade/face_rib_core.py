# -*- coding: utf-8 -*-
"""Rib-between-faces feature core geometry and feature classes.

Unlike the sketch-based rib, this feature needs NO sketch: the user selects
two faces of an existing part and the rib (a stiffening plate) is generated
between them.

Two cases are supported:

1. Two angled planar faces forming a corner.  The rib is a plate closing
   the angle: ``length1`` / ``length2`` are the contact lengths on the two
   faces measured from the corner edge (Rectangle or Triangle profile).
   ``offset`` slides the plate along the corner edge; ``copies`` with
   ``spacing`` builds several ribs along the edge.

2. A planar face plus a cylindrical face.  The rib is a vertical plate from
   the planar face up against the cylinder (contact along a generatrix).
   ``length1`` is the contact length up the cylinder, ``length2`` is the
   contact length on the planar face.  ``copies`` places N identical ribs
   rotated around the cylinder axis; ``angle`` rotates the whole set.

The geometry lives in document coordinates (the same frame the selected
faces resolve to), so features may be used inside PartDesign bodies or as
standalone Part objects.
"""

import math

import FreeCAD
import Part

try:
    from .translations import tr as _tr
except ImportError:
    from translations import tr as _tr

from .rib_core import _refine

_OVERLAP = 0.5
_EPS = 1e-7


def _is_triangle_shape(shp):
    """True when a user-supplied shape value means a triangular plate."""
    if not isinstance(shp, str):
        shp = str(shp)
    return shp.lower() in ("triangle", "trapezoid", "triangolo", "3", "t")


# =============================================================================
# Surface helpers
# =============================================================================

def _geometry_type(s):
    t = getattr(s, "TypeId", "") or ""
    return t


def _plane_normal(face):
    """Outward face normal for a planar face (unit length)."""
    try:
        n = face.normalAt(0.0, 0.0)
        if n.Length > _EPS:
            return n.normalize()
    except Exception:
        pass
    s = face.Surface
    for name in ("Axis", "Normal"):
        if hasattr(s, name):
            v = getattr(s, name)
            if hasattr(v, "Length") and v.Length > _EPS:
                return v.normalize()
    return FreeCAD.Vector(0, 0, 1)


def _is_plane_face(face):
    t = _geometry_type(face.Surface)
    if "Plane" in t or "GeomPlane" in t:
        return True
    s = face.Surface
    return hasattr(s, "Position") and hasattr(s, "Axis") and hasattr(s, "XAxis")


def _is_cylinder_face(face):
    t = _geometry_type(face.Surface)
    if "Cylinder" in t or "GeomCylinder" in t:
        return True
    return hasattr(face.Surface, "Radius")


def _cylinder_info(face):
    """Return (axis_point, axis_unit, radius) for a cylindrical face or None."""
    s = face.Surface
    try:
        radius = float(s.Radius)
    except Exception:
        return None
    if radius <= _EPS:
        return None
    ap = getattr(s, "AxisPoint", None) or getattr(s, "Center", None)
    ad = getattr(s, "AxisDirection", None) or getattr(s, "Axis", None)
    if isinstance(ad, (tuple, list)):
        if ap is None and len(ad) > 0:
            ap = ad[0]
        if len(ad) > 1:
            ad = ad[1]
    if ad is None or not hasattr(ad, "Length") or ad.Length <= _EPS:
        return None
    if ap is None:
        ap = FreeCAD.Vector(0, 0, 0)
    return ap, ad.normalize(), radius


def _perpendicular(vec):
    """Any unit vector perpendicular to *vec* (unit not required)."""
    tmp = FreeCAD.Vector(1, 0, 0)
    if abs(vec.dot(tmp)) > 0.9:
        tmp = FreeCAD.Vector(0, 1, 0)
    out = tmp - vec * (tmp.dot(vec) / vec.dot(vec))
    return out.normalize()


def _cut_proj(p, ap, ad):
    return p - ap - ad * ((p - ap).dot(ad))


def _planar_principal_dir(face, n):
    """In-plane direction of largest spread across the face boundary."""
    verts = [v.Point for v in face.Vertexes]
    if not verts:
        return _perpendicular(n)
    u0 = _perpendicular(n)
    v0 = n.cross(u0)
    xs = [p.dot(u0) for p in verts]
    ys = [p.dot(v0) for p in verts]
    dx = max(xs) - min(xs)
    dy = max(ys) - min(ys)
    return (u0 if dx >= dy else v0).normalize()


# =============================================================================
# Classification
# =============================================================================

def classify_faces(face_a, face_b):
    """Classify the two faces.

    Returns
    -------
    str
        ``'cylinder'``, ``'corner'``, or ``None`` when the pair is not
        supported.
    """
    a_plane = _is_plane_face(face_a)
    b_plane = _is_plane_face(face_b)
    a_cyl = _is_cylinder_face(face_a)
    b_cyl = _is_cylinder_face(face_b)

    if a_plane and b_plane:
        na = _plane_normal(face_a)
        nb = _plane_normal(face_b)
        if abs(na.dot(nb)) > 0.99:
            return None
        return "corner"
    if (a_plane and b_cyl) or (a_cyl and b_plane):
        return "cylinder"
    return None


# =============================================================================
# Geometry builders
# =============================================================================

def _solid_from_basis(origin, x_vec, y_vec, z_vec, lx, ly, lz):
    """Build an axis-aligned box in a custom orthonormal basis."""
    m = FreeCAD.Matrix()
    m.A11, m.A21, m.A31 = x_vec.x, x_vec.y, x_vec.z
    m.A12, m.A22, m.A32 = y_vec.x, y_vec.y, y_vec.z
    m.A13, m.A23, m.A33 = z_vec.x, z_vec.y, z_vec.z
    rot = FreeCAD.Rotation(m)
    box = Part.makeBox(lx, ly, lz)
    box.Placement = FreeCAD.Placement(origin, rot)
    return box


def _cap_box(pos, n_dir, vertical, length, ext):
    """Half-space box: bottom face is the plane through *pos* normal *n_dir*,
    occupying the +*n_dir* side, centered laterally on *pos*."""
    n = n_dir.normalize()
    ad = vertical.normalize()
    e = ad.cross(n)         # right-handed basis (e, h, n)
    if e.Length <= _EPS:
        e = _perpendicular(n)
    e.normalize()
    h = n.cross(e)          # in-plane perpendicular to e
    pnt = pos - e * ext - h * ext
    return _solid_from_basis(pnt, e, h, n, 2.0 * ext, 2.0 * ext, length)


def _validate(length1, length2, thickness):
    if float(thickness) <= 0:
        raise ValueError(_tr("Thickness must be positive"))
    if float(length1) <= 0:
        raise ValueError(_tr("Length on face 1 must be positive"))
    if float(length2) <= 0:
        raise ValueError(_tr("Length on face 2 must be positive"))


def build_cylinder_rib(face_flat, face_cyl, length1, length2, thickness,
                       copies=3, offset=0.0, shape="rectangle", angle=0.0,
                       penetration=None):
    """One or more gusset plates standing on a planar face against a cylinder.

    The plate closes the corner between the planar face and the cylindrical
    wall exactly like the corner rib between two non-parallel faces: a flat
    plate (``shape='rectangle'``) or a triangular gusset (``shape='triangle'``).
    Length1 runs upward along the cylinder, Length2 outward on the planar
    face, both measured from the corner.  Offset slides the plate along the
    cylinder axis; Copies places several plates rotated around the axis.
    ``angle`` (degrees) rotates the whole set around the cylinder axis to
    position the ribs where wanted.

    Penetration: a thin plate whose inner side is radial-tangent to the
    cylinder only touches it along one line ("resting").  By default the
    plate is sunk radially inward until both inner corners (at +- t/2 across
    the thickness) touch the cylinder surface, so ``r_in = sqrt(r^2-(t/2)^2)``.
    Pass an explicit depth to override (``r_in = radius - depth``).
    """
    copies = max(1, int(round(float(copies))))
    _validate(length1, length2, thickness)
    t = float(thickness)
    l1, l2 = float(length1), float(length2)

    info = _cylinder_info(face_cyl)
    if info is None:
        raise ValueError(_tr("The cylindrical face could not be read."))
    ap, ad_raw, radius = info
    ad, z0, _zmin, _zmax = _cyl_axis_oriented(face_cyl, face_flat, ad_raw)

    c = face_flat.CenterOfGravity
    radial = (c - ap) - ad * ((c - ap).dot(ad))
    if radial.Length <= _EPS:
        raise ValueError(_tr("Could not determine the radial direction."))
    rd = radial.normalize()
    ang = float(angle or 0.0)
    if ang != 0.0:
        rd = FreeCAD.Rotation(ad, ang).multVec(rd)

    z_bot = z0 + float(offset)
    z_top = z_bot + l1

    if penetration is None:
        half_t = t / 2.0
        r_in = math.sqrt(max(radius * radius - half_t * half_t, 0.0))
    else:
        r_in = max(radius - max(0.0, float(penetration)), 0.0)
    r_out = radius + l2

    p0 = ap + ad * z_bot + rd * r_in        # corner at flat-face level
    p1 = ap + ad * z_top + rd * r_in        # up the cylinder wall
    p2 = ap + ad * z_bot + rd * r_out       # outward on the planar face
    if _is_triangle_shape(shape):
        verts = [p0, p1, p2]
    else:
        p3 = ap + ad * z_top + rd * r_out
        verts = [p0, p1, p3, p2]

    m = (verts[1] - verts[0]).cross(verts[2] - verts[0])
    ml = m.Length
    if ml <= _EPS:
        raise ValueError(_tr("The two faces share the same centre."))
    m.multiply(t / ml)
    wire = Part.makePolygon([v for v in verts] + [verts[0]], True)
    solid = Part.Face(wire).extrude(m)
    solid.translate(-m * 0.5)               # centre the thickness

    if copies == 1:
        return _refine(solid)

    plates = [solid]
    for k in range(1, copies):
        cpy = solid.copy()
        cpy.rotate(ap, ad, k * 360.0 / copies)
        plates.append(cpy)
    result = plates[0]
    for pl in plates[1:]:
        result = result.fuse(pl)
    return _refine(result)


def _plane_intersection_line(plane_a, plane_b):
    """Intersection line of two non-parallel planes as (point, unit_dir)."""
    n_a = _plane_normal(plane_a)
    n_b = _plane_normal(plane_b)
    p_a = plane_a.CenterOfGravity
    p_b = plane_b.CenterOfGravity
    d_a = n_a.dot(p_a)
    d_b = n_b.dot(p_b)
    i_raw = n_a.cross(n_b)
    il = i_raw.Length
    if il < 1e-9:
        return None
    i = FreeCAD.Vector(i_raw)
    i.multiply(1.0 / il)
    ref = FreeCAD.Vector(0.0, 0.0, 1.0)
    for cand in ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                 (1.0, 1.0, 1.0)):
        v = FreeCAD.Vector(*cand)
        if abs(v.dot(i)) > 0.2:
            ref = v
            break
    det = n_a.dot(n_b.cross(ref))
    if abs(det) < 1e-9:
        return None
    c = ref.dot(p_a + p_b) * 0.5
    q1 = n_b.cross(ref)
    q2 = ref.cross(n_a)
    q = FreeCAD.Vector(
        (d_a * q1.x + d_b * q2.x + c * i_raw.x) / det,
        (d_a * q1.y + d_b * q2.y + c * i_raw.y) / det,
        (d_a * q1.z + d_b * q2.z + c * i_raw.z) / det,
    )
    return q, i


def _corner_axes(face_a, face_b, offset=0.0):
    """Axis frame of a corner gusset.

    Returns (r0, i, w_a, w_b, n_a, n_b): the reference point on the
    intersection line (already shifted by *offset* along the line), the unit
    direction of the intersection line, the two in-plane directions pointing
    from the corner line into faces A and B, and the two face normals.
    """
    r = _plane_intersection_line(face_a, face_b)
    if r is None:
        raise ValueError(_tr("The two faces share the same centre."))
    r0, i = r
    off = float(offset or 0.0)
    if off != 0.0:
        r0 = FreeCAD.Vector(r0.x + i.x * off, r0.y + i.y * off,
                            r0.z + i.z * off)
    n_a = _plane_normal(face_a)
    n_b = _plane_normal(face_b)
    w_a = i.cross(n_a)
    if w_a.dot(face_a.CenterOfGravity - r0) < 0.0:
        w_a.multiply(-1.0)
    w_b = n_b.cross(i)
    if w_b.dot(face_b.CenterOfGravity - r0) < 0.0:
        w_b.multiply(-1.0)
    return r0, i, w_a, w_b, n_a, n_b


def build_corner_rib(face_a, face_b, length1, length2, thickness, offset=0.0,
                     shape="triangle", copies=1, spacing=10.0,
                     flip_a=False, flip_b=False):
    """Plate(s) closing the corner between two angled planar faces.

    The two long edges of the plate lie on the two faces over their whole
    length (Length1 along face A, Length2 along face B, measured from the
    intersection line).  ``shape='rectangle'`` yields the full parallelogram
    plate, ``shape='triangle'`` the triangular gusset.  The thickness is
    applied centred, perpendicular to the plate plane.

    ``copies`` builds several ribs spaced ``spacing`` mm apart (centre to
    centre) along the corner line; the first one sits at *offset*.
    ``flip_a`` / ``flip_b`` mirror each cathetus (the leg lying on face A /
    face B) onto the other side of the corner edge.
    """
    copies = max(1, int(round(float(copies))))
    _validate(length1, length2, thickness)
    t = float(thickness)
    l1, l2 = float(length1), float(length2)
    spacing = float(spacing or 0.0)
    r0_base, i_d, w_a, w_b, _n_a, _n_b = _corner_axes(face_a, face_b, 0.0)
    if flip_a:
        w_a = FreeCAD.Vector(-w_a.x, -w_a.y, -w_a.z)
    if flip_b:
        w_b = FreeCAD.Vector(-w_b.x, -w_b.y, -w_b.z)
    solids = []
    for k in range(copies):
        r0 = FreeCAD.Vector(
            r0_base.x + i_d.x * (float(offset) + spacing * k),
            r0_base.y + i_d.y * (float(offset) + spacing * k),
            r0_base.z + i_d.z * (float(offset) + spacing * k))
        v0 = r0
        v1 = FreeCAD.Vector(r0.x + w_a.x * l1, r0.y + w_a.y * l1,
                            r0.z + w_a.z * l1)
        v2 = FreeCAD.Vector(r0.x + w_b.x * l2, r0.y + w_b.y * l2,
                            r0.z + w_b.z * l2)
        if _is_triangle_shape(shape):
            verts = [v0, v1, v2]
        else:
            v3 = FreeCAD.Vector(
                r0.x + w_a.x * l1 + w_b.x * l2,
                r0.y + w_a.y * l1 + w_b.y * l2,
                r0.z + w_a.z * l1 + w_b.z * l2)
            verts = [v0, v1, v3, v2]
        m = (v1 - v0).cross(v2 - v0)
        ml = m.Length
        if ml < 1e-9:
            raise ValueError(_tr("The two faces share the same centre."))
        m.multiply(1.0 / ml)
        wire = Part.makePolygon(verts + [verts[0]], True)
        solid = Part.Face(wire).extrude(
            FreeCAD.Vector(m.x * t, m.y * t, m.z * t))
        half = t / 2.0
        solid.translate(FreeCAD.Vector(-m.x * half, -m.y * half,
                                       -m.z * half))
        solids.append(_refine(solid))
    result = solids[0]
    for s in solids[1:]:
        result = result.fuse(s)
    return _refine(result)


def build_face_rib(face_a, face_b, length1, length2, thickness, offset=0.0,
                   copies=3, flip_a=False, flip_b=False, angle=0.0,
                   shape="rectangle", spacing=10.0):
    """Build the rib solid for the given face pair.

    Returns
    -------
    (Part.Shape, str)
        The rib solid and the case kind (``'corner'`` or
        ``'cylinder'``).
    """
    kind = classify_faces(face_a, face_b)
    if kind == "corner":
        return (
            build_corner_rib(face_a, face_b, length1, length2, thickness,
                             offset, shape, copies, spacing, flip_a, flip_b),
            kind,
        )
    if kind == "cylinder":
        if _is_plane_face(face_a):
            flat, cyl = face_a, face_b
        else:
            flat, cyl = face_b, face_a
        return (
            build_cylinder_rib(flat, cyl, length1, length2, thickness, copies,
                               offset, shape, angle),
            kind,
        )
    raise ValueError(_tr(
        "The faces are not usable: select two angled planar faces, or a "
        "planar face and a cylinder."))


# =============================================================================
# Reference resolution
# =============================================================================

def _resolve_face(fp, propname):
    try:
        raw = getattr(fp, propname)
        if hasattr(raw, "getValue"):
            obj, sub = raw.getValue()
        elif isinstance(raw, (tuple, list)) and len(raw) == 2:
            obj, sub = raw
        else:
            return None
        if isinstance(sub, (tuple, list)):
            sub = sub[0]
        sh = obj.getSubObject(sub)
    except Exception:
        return None
    if sh is None:
        return None
    if sh.ShapeType == "Face":
        return sh
    if sh.Faces:
        return sh.Faces[0]
    return None


# =============================================================================
# Feature proxies
# =============================================================================

def _setup_properties(obj):
    if not hasattr(obj, "F1Ref"):
        obj.addProperty("App::PropertyLinkSub", "F1Ref", "RibBetweenFaces")
    if not hasattr(obj, "F2Ref"):
        obj.addProperty("App::PropertyLinkSub", "F2Ref", "RibBetweenFaces")
    if not hasattr(obj, "Thickness"):
        obj.addProperty("App::PropertyLength", "Thickness", "RibBetweenFaces")
        obj.Thickness = 5.0
    if not hasattr(obj, "Length1"):
        obj.addProperty("App::PropertyLength", "Length1", "RibBetweenFaces")
        obj.Length1 = 20.0
    if not hasattr(obj, "Length2"):
        obj.addProperty("App::PropertyLength", "Length2", "RibBetweenFaces")
        obj.Length2 = 20.0
    if not hasattr(obj, "Offset"):
        obj.addProperty("App::PropertyDistance", "Offset", "RibBetweenFaces")
        obj.Offset = 0.0
    if not hasattr(obj, "Copies"):
        obj.addProperty("App::PropertyInteger", "Copies", "RibBetweenFaces")
        obj.Copies = 3
    if not hasattr(obj, "Spacing"):
        obj.addProperty("App::PropertyLength", "Spacing", "RibBetweenFaces")
        obj.Spacing = 10.0
    if not hasattr(obj, "Reversed"):
        obj.addProperty("App::PropertyBool", "Reversed", "RibBetweenFaces")
        obj.Reversed = False
    if not hasattr(obj, "Reversed1"):
        obj.addProperty("App::PropertyBool", "Reversed1", "RibBetweenFaces")
        obj.Reversed1 = False
    if not hasattr(obj, "Reversed2"):
        obj.addProperty("App::PropertyBool", "Reversed2", "RibBetweenFaces")
        obj.Reversed2 = False
    if not hasattr(obj, "Angle"):
        obj.addProperty("App::PropertyAngle", "Angle", "RibBetweenFaces")
        obj.Angle = 0.0
    if not hasattr(obj, "ProfileType"):
        obj.addProperty("App::PropertyEnumeration", "ProfileType",
                        "RibBetweenFaces")
        obj.ProfileType = ["rectangle", "triangle"]
        obj.ProfileType = "rectangle"
    if not hasattr(obj, "Refine"):
        obj.addProperty("App::PropertyBool", "Refine", "RibBetweenFaces")
        obj.Refine = True
    if not hasattr(obj, "Sketch"):
        obj.addProperty("App::PropertyLink", "Sketch", "RibBetweenFaces")


def _build_fp(fp):
    fa = _resolve_face(fp, "F1Ref")
    fb = _resolve_face(fp, "F2Ref")
    if fa is None or fb is None:
        return None
    flip_a = bool(getattr(fp, "Reversed1", False))
    flip_b = bool(getattr(fp, "Reversed2", False))
    legacy = getattr(fp, "Reversed", False)
    if legacy and (not hasattr(fp, "Reversed1")
                   or not hasattr(fp, "Reversed2")):
        flip_a = flip_b = True
    return build_face_rib(
        fa, fb,
        float(fp.Length1),
        float(fp.Length2),
        float(fp.Thickness),
        float(fp.Offset),
        int(getattr(fp, "Copies", 3)),
        flip_a,
        flip_b,
        float(getattr(fp, "Angle", 0.0)),
        str(getattr(fp, "ProfileType", "rectangle")),
        float(getattr(fp, "Spacing", 10.0)),
    )[0]


class FaceRibFeature:
    """Standalone parametric rib between two faces (no body required)."""

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "FaceRibFeature"
        _setup_properties(obj)

    def execute(self, fp):
        try:
            shape = _build_fp(fp)
            if shape is None:
                fp.Shape = Part.Shape()
                return
            fp.Shape = _refine(shape) if fp.Refine else shape
        except Exception as e:
            FreeCAD.Console.PrintError(
                "FaceRibFeature.execute error: {}\n".format(e))
            fp.Shape = Part.Shape()


class AdditiveFaceRibFeature:
    """PartDesign additive rib between faces: fused with the body tip."""

    def __init__(self, obj):
        obj.Proxy = self
        self.Type = "AdditiveFaceRibFeature"
        _setup_properties(obj)

    def execute(self, fp):
        try:
            shape = _build_fp(fp)
            if shape is None:
                fp.Shape = Part.Shape()
                return
            base = getattr(fp, "BaseFeature", None)
            if base is not None and base.Shape is not None and not base.Shape.isNull():
                shape = base.Shape.fuse(shape)
            fp.Shape = _refine(shape) if fp.Refine else shape
        except Exception as e:
            FreeCAD.Console.PrintError(
                "AdditiveFaceRibFeature.execute error: {}\n".format(e))
            fp.Shape = Part.Shape()


# =============================================================================
# Selection helpers
# =============================================================================

def _collect_face_selection():
    """Return an ordered list of (object, subelement) tuples for faces."""
    import FreeCADGui as Gui
    picked = []
    for se in Gui.Selection.getSelectionEx():
        obj = se.Object
        if obj is None:
            continue
        subs = list(se.SubElementNames or [])
        if not subs:
            try:
                if getattr(obj, "Shape", None) is not None and len(obj.Shape.Faces) == 1:
                    picked.append((obj, "Face1"))
            except Exception:
                pass
            continue
        for s in subs:
            if s.startswith("Face"):
                picked.append((obj, s))
    return picked


def _find_face_subname(obj, sub_shape):
    """Return the subelement name of *sub_shape* on *obj*, or None."""
    if sub_shape is None:
        return None
    try:
        nfaces = len(obj.Shape.Faces)
    except Exception:
        return None
    for i in range(1, nfaces + 1):
        try:
            f = obj.getSubObject("Face%d" % i)
        except Exception:
            continue
        if f is None or f.ShapeType != "Face":
            continue
        if f.isSame(sub_shape) or f.isEqual(sub_shape):
            return "Face%d" % i
    return None


def _find_owning_feature(body, obj, sub):
    """Return the body feature whose shape contains the requested sub-face."""
    try:
        sub_shape = obj.getSubObject(sub)
    except Exception:
        return None
    for feat in reversed(list(getattr(body, "Group", []) or [])):
        try:
            shp = feat.Shape
        except Exception:
            continue
        if shp is None or shp.isNull() or not shp.Faces:
            continue
        name = _find_face_subname(feat, sub_shape)
        if name is not None:
            return feat, name
    return None, None


def _ref_for(obj, sub, target_body):
    """Resolve a good reference object for a face selection.

    Referencing the PartDesign body from inside one of its own features would
    create a dependency cycle, so when the face belongs to the target body we
    re-target it to the feature that actually owns it.
    """
    if obj is None:
        return None, None
    if target_body is not None and obj is target_body:
        owner, oname = _find_owning_feature(target_body, obj, sub)
        if owner is not None and oname is not None:
            return owner, oname
    return obj, sub


def _default_lengths(face_a, face_b, kind):
    """Pleasant defaults for L1/L2 based on the actual faces."""
    d1 = 20.0
    d2 = 20.0
    try:
        if kind == "corner":
            d1 = max(_planar_principal_span(face_a), 1.0)
            d2 = max(_planar_principal_span(face_b), 1.0)
            d1 = min(d1, 30.0)
            d2 = min(d2, 30.0)
        else:
            if _is_plane_face(face_a):
                flat, cyl = face_a, face_b
            else:
                flat, cyl = face_b, face_a
            info = _cylinder_info(cyl)
            if info is not None:
                ap, ad, radius = info
                n = _plane_normal(flat)
                if n.dot(ad) < 0:
                    ad = -ad
                d1 = _cylinder_free_height(cyl, flat, ad)
                d2 = max(
                    (_cut_proj(flat.CenterOfGravity, ap, ad).Length - radius), 5.0)
    except Exception:
        pass
    return d1, d2


def _planar_principal_span(face):
    n = _plane_normal(face)
    w = _planar_principal_dir(face, n)
    verts = [v.Point for v in face.Vertexes]
    if len(verts) < 2:
        return 20.0
    proj = [p.dot(w) for p in verts]
    return max(proj) - min(proj)


def _cyl_axis_oriented(cyl, flat, ad):
    """(ad, z0, zmin, zmax) with *ad* pointing toward the longer free end.

    Values are measured from the cylinder axis point along *ad*; the returned
    ``z0`` is the flat face level, ``zmax``/``zmin`` the cylinder ends.
    """
    try:
        ap, _, _ = _cylinder_info(cyl)
    except Exception:
        ap = FreeCAD.Vector(0, 0, 0)
    if ad is None:
        ad = FreeCAD.Vector(0, 0, 1)
    bb = cyl.BoundBox
    vals = []
    for x in (bb.XMin, bb.XMax):
        for y in (bb.YMin, bb.YMax):
            for z in (bb.ZMin, bb.ZMax):
                vals.append((FreeCAD.Vector(x, y, z) - ap).dot(ad))
    if not vals:
        return ad, 0.0, 20.0, 0.0
    z0 = (flat.CenterOfGravity - ap).dot(ad)
    zmin, zmax = min(vals), max(vals)
    if zmax - z0 < z0 - zmin:
        ad = -ad
        vals = [-v for v in vals]
        z0 = -z0
        zmin, zmax = min(vals), max(vals)
    return ad, z0, zmin, zmax


def _cylinder_free_height(cyl, flat, ad):
    try:
        ad, z0, _zmin, zmax = _cyl_axis_oriented(cyl, flat, ad)
        return max(zmax - z0, 1.0)
    except Exception:
        return 20.0


# =============================================================================
# Whole-face lengths and helper sketch
# =============================================================================

def _extent_along(face, direction):
    """Extent of a face's vertices along a unit *direction*."""
    verts = [v.Point for v in face.Vertexes]
    if len(verts) < 2:
        return 20.0
    proj = [p.dot(direction) for p in verts]
    return max(max(proj) - min(proj), 1.0)


def _corner_reach(face, r0, w):
    """Max distance from the corner line into a face, along the unit *w*."""
    reach = 0.0
    for v in face.Vertexes:
        reach = max(reach, (v.Point - r0).dot(w))
    return max(reach, 1.0)


def _full_lengths(face_a, face_b, kind):
    """(L1, L2) that make the rib cover the whole of each face."""
    if kind == "corner":
        r0, _i, w_a, w_b, _n_a, _n_b = _corner_axes(face_a, face_b)
        return _corner_reach(face_a, r0, w_a), _corner_reach(face_b, r0, w_b)
    if kind == "cylinder":
        if _is_plane_face(face_a):
            flat, cyl = face_a, face_b
        else:
            flat, cyl = face_b, face_a
        info = _cylinder_info(cyl)
        if info is None:
            return 15.0, 5.0
        ap, ad, _radius = info
        l1 = _cylinder_free_height(cyl, flat, ad)
        l2 = 5.0
        return l1, l2
    return 20.0, 20.0


def _sketch_frame(kind, f1, f2, l1, l2, offset, copies, flip_a=False,
                  flip_b=False, angle=0.0, shape="rectangle", thickness=1.0,
                  penetration=None):
    """Helper-sketch placement and profile for a rib.

    Returns (origin, uvec, vvec, normal, polygon) where the polygon is a list
    of world-space vertices (closed) and uvec/vvec are orthonormal in-plane
    axes, or None when the profile cannot be computed.
    """
    try:
        if kind == "corner":
            r0, _i, w_a, w_b, _n_a, _n_b = _corner_axes(f1, f2, offset)
            if flip_a:
                w_a = FreeCAD.Vector(-w_a.x, -w_a.y, -w_a.z)
            if flip_b:
                w_b = FreeCAD.Vector(-w_b.x, -w_b.y, -w_b.z)
            v0 = r0
            v1 = FreeCAD.Vector(r0.x + w_a.x * float(l1),
                                r0.y + w_a.y * float(l1),
                                r0.z + w_a.z * float(l1))
            v2 = FreeCAD.Vector(r0.x + w_b.x * float(l2),
                                r0.y + w_b.y * float(l2),
                                r0.z + w_b.z * float(l2))
            m = (v1 - v0).cross(v2 - v0)
            if m.Length <= _EPS:
                return None
            m.normalize()
            u = v1 - v0
            if u.Length <= _EPS:
                return None
            u.normalize()
            v = m.cross(u)
            if _is_triangle_shape(shape):
                return v0, u, v, m, [v0, v1, v2]
            v3 = FreeCAD.Vector(
                r0.x + w_a.x * float(l1) + w_b.x * float(l2),
                r0.y + w_a.y * float(l1) + w_b.y * float(l2),
                r0.z + w_a.z * float(l1) + w_b.z * float(l2))
            return v0, u, v, m, [v0, v1, v3, v2]
        if kind == "cylinder":
            if _is_plane_face(f1):
                flat, cyl = f1, f2
            else:
                flat, cyl = f2, f1
            info = _cylinder_info(cyl)
            if info is None:
                return None
            ap, ad_raw, radius = info
            ad, z0, _zmin, _zmax = _cyl_axis_oriented(cyl, flat, ad_raw)
            center = flat.CenterOfGravity - ap
            radial = center - ad * (center.dot(ad))
            if radial.Length <= _EPS:
                return None
            rd = radial.normalize()
            ang = float(angle or 0.0)
            if ang != 0.0:
                rd = FreeCAD.Rotation(ad, ang).multVec(rd)
            z_top = z0 + float(l1)
            r_out = radius + float(l2)
            if penetration is None:
                half_t = float(thickness) / 2.0
                r_in = math.sqrt(max(radius * radius - half_t * half_t, 0.0))
            else:
                r_in = max(radius - max(0.0, float(penetration)), 0.0)
            c1 = ap + ad * z0 + rd * r_in
            c2 = ap + ad * z_top + rd * r_in
            c3 = ap + ad * z0 + rd * r_out
            if isinstance(shape, str) and shape.lower() in (
                    "triangle", "trapezoid", "triangolo", "t"):
                origin = (c1 + c3) / 2.0
                normal = ad.cross(rd)
                return origin, ad, rd, normal, [c1, c2, c3]
            c4 = ap + ad * z_top + rd * r_out
            origin = (c1 + c3) / 2.0
            normal = ad.cross(rd)
            return origin, ad, rd, normal, [c1, c2, c3, c4]
    except Exception:
        return None
    return None


def _make_rib_sketch(doc, body, name, origin, uvec, vvec, normal, polygon):
    """Create a helper Sketcher sketch showing the rib profile."""
    try:
        sketch = doc.addObject("Sketcher::SketchObject", name)
    except Exception:
        return None
    if body is not None:
        try:
            body.addObject(sketch)
        except Exception:
            pass
    m = FreeCAD.Matrix()
    m.A11 = uvec.x
    m.A12 = vvec.x
    m.A13 = normal.x
    m.A14 = origin.x
    m.A21 = uvec.y
    m.A22 = vvec.y
    m.A23 = normal.y
    m.A24 = origin.y
    m.A31 = uvec.z
    m.A32 = vvec.z
    m.A33 = normal.z
    m.A34 = origin.z
    sketch.Placement = FreeCAD.Placement(m)
    pts = [
        FreeCAD.Vector((p - origin).dot(uvec), (p - origin).dot(vvec), 0.0)
        for p in polygon
    ]
    for i in range(len(pts)):
        a = pts[i]
        b = pts[(i + 1) % len(pts)]
        try:
            sketch.addGeometry(Part.LineSegment(a, b), False)
        except Exception:
            break
    return sketch


# =============================================================================
# Public command
# =============================================================================

def _active_body(doc):
    """Return the active PartDesign body, tolerating missing GUI APIs."""
    import FreeCADGui as Gui
    try:
        body = Gui.activeBody()
        if body is not None:
            return body
    except AttributeError:
        pass
    try:
        for so in Gui.Selection.getSelectionEx():
            o = so.Object
            while o is not None:
                if o.TypeId == "PartDesign::Body":
                    return o
                o = getattr(o, "getParentGeoFeatureGroup", lambda: None)()
    except Exception:
        pass
    bodies = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]
    if len(bodies) == 1:
        return bodies[0]
    return None


def create_face_rib():
    """Create a rib between two selected faces.

    The user selects two faces (two angled planar walls forming a corner,
    or a planar face plus a cylinder) and a small
    task panel lets them adjust length1, length2, thickness, offset and (for
    cylinders) the number of copies before committing.
    """
    import FreeCADGui as Gui

    doc = FreeCAD.ActiveDocument
    if doc is None:
        FreeCAD.Console.PrintError(_tr("No active document") + "\n")
        return

    picked = _collect_face_selection()
    if len(picked) != 2:
        FreeCAD.Console.PrintError(_tr("Select exactly two faces.") + "\n")
        return

    (obj1, sub1), (obj2, sub2) = picked
    face1 = obj1.getSubObject(sub1)
    face2 = obj2.getSubObject(sub2)
    if face1 is None or face2 is None or not face1.Faces and face1.ShapeType != "Face" \
            or not face2.Faces and face2.ShapeType != "Face":
        FreeCAD.Console.PrintError(_tr("Select exactly two faces.") + "\n")
        return
    if face1.ShapeType == "Face":
        f1 = face1
    else:
        f1 = face1.Faces[0]
    if face2.ShapeType == "Face":
        f2 = face2
    else:
        f2 = face2.Faces[0]

    try:
        kind = classify_faces(f1, f2)
    except Exception:
        kind = None
    if kind is None:
        FreeCAD.Console.PrintError(_tr(
            "The faces are not usable: select two angled planar faces, or a "
            "planar face and a cylinder.") + "\n")
        return

    d1, d2 = _default_lengths(f1, f2, kind)
    fl1, fl2 = _full_lengths(f1, f2, kind)

    body = _active_body(doc)
    if body is None:
        try:
            from .rib_core import _parent_body
            body = _parent_body(obj1, doc)
        except Exception:
            body = None
    if body is None:
        bodies = [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]
        if len(bodies) == 1:
            body = bodies[0]

    from .FaceRibDialog import FaceRibPanel

    def _shape_of(l1, l2, thick, offset, copies, rev1, rev2, mode="tool",
                  angle=0.0, shape="rectangle", spacing=10.0):
        try:
            raw = build_face_rib(f1, f2, l1, l2, thick, offset, copies, rev1,
                                 rev2, angle, shape, spacing)[0]
            if mode != "tool" and body is not None:
                tip = getattr(body, "Tip", None)
                if tip is not None and tip.Shape is not None and not tip.Shape.isNull():
                    raw = tip.Shape.fuse(raw)
            return _refine(raw)
        except Exception:
            return None

    hidden_tip = {"obj": None, "was": True}

    def _hide_body_for_preview():
        if body is None:
            return
        tip = getattr(body, "Tip", None)
        if tip is None:
            return
        if hidden_tip["obj"] is not None:
            return
        hidden_tip["obj"] = str(tip.Name)
        try:
            hidden_tip["was"] = bool(tip.ViewObject.Visibility)
        except Exception:
            hidden_tip["was"] = True
        try:
            tip.ViewObject.Visibility = False
        except Exception:
            pass

    def _restore_body_visibility(restore=True):
        if hidden_tip["obj"] is None:
            return
        tip = doc.getObject(hidden_tip["obj"])
        hidden_tip["obj"] = None
        if tip is None or not restore:
            return
        try:
            tip.ViewObject.Visibility = hidden_tip["was"]
        except Exception:
            pass

    def _remove_preview(restore=True):
        pv = doc.getObject("FaceRibPreview")
        if pv is not None:
            try:
                doc.removeObject(pv.Name)
            except Exception:
                pass
        _restore_body_visibility(restore)

    def _on_change(l1, l2, thick, offset, copies, rev1, rev2, mode="tool",
                   angle=0.0, shape="rectangle", spacing=10.0):
        shp = _shape_of(l1, l2, thick, offset, copies, rev1, rev2, mode,
                        angle, shape, spacing)
        pv = doc.getObject("FaceRibPreview")
        if shp is None:
            _remove_preview()
            return
        if pv is None:
            pv = doc.addObject("Part::Feature", "FaceRibPreview")
            try:
                from .rib_core import _set_view_object_ok
                _set_view_object_ok(pv)
            except Exception:
                pass
            try:
                pv.ViewObject.Selectable = False
            except Exception:
                pass
        if mode == "result":
            _hide_body_for_preview()
        else:
            _restore_body_visibility()
        try:
            if mode == "result":
                pv.ViewObject.ShapeColor = (0.7, 0.7, 0.7, 1.0)
                pv.ViewObject.Transparency = 0
            else:
                pv.ViewObject.ShapeColor = (0.0, 0.70, 0.0, 1.0)
                pv.ViewObject.Transparency = 40
        except Exception:
            pass
        pv.Shape = shp
        pv.Visibility = True
        try:
            doc.recompute()
        except Exception:
            pass

    def _on_finish(l1, l2, thick, offset, copies, rev1, rev2, mode="tool",
                   angle=0.0, shape="rectangle", spacing=10.0):
        newfeat = None
        try:
            build_face_rib(f1, f2, l1, l2, thick, offset, copies, rev1, rev2,
                           angle, shape, spacing)
        except Exception as e:
            FreeCAD.Console.PrintError(_tr("Rib between faces: {}").format(e) + "\n")
            return
        sketch = None
        frame = _sketch_frame(kind, f1, f2, l1, l2, offset, copies, rev1,
                              rev2, angle, shape, thick)
        if frame is not None:
            sketch = _make_rib_sketch(doc, body, "FaceRibSketch", *frame)
            if sketch is not None:
                try:
                    sketch.ViewObject.Visibility = False
                except Exception:
                    pass
        try:
            if body is not None:
                feat = doc.addObject(
                    "PartDesign::FeatureAdditivePython", "FaceRib")
                AdditiveFaceRibFeature(feat)
            else:
                feat = doc.addObject("Part::FeaturePython", "FaceRib")
                FaceRibFeature(feat)
            ref1 = _ref_for(obj1, sub1, body)
            ref2 = _ref_for(obj2, sub2, body)
            feat.F1Ref = ref1
            feat.F2Ref = ref2
            feat.Thickness = thick
            feat.Length1 = l1
            feat.Length2 = l2
            feat.Offset = offset
            feat.Copies = int(copies)
            feat.Reversed1 = bool(rev1)
            feat.Reversed2 = bool(rev2)
            feat.Reversed = bool(rev1) and bool(rev2)
            if kind == "cylinder":
                feat.Angle = float(angle)
            if kind in ("corner", "cylinder"):
                feat.ProfileType = shape
            if kind == "corner":
                feat.Spacing = float(spacing)
            if sketch is not None:
                try:
                    feat.Sketch = sketch
                except Exception:
                    pass
            if body is not None:
                body.addObject(feat)
            try:
                from .rib_core import _set_view_object_ok
                _set_view_object_ok(feat)
            except Exception:
                pass
            doc.recompute()
            if body is not None:
                try:
                    body.Tip = feat
                except Exception:
                    pass
                doc.recompute()
                FreeCAD.Console.PrintMessage(_tr(
                    "Additive rib between faces added to '{}'.").format(
                    body.Label) + "\n")
            else:
                doc.recompute()
                FreeCAD.Console.PrintMessage(
                    _tr("Rib between faces created.") + "\n")
            newfeat = feat
        finally:
            _remove_preview(restore=False)
            try:
                Gui.Selection.clearSelection()
                if newfeat is not None and newfeat.ViewObject is not None:
                    newfeat.ViewObject.Visibility = True
            except Exception:
                pass

    def _on_cancel():
        _remove_preview()

    try:
        if Gui.Control.activeDialog():
            Gui.Control.closeDialog()
    except Exception:
        pass
    Gui.Control.showDialog(FaceRibPanel(
        kind, d1, d2, fl1, fl2, _on_change, _on_finish, _on_cancel))
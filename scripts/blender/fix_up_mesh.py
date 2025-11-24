import bpy
import bmesh
import os
import sys
from mathutils import Vector
from mathutils.kdtree import KDTree

# Threshold for "near edge" and merge distance
THRESHOLD = 0.005

# -------------------------------
# Helper function: process a single mesh object
# -------------------------------
def process_object(obj, phase):
    if obj.type != 'MESH':
        return 0

    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    verts_before = len(bm.verts)

    # Merge doubles early (fast)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=THRESHOLD)

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    if not bm.verts or not bm.edges:
        bm.to_mesh(me); bm.free()
        return 0

    # ---- Build compact edge center table ----
    edges = bm.edges
    edge_count = len(edges)

    kd = KDTree(edge_count)
    edge_centers = [None] * edge_count
    edge_data = [None] * edge_count

    max_half = 0.0
    for i, e in enumerate(edges):
        v1 = e.verts[0].co
        v2 = e.verts[1].co
        center = (v1 + v2) * 0.5
        edge_centers[i] = center
        edge_data[i] = (e, v1, v2)
        kd.insert(center, i)
        half = (v2 - v1).length_squared ** 0.5 * 0.5
        if half > max_half:
            max_half = half

    kd.balance()
    search_radius = THRESHOLD + max_half

    # ---- Closest point utility (inlined for speed) ----
    def closest_point_and_t(pt, a, b):
        ab = b - a
        ab_len_sq = ab.length_squared
        if ab_len_sq == 0:
            return a, 0.0
        t = (pt - a).dot(ab) / ab_len_sq
        if t < 0.0: t = 0.0
        elif t > 1.0: t = 1.0
        return a + ab * t, t

    # ---- Collect splits ----
    pending = {}

    for v in bm.verts:
        A = v.co
        hits = kd.find_range(A, search_radius)
        for _, idx, _ in hits:
            e, v1, v2 = edge_data[idx]
            if v in e.verts:
                continue
            B, t = closest_point_and_t(A, v1, v2)
            if (A - B).length_squared < THRESHOLD * THRESHOLD:
                pending.setdefault(e, []).append(t)

    # ---- Apply edge splits ----
    for e, t_list in pending.items():
        for t in sorted(set(t_list)):
            bmesh.utils.edge_split(e, e.verts[0], t)

    # Final merge + final triangulate
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=THRESHOLD)
    bmesh.ops.triangulate(bm, faces=bm.faces)

    for f in bm.faces:
        f.smooth = False

    bm.to_mesh(me)
    bm.free()

    verts_after = len(me.vertices)
    created = verts_after - verts_before
    print(f"Processed {obj.name}, phase {phase}: {created} verts")
    return created

# -------------------------------
# MAIN: process all mesh objects in the scene
# -------------------------------
def process_objects():
    total_created = 0
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            for i in range(3):
                created = process_object(obj, i)
                total_created += created
                if created == 0:
                    break
    print(f"Total vertices created across scene: {total_created}")


def stage_fix_up_mesh(num, folder):
    process_objects()
    bpy.ops.wm.save_mainfile(filepath=os.path.join(folder, f"{num}-fix-up-mesh.blend"))

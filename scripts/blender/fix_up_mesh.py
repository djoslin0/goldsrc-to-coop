import bpy
import bmesh
import os
import sys
from mathutils import Vector
from mathutils.kdtree import KDTree

# Threshold for "near edge" and merge distance
THRESHOLD = 0.005

# Helper function to check if two sets of vertex positions match within threshold
def verts_match(verts_a, verts_b, threshold):
    for p in verts_a:
        found = False
        for q in verts_b:
            if (Vector(p) - Vector(q)).length_squared < threshold * threshold:
                found = True
                break
        if not found:
            return False
    return True


# Helper function to choose outward-facing face for backfaces
def backface_choose_outward(face_a, face_b, obj_center):
    """
    Determines which of two backface pairs is pointing outward based on object center.

    Args:
        face_a (bmesh.types.BMFace): First face.
        face_b (bmesh.types.BMFace): Second face.
        obj_center (Vector): Object center position.

    Returns:
        bool: True if face_a is more outward, False if face_b is more outward.
    """
    # Compute center of face_a
    face_a_center = sum((v.co for v in face_a.verts), Vector()) / len(face_a.verts)
    dir_a = (face_a_center - obj_center).normalized()
    dot_a = face_a.normal.dot(dir_a)

    face_b_center = sum((v.co for v in face_b.verts), Vector()) / len(face_b.verts)
    dir_b = (face_b_center - obj_center).normalized()
    dot_b = face_b.normal.dot(dir_b)

    return dot_a > dot_b  # Choose face_a if it's more outward

def backface_choose_up(face_a, face_b, choose_data):
    if abs(face_a.normal.y - face_b.normal.y) > THRESHOLD:
        return face_a.normal.y > face_b.normal.y

    if abs(face_a.normal.x - face_b.normal.x) > THRESHOLD:
        return face_a.normal.x > face_b.normal.x

    return face_a.normal.z > face_b.normal.z


def find_backfaces(obj, choose_func, choose_data):
    """
    Identifies pairs of faces that are backfaces: same number of vertices,
    identical vertex positions (unordered), but opposite normals.

    Args:
        obj (bpy.types.Object): The Blender mesh object to analyze.

    Returns:
        list of tuples: Each tuple contains the indices (int, int) of a backface pair in the object's mesh data.
    """
    if obj.type != 'MESH':
        return []

    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)

    backface_pairs = []
    faces = list(bm.faces)

    for i, face_a in enumerate(faces):
        verts_a_set = set(tuple(v.co) for v in face_a.verts)
        for j in range(i + 1, len(faces)):
            face_b = faces[j]
            if len(face_a.verts) != len(face_b.verts):
                continue
            verts_b_set = set(tuple(v.co) for v in face_b.verts)
            if verts_match(verts_a_set, verts_b_set, THRESHOLD) and verts_match(verts_b_set, verts_a_set, THRESHOLD) and (face_a.normal + face_b.normal).length < THRESHOLD:
                # Prefer the face with normal pointing more upwards (higher Z-component) as first index
                if choose_func(face_a, face_b, choose_data):
                    backface_pairs.append((i, j))
                else:
                    backface_pairs.append((j, i))

    bm.free()
    return backface_pairs

# -------------------------------
# Function to split backface pairs into two new objects
# -------------------------------
def split_backfaces(obj):
    """
    Takes an object and splits identified backface pairs into two new objects.
    Obj A contains all faces from the first index of each pair.
    Obj B contains all faces from the second index of each pair.

    Args:
        obj (bpy.types.Object): The Blender mesh object to process.

    Returns:
        tuple: (obj_A, obj_B) where obj_A and obj_B are the new objects, or (None, None) if no backfaces found.
    """
    pairs = find_backfaces(obj, backface_choose_up, None)
    if not pairs:
        return None, None

    # Collect unique face indices for each group
    faces_a = set()
    faces_b = set()
    for idx_a, idx_b in pairs:
        faces_a.add(idx_a)
        faces_b.add(idx_b)

    if not faces_a or not faces_b:
        return None, None

    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)

    # Process Obj A
    bm_a = bm.copy()
    bm_a.verts.ensure_lookup_table()
    bm_a.edges.ensure_lookup_table()
    bm_a.faces.ensure_lookup_table()
    # Deselect all, then select A faces
    for f in bm_a.faces:
        f.select_set(False)
    for idx in faces_a:
        bm_a.faces[idx].select_set(True)
    # Delete deselected
    deselected_a = [f for f in bm_a.faces if not f.select]
    bmesh.ops.delete(bm_a, geom=deselected_a, context='FACES')

    temp_me_a = bpy.data.meshes.new(obj.name + "_backfaces_A")
    bm_a.to_mesh(temp_me_a)
    for mat in obj.data.materials:  # Copy materials from original
        temp_me_a.materials.append(mat)
    temp_obj_a = bpy.data.objects.new(obj.name + "_backfaces_A", temp_me_a)
    temp_obj_a.matrix_world = obj.matrix_world  # Copy transform
    temp_obj_a.parent = obj.parent  # Copy parent
    bpy.context.collection.objects.link(temp_obj_a)

    # Process Obj B
    bm_b = bm.copy()
    bm_b.verts.ensure_lookup_table()
    bm_b.edges.ensure_lookup_table()
    bm_b.faces.ensure_lookup_table()
    # Select B faces
    for f in bm_b.faces:
        f.select_set(False)
    for idx in faces_b:
        bm_b.faces[idx].select_set(True)
    # Delete deselected
    deselected_b = [f for f in bm_b.faces if not f.select]
    bmesh.ops.delete(bm_b, geom=deselected_b, context='FACES')

    temp_me_b = bpy.data.meshes.new(obj.name + "_backfaces_B")
    bm_b.to_mesh(temp_me_b)
    for mat in obj.data.materials:  # Copy materials from original
        temp_me_b.materials.append(mat)
    temp_obj_b = bpy.data.objects.new(obj.name + "_backfaces_B", temp_me_b)
    temp_obj_b.matrix_world = obj.matrix_world  # Copy transform
    temp_obj_b.parent = obj.parent  # Copy parent
    bpy.context.collection.objects.link(temp_obj_b)

    # Clean up
    bm.free()
    bm_a.free()
    bm_b.free()

    return temp_obj_a, temp_obj_b

# -------------------------------
# Function to split faces with liquid materials ("!water", "!slime", "!lava")
# -------------------------------
def split_liquid_faces(obj):
    """
    Selects all faces in obj that have materials starting with '!water', '!slime', or '!lava'.
    Separates them into a new object (only upward facing, facing down are deleted).
    Removes those faces from the original obj.
    The new object uses the same transform, materials, parent as the original.

    Args:
        obj (bpy.types.Object): The Blender mesh object to process.

    Returns:
        bpy.types.Object or None: The new object containing the upward-facing liquid faces, or None if no liquid faces.
    """
    if obj.type != 'MESH':
        return None

    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    liquid_indices = set()

    for face in bm.faces:
        mat_index = face.material_index
        if mat_index < len(me.materials):
            mat_name = me.materials[mat_index].name
            if mat_name.startswith('!water') or mat_name.startswith('!slime') or mat_name.startswith('!lava'):
                liquid_indices.add(face.index)

    if not liquid_indices:
        bm.free()
        return None

    # Process Obj Liquid (A)
    bm_liquid = bm.copy()
    bm_liquid.verts.ensure_lookup_table()
    bm_liquid.edges.ensure_lookup_table()
    bm_liquid.faces.ensure_lookup_table()
    # Deselect all, then select liquid faces
    for f in bm_liquid.faces:
        f.select_set(False)
    for idx in liquid_indices:
        bm_liquid.faces[idx].select_set(True)
    # Delete deselected (keep only liquid)
    deselected_liquid = [f for f in bm_liquid.faces if not f.select]
    bmesh.ops.delete(bm_liquid, geom=deselected_liquid, context='FACES')

    temp_me_liquid = bpy.data.meshes.new(obj.name + "_liquid")
    bm_liquid.to_mesh(temp_me_liquid)
    for mat in me.materials:
        temp_me_liquid.materials.append(mat)
    temp_obj_liquid = bpy.data.objects.new(obj.name + "_liquid", temp_me_liquid)
    temp_obj_liquid.matrix_world = obj.matrix_world
    temp_obj_liquid.parent = obj.parent
    bpy.context.collection.objects.link(temp_obj_liquid)

    # Process Obj Remaining (B)
    bm_remaining = bm.copy()
    bm_remaining.verts.ensure_lookup_table()
    bm_remaining.edges.ensure_lookup_table()
    bm_remaining.faces.ensure_lookup_table()
    # Select liquid faces to delete them
    for f in bm_remaining.faces:
        f.select_set(False)
    for idx in liquid_indices:
        bm_remaining.faces[idx].select_set(True)
    # Delete selected (liquid), keep remaining
    bmesh.ops.delete(bm_remaining, geom=[f for f in bm_remaining.faces if f.select], context='FACES')

    # Update original object with remaining faces (liquid faces removed)
    bm_remaining.to_mesh(obj.data)

    temp_obj_liquid.ignore_collision = True

    # Clean up
    bm.free()
    bm_liquid.free()
    bm_remaining.free()

    return temp_obj_liquid

# Helper function to determine if a face is pointing outward relative to object center
def is_face_outward(face, obj_center):
    """
    Checks if a face is pointing outward based on object center.

    Args:
        face (bmesh.types.BMFace): The face to check.
        obj_center (Vector): Object center position.

    Returns:
        bool: True if face is pointing outward, False otherwise.
    """
    # Compute center of face
    face_center = sum((v.co for v in face.verts), Vector()) / len(face.verts)
    # Direction from center to face
    dir_to_face = (face_center - obj_center).normalized()
    dot = face.normal.dot(dir_to_face)
    return dot > 0  # Outward if normal aligns with direction to face center

def remove_backfaces(obj):
    """
    Calls find_backfaces using backface_choose_outward and the object's center position,
    then removes the inward-pointing faces from paired backfaces.

    Args:
        obj (bpy.types.Object): The Blender mesh object to process.
    """
    if obj.type != 'MESH':
        return

    if not obj.name.startswith("M_"):
        return

    entity_index = int(obj.name.split('#', 1)[0].rsplit('_', 1)[-1])
    if entity_index <= 0:
        return

    # Compute object center: average of all vertices
    bm_temp = bmesh.new()
    bm_temp.from_mesh(obj.data)
    obj_center = sum((v.co for v in bm_temp.verts), Vector()) / len(bm_temp.verts)
    bm_temp.free()

    # Call find_backfaces with backface_choose_outward and obj_center
    pairs = find_backfaces(obj, backface_choose_outward, obj_center)
    if not pairs:
        return

    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    faces_to_delete = set()
    for keep_idx, remove_idx in pairs:
        faces_to_delete.add(remove_idx)  # remove_idx is the inward face

    # Delete the faces (collect face objects first to avoid index issues)
    face_objs_to_delete = [bm.faces[idx] for idx in faces_to_delete]
    for face in face_objs_to_delete:
        bm.faces.remove(face)

    # Remove loose edges and verts
    loose_edges = [e for e in bm.edges if len(e.link_faces) == 0]
    bmesh.ops.delete(bm, geom=loose_edges, context='EDGES')
    loose_verts = [v for v in bm.verts if len(v.link_edges) == 0]
    bmesh.ops.delete(bm, geom=loose_verts, context='VERTS')

    bm.to_mesh(obj.data)
    bm.free()

def delete_non_upward_faces(obj):
    """
    Deletes faces from the mesh where the face normal's Z component is less than 0.5.
    Then removes any edges that are not connected to any faces.
    Finally, removes any vertices that are not connected to any edges.

    Args:
        obj (bpy.types.Object): The Blender mesh object to process.
    """
    if not obj:
        return

    if obj.type != 'MESH':
        return

    bm = bmesh.new()
    bm.from_mesh(obj.data)

    faces_to_delete = []
    for face in bm.faces:
        if face.normal.y < 0.5:
            faces_to_delete.append(face)

    for face in faces_to_delete:
        bm.faces.remove(face)

    # Remove loose edges
    loose_edges = [e for e in bm.edges if len(e.link_faces) == 0]
    bmesh.ops.delete(bm, geom=loose_edges, context='EDGES')

    # Remove loose vertices
    loose_verts = [v for v in bm.verts if len(v.link_edges) == 0]
    bmesh.ops.delete(bm, geom=loose_verts, context='VERTS')

    bm.to_mesh(obj.data)
    bm.free()


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

def recalculate_outside(obj):
    if not obj.name.startswith("M_"):
        return

    entity_index = int(obj.name.split('#', 1)[0].rsplit('_', 1)[-1])
    if entity_index <= 0:
        return

    # Select and activate the object
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Enter edit mode, recalculate normals outside, then exit edit mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')

# -------------------------------
# MAIN: process all mesh objects in the scene
# -------------------------------
def process_objects():
    total_created = 0
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            remove_backfaces(obj)
            for i in range(3):
                created = process_object(obj, i)
                total_created += created
                if created == 0:
                    break
            recalculate_outside(obj)
    print(f"Total vertices created across scene: {total_created}")


def stage_fix_up_mesh(num, folder):
    # Check for specific object and split backfaces if it exists
    target_obj = bpy.data.objects.get("M_0_ENT_0#worldspawn")
    if target_obj:
        liquid = split_liquid_faces(target_obj)
        delete_non_upward_faces(liquid)
        split_backfaces(target_obj)

    process_objects()
    bpy.ops.wm.save_mainfile(filepath=os.path.join(folder, f"{num}-fix-up-mesh.blend"))

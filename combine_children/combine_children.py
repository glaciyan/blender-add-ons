bl_info = {
    "name": "Combine Children",
    "description": "Combine an object with its children.",
    "author": "slimetsp",
    "version": (1, 0, 0),
    "blender": (2, 83, 0),
    "warning": "",
    "tracker_url": "https://github.com/slimetsp/blender-add-ons/issues",
    "category": "Object",
}

import bpy

def select_all_children(scene_object, object_type):
    """
    This function selects all of an objects children.

    :param object scene_object: A object.
    :param str object_type: The type of object to select.
    """
    for child_object in scene_object.children:
        if child_object.type == object_type:
            child_object.select_set(True)
            if child_object.children:
                select_all_children(child_object, object_type)

def apply_all_mesh_modifiers(scene_object):
    """
    This function applies all mesh modifiers on the given object.

    :param object scene_object: A object.
    """
    deselect_all_objects()

    # select the provided object
    bpy.context.view_layer.objects.active = scene_object
    scene_object.select_set(True)

    # apply all modifiers except the armature modifier
    for modifier in scene_object.modifiers:
        if modifier.type != 'ARMATURE':
            bpy.ops.object.modifier_apply(modifier=modifier.name)

    deselect_all_objects()


def deselect_all_objects():
    """
    This function deselects all object in the scene.
    """
    for scene_object in bpy.data.objects:
        scene_object.select_set(False)

def combine_child_meshes():
    """
    This function combines all an objects child meshes and all of its children.

    :param object properties: The property group that contains variables that maintain the addon's correct state.
    """
    selected_object_names = [selected_object.name for selected_object in bpy.context.selected_objects]
    selected_objects = bpy.context.selected_objects.copy()

    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # select all children
    for selected_object in selected_objects:
        select_all_children(selected_object, object_type='MESH')

    # duplicate the selection
    bpy.ops.object.duplicate()

    duplicate_object_names = [selected_object.name for selected_object in bpy.context.selected_objects]
    duplicate_objects = bpy.context.selected_objects.copy()

    # apply all modifiers on the duplicates
    for duplicate_object in duplicate_objects:
        apply_all_mesh_modifiers(duplicate_object)

    deselect_all_objects()

    # select all the duplicate objects that are meshes
    mesh_count = 0
    for duplicate_object in duplicate_objects:
        if duplicate_object.type == 'MESH':
            bpy.context.view_layer.objects.active = duplicate_object
            duplicate_object.select_set(True)
            mesh_count += 1

    # join all the selected mesh objects
    if mesh_count > 1:
        bpy.ops.object.join()

    # now select all the duplicate objects by their name
    for duplicate_object_name in duplicate_object_names:
        duplicate_object = bpy.data.objects.get(duplicate_object_name)
        if duplicate_object:
            duplicate_object.select_set(True)


class CombineChildren(bpy.types.Operator):
    bl_idname = "object.combine_children"
    bl_label = "Combine child meshes"

    def execute(self, context):
        combine_child_meshes()
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(CombineChildren)

def unregister():
    bpy.utils.unregister_class(CombineChildren)

if __name__ == "__main__":
    register()
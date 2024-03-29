# Bugs:
#   - Can't handle multiple objects having the same material

bl_info = {
    "name": "Material ID Helper",
    "description": "Quickly create material ids",
    "author": "slimetsp",
    "version": (1, 0, 0),
    "blender": (2, 83, 0),
    "location": "N Panel -> Material ID",
    "warning": "",
    "tracker_url": "https://github.com/slimetsp/blender-add-ons/issues",
    "category": "Material",
}

import colorsys
import bpy
from bpy.props import (PointerProperty, BoolProperty, FloatVectorProperty,
                       IntProperty, StringProperty, EnumProperty)


class Options(bpy.types.PropertyGroup):
    image: PointerProperty(type=bpy.types.Image,
                           name="Image Texture",
                           description="Image used when creating MID material"
                                       " with an image texture")

        
# Panels


class MID_PT_MAINPANEL(bpy.types.Panel):
    bl_idname = "MID_PT_MAINPANEL"
    bl_label = "Material ID Helper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Material ID"

    def draw(self, context):
        self.layout.operator("slmid.generate_material_id", text="Material ID", icon="MATERIAL")


class MID_PT_ImagePanel(bpy.types.Panel):
    bl_label = "Texture Image (CTRL)"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = "MID_PT_MAINPANEL"

    def draw(self, context):
        layout.template_ID


# End of Panels


class DupeObjectSetSingleUserMaterials(bpy.types.Operator):
    bl_idname = "slmid.dupe_single_user_material"
    bl_label = "Dupe object and materials"

    suffix: StringProperty(name="suffix", default="MID")

    def execute(self, context):
        return {'FINISHED'}

def KeepIn(n, max):
    if n == max:
        return n
    elif n > max:
        return n % max
    else:
        return n

def ColorSequence(iteration):
    h = 0.0
    s = 1.0
    v = 1.0

    h += 0.08333 * (iteration)
    if round(h) % 2 == 0:
        s = s - (h / 1) * 0.02
    else:
        v = v - (h / 1) * 0.05


    h = KeepIn(h, 1.0)
    s = KeepIn(s, 1.0)
    v = KeepIn(v, 1.0)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


def UnlinkFromAllCollections(object):
    for collection in object.users_collection:
        collection.objects.unlink(object)


class GenerateMaterialID(bpy.types.Operator):
    bl_idname = "slmid.generate_material_id"
    bl_label = "Generate Material ID"
    bl_description = """ Generates materials for a material ID map on a duplicate of the active object.
        LFT = Normal Operation
    + SHIFT = Don't make duplicate of object
    + CTRL = Create Texture Nodes from Texture Image"""
    bl_options = {'REGISTER', 'UNDO'}

    mode: EnumProperty(
        items=(('NOIMAGE', "Without Texture Nodes", ""), ('IMAGE', "With Texture Nodes", "")),
        name="Mode",
        default='NOIMAGE'
    )

    createDupe: BoolProperty(name="Create Duplicate", default=True)

    @classmethod
    def poll(cls, context):
        isEverythingMesh = True
        for obj in context.selected_objects:
            isEverythingMesh = getattr(obj, 'type', '') in ['MESH']
            if not isEverythingMesh:
                break

        return len(context.selected_objects) != 0 and isEverythingMesh

    def execute(self, context):
        if self.mode == 'IMAGE':
            texture = context.scene.mid_options.image
            if texture is None:
                self.report({'ERROR'}, "No image selected")
                return {'CANCELLED'}

        if self.createDupe:
            bpy.ops.object.duplicate()

        if self.createDupe:
            collection = bpy.context.scene.collection.children.get("MID")
            if not collection:
                collection = bpy.data.collections.new("MID")
                bpy.context.scene.collection.children.link(collection)

        objIndex = 0
        iteration = 0
        for obj in context.selected_objects:
            if self.createDupe:
                UnlinkFromAllCollections(obj)
                collection.objects.link(obj)
            bpy.ops.object.make_single_user(object=True, obdata=True, material=True, animation=True)
            context.view_layer.objects.active = obj

            for ms in obj.material_slots:
                material = ms.material
                material.use_nodes = True
                material.name = "MaterialID.%d" % iteration

                nodes = material.node_tree.nodes
                nodes.clear()

                output = nodes.new("ShaderNodeOutputMaterial")
                bsdf = nodes.new("ShaderNodeBsdfPrincipled")
                # Base Color
                bsdf.inputs[0].default_value = ColorSequence(iteration)
                # Roughness
                bsdf.inputs[7].default_value = 1.0
                iteration += 1

                material.node_tree.links.new(output.inputs[0], bsdf.outputs[0])

                if self.mode == 'IMAGE':
                    textNode = nodes.new('ShaderNodeTexImage')
                    textNode.image = texture
                    nodes.active = textNode
            objIndex += 1

        return {'FINISHED'}

    def invoke(self, context, event):
        if event.ctrl:
            self.mode = 'IMAGE'
        else:
            self.mode = 'NOIMAGE'

        self.createDupe = not event.shift

        return self.execute(context)


classes = (
    Options,
    GenerateMaterialID,
    MID_PT_MAINPANEL,
    MID_PT_ImagePanel,
    MID_PT_ImagePanel.NewImage,
    MID_PT_ImagePanel.OpenImage,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.mid_options = PointerProperty(type=Options)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    del bpy.types.Scene.mid_options


if __name__ == "__main__":
    register()

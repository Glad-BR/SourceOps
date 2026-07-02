import bpy
from . import (
    autofill_materials,
    open_folder,
    export_meshes,
    generate_qc,
    compile_qc,
    view_model,
    export_auto,
    list_operator,
    export_vmf,
    rig_simulation,
    pose_bone_transforms,
    weighted_normal,
    triangulate,
    backup,
    export_materials,
)

classes = (
    autofill_materials.SOURCEOPS_OT_AutofillMaterials,
    open_folder.SOURCEOPS_OT_OpenFolder,
    open_folder.SOURCEOPS_OT_OpenMaterialFolder,
    export_meshes.SOURCEOPS_OT_ExportMeshes,
    generate_qc.SOURCEOPS_OT_GenerateQC,
    compile_qc.SOURCEOPS_OT_CompileQC,
    view_model.SOURCEOPS_OT_ViewModel,
    export_auto.SOURCEOPS_OT_ExportAuto,
    list_operator.SOURCEOPS_OT_ListOperator,
    export_vmf.SOURCEOPS_OT_ExportVMF,
    rig_simulation.SOURCEOPS_OT_RigSimulation,
    pose_bone_transforms.SOURCEOPS_OT_PoseBoneTransforms,
    weighted_normal.SOURCEOPS_OT_weighted_normal,
    triangulate.SOURCEOPS_OT_triangulate,
    backup.SOURCEOPS_OT_BackupPreferences,
    backup.SOURCEOPS_OT_RestorePreferences,
    export_materials.SOURCEOPS_OT_ExportMaterials,
)

class_register, class_unregister = bpy.utils.register_classes_factory(classes)

def register():
    class_register()

    bpy.types.VIEW3D_MT_pose_context_menu.append(pose_bone_transforms.menu_func)

def unregister():
    bpy.types.VIEW3D_MT_pose_context_menu.remove(pose_bone_transforms.menu_func)

    class_unregister()

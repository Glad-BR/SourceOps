import bpy

from ... utils import common
from .model import Model

def generate_qc(self:Model):
    if not self.reference and not self.stacking:
        return self.report(f'Unable to generate QC for: {self.name} (reference and stacking both not set)')

    if not self.armature and not self.static:
        self.static = True
        print(f'Armature not set for {self.name}, using static')

    self.ensure_modelsrc_folder()
    path = self.directory.joinpath(f'{self.stem}.qc')

    try:
        qc = path.open('w')
        print(f'Generating: {path}')
    except:
        return self.report(f'Failed to open: {path}', exception=True)

    qc.write(f'$modelname "{self.name}"')
    qc.write('\n')

    if not self.material_folder_items:
        qc.write('\n')
        qc.write('$cdmaterials "/"')
        qc.write('\n')

    for material_folder in self.material_folder_items:
        qc.write('\n')
        qc.write(f'$cdmaterials "{material_folder.name}"')
        qc.write('\n')

    qc.write('\n')
    qc.write(f'$surfaceprop "{self.surface}"')
    qc.write('\n')

    if self.glass:
        qc.write('\n')
        qc.write('$mostlyopaque')
        qc.write('\n')

    if self.static:
        qc.write('\n')
        qc.write('$staticprop')
        qc.write('\n')

    if self.origin_source == 'MANUAL':
        rotation = self.rotation-180
    else:
        rotation = -180

    origin = common.blender_to_source( common.rotate_z(common.get_origin(self), rotation) * self.scale )
    illumposition = (common.get_origin(self) - self.illumposition)

    # The origin command does not work with static prop combine.
    if not (self.static and self.static_prop_combine):
        qc.write('\n')
        qc.write(f'$origin {origin.x:.6f} {origin.y:.6f} {-origin.z:.6f} {rotation:.6f}')
        qc.write('\n')

    if self.illumposition:
        qc.write('\n')
        qc.write(f'$illumposition {illumposition.x:.6f} {illumposition.y:.6f} {-illumposition.z:.6f}')
        qc.write('\n')

    qc.write('\n')
    qc.write(f'$scale {self.scale:.4f}')
    qc.write('\n')

    if self.reference:
        qc.write('\n')
        name = common.clean_filename(self.reference.name)
        qc.write(f'$body "{name}" "{name}.{self.mesh_type}"')
        qc.write('\n')

    if self.bodygroups:
        for bodygroup in self.bodygroups:
            if bodygroup.sublist_items:

                qc.write('\n')
                bodygroup_name = common.clean_filename(bodygroup.name)
                qc.write(f'$bodygroup "{bodygroup_name}"' + ' {\n')
                for sublist in bodygroup.sublist_items:
                    if sublist.reference:
                        name = common.clean_filename(sublist.reference.name)
                        qc.write(f'    studio "{name}.{self.mesh_type}"\n')
                    else:
                        qc.write(f'    blank\n')
                qc.write('}')
                qc.write('\n')

    if self.lods_items:
        for lod in self.lods_items:
            if lod.replacemodel_items:
                qc.write('\n')
                qc.write(f'$lod {lod.distance}\n')
                qc.write('{\n')
                for replace in lod.replacemodel_items:
                    if replace.source:
                        source_name = common.clean_filename(replace.source.name)
                        if replace.target:
                            target_name = common.clean_filename(replace.target.name)
                            qc.write(f'    replacemodel "{source_name}.{self.mesh_type}" "{target_name}.{self.mesh_type}"\n')
                        else:
                            qc.write(f'    replacemodel "{source_name}.{self.mesh_type}" "blank.SMD"\n')
                qc.write('}\n')

    if not self.rename_material == '':
        qc.write('\n')
        qc.write(f'$renamematerial {self.rename_material}')
        qc.write('\n')

    if self.collision:
        qc.write('\n')
        name = common.clean_filename(self.collision.name)
        command = 'collisionjoints' if self.joints else 'collisionmodel'
        qc.write(f'${command} "{name}.{self.mesh_type}"' + ' {\n')
        command = 'concaveperjoint' if self.joints else 'concave'
        qc.write(f'    ${command}\n')
        command = f'mass {self.mass}' if self.mass > 0 else 'automass'
        qc.write(f'    ${command}\n')
        qc.write('    $maxconvexpieces 10000\n')
        qc.write('}')
        qc.write('\n')

    if self.stacking:
        for collection in self.stacking.children:
            qc.write('\n')
            name = common.clean_filename(collection.name)
            qc.write(f'$model "{name}" "{name}.{self.mesh_type}"')
            qc.write('\n')

    if not self.sequence_items:
        qc.write('\n')
        qc.write(f'$sequence "idle" "anims/idle.SMD"')
        qc.write('\n')

    for sequence in self.sequence_items:
        qc.write('\n')
        qc.write(f'$sequence "{sequence.name}"' + ' {\n')
        qc.write(f'    "anims/{common.clean_filename(sequence.name)}.SMD"\n')
        if sequence.use_framerate:
            qc.write(f'    fps {sequence.framerate}\n')
        else:
            qc.write(f'    fps {bpy.context.scene.render.fps}\n')
        if sequence.use_range:
            qc.write(f'    frames {sequence.start} {sequence.end}\n')
        if sequence.snap:
            qc.write('    snap\n')
        if sequence.loop:
            qc.write('    loop\n')
        qc.write(f'    activity "{sequence.activity}" {sequence.weight}\n')
        for event in sequence.event_items:
            qc.write('    { ' + f'event "{event.event}" {event.frame} "{event.value}"' + ' }\n')
        qc.write('}')
        qc.write('\n')

    for attachment in self.attachment_items:
        if self.armature and attachment.bone:
            qc.write('\n')
            qc.write(f'$attachment "{attachment.name}"')
            if self.prepend_armature:
                qc.write(f' "{self.armature.name}.{attachment.bone}"')
            else:
                qc.write(f' "{attachment.bone}"')
            qc.write(f' {attachment.offset[0]} {attachment.offset[1]} {attachment.offset[2]}')
            if attachment.absolute:
                qc.write(' absolute')
            if attachment.rigid:
                qc.write(' rigid')
            qc.write(f' rotate {attachment.rotation[0]} {attachment.rotation[1]} {attachment.rotation[2]}')
            qc.write('\n')

    if self.skin_items:
        qc.write('\n')
        qc.write('$texturegroup "skinfamilies"')
        qc.write('\n')
        qc.write('{')

        for skin in self.skin_items:
            qc.write('\n')
            qc.write(f'    {{ {skin.name} }}')

        qc.write('\n')
        qc.write('}')
        qc.write('\n')
    
    if(len(self.particle_items) > 0):
        qc.write('\n')      
        qc.write('$keyvalues')
        qc.write('\n')
        qc.write('{')
        qc.write('\n')
        qc.write('    particles')
        qc.write('\n')
        qc.write('    {')
        
        for index, particle in enumerate(self.particle_items):
            qc.write('\n')
            qc.write(f'        "effect{index}"')
            qc.write('\n        {\n')
            qc.write(f'            "name" "{particle.name}"')
            qc.write('\n')
            qc.write(f'            "attachment_type" "{particle.attachment_type}"')
            qc.write('\n')
            if(particle.attachment_point):
                qc.write(f'            "attachment_point" "{particle.attachment_point}"')
                qc.write('\n')
            qc.write('        }\n')
        
        qc.write('    }')
        qc.write('\n')
        qc.write('}')
    
    qc.close()
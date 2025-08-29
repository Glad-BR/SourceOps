import bpy


class SOURCEOPS_EventProps(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(
        name='Name',
        description='The name this event has in the list, just for display',
        default='Example',
    ) #type:ignore

    event: bpy.props.StringProperty(
        name='Event Type',
        description='The type of the event',
        default='AE_CL_PLAYSOUND',
    ) #type:ignore

    frame: bpy.props.IntProperty(
        name='Start Frame',
        description='The frame of the sequence at which the event should start',
        default=0,
    ) #type:ignore

    value: bpy.props.StringProperty(
        name='Event Value',
        description='The value for the event',
        default='Weapon_Shotgun.Single',
    ) #type:ignore

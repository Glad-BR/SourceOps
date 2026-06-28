#from .. import PyVTFlib

#SOURCEOPS_VTF_FORMAT             = [(i.name, i.name, '') for i in PyVTFlib.FORMAT]
#SOURCEOPS_VTF_PLATFORM           = [(i.name, i.name, '') for i in PyVTFlib.PLATFORM]
#SOURCEOPS_VTF_FILE_FORMAT        = [(i.name, i.name, '') for i in PyVTFlib.FILE_FORMAT]
#SOURCEOPS_VTF_RESIZE_FILTER      = [(i.name, i.name, '') for i in PyVTFlib.RESIZE_FILTER]
#SOURCEOPS_VTF_RESIZE_METHOD      = [(i.name, i.name, '') for i in PyVTFlib.RESIZE_METHOD]
#SOURCEOPS_VTF_COMPRESSION_METHOD = [(i.name, i.name, '') for i in PyVTFlib.COMPRESSION_METHOD]


from sourcepp import vtfpp

SOURCEOPS_VTF_FORMAT = [(i.name, i.name, '') for i in vtfpp.ImageFormat]
SOURCEOPS_VTF_FLAGS  = [(i.name, i.name, '') for i in vtfpp.VTF.Flags]
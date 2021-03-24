import os
import constants


def __bootstrap__():
    global __bootstrap__, __loader__, __file__
    import sys, pkg_resources, imp
    __file__ = pkg_resources.resource_filename(__name__, os.path.join(constants.bundle_dir, 'webrtcvad_package//_webrtcvad.cp36-win_amd64.pyd'))
    __loader__ = None; del __bootstrap__, __loader__
    imp.load_dynamic(__name__,__file__)
__bootstrap__()

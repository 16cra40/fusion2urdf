#Author-syuntoku14
#Author-spacemaster85
#Modified on Sun Jan 17 2021
#Description-Generate URDF file from Fusion 360

import adsk, adsk.core, adsk.fusion, traceback
import os
from .utils import utils
from .core import Link, Joint, Write

"""
# length unit is 'cm' and inertial unit is 'kg/cm^2'
# If there is no 'body' in the root component, maybe the corrdinates are wrong.
"""

# joint effort: 100
# joint velocity: 100
# supports "Revolute", "Rigid" and "Slider" joint types



# I'm not sure how prismatic joint acts if there is no limit in fusion model

def run(context):
    ui = None
    success_msg = 'Successfully created URDF file'
    msg = success_msg

    try:
        # --------------------
        # initialize
        app = adsk.core.Application.get()
        ui = app.userInterface
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        title = 'Fusion2URDF'
        if not design:
            ui.messageBox('No active Fusion design', title)
            return

        root = design.rootComponent  # root component 
        # set the names
        robot_name = "default"      
        robot_name = ui.inputBox('Name of Robot', 
                                'Name the robot', robot_name)
        package_name = "%s_description"%robot_name[0]  
        robot_name = robot_name[0]
        robot_name.lower()
        package_name.lower()
        
        save_dir = utils.file_dialog(ui)
        if save_dir == False:
            ui.messageBox('Fusion2URDF was canceled', title)
            return 0

        save_dir= save_dir + '/' + package_name
        try: os.mkdir(save_dir)
        except: pass  

        package_dir_ros2 = os.path.abspath(os.path.dirname(__file__)) + '/package_ros2/'        
        # --------------------
        # set dictionaries
        
        # Generate joints_dict. All joints are related to root. 
        joints_dict, msg = Joint.make_joints_dict(root, msg)
        if msg != success_msg:
            ui.messageBox(msg, title)
            return 0   
        print(joints_dict)
        # Generate inertial_dict
        inertial_dict, msg = Link.make_inertial_dict(root, msg)
        if msg != success_msg:
            ui.messageBox(msg, title)
            return 0
        elif not 'base_link' in inertial_dict:
            msg = 'There is no base_link. Please set base_link and run again.'
            ui.messageBox(msg, title)
            return 0
        
        material_dict, color_dict, msg = Link.make_material_dict(root, msg)
        if msg != success_msg:
            ui.messageBox(msg, title)
            return 0  
        
        links_xyz_dict = {} 
        # --------------------
        # Generate URDF
        Write.write_urdf(joints_dict, links_xyz_dict, inertial_dict, material_dict, package_name, robot_name, save_dir, 0)
        Write.write_materials_xacro(color_dict, robot_name, save_dir)
        Write.write_transmissions_xacro(joints_dict, links_xyz_dict, robot_name, save_dir)
        utils.copy_package(save_dir, package_dir_ros2)
        utils.update_cmakelists(save_dir, package_name)
        utils.update_package_xml(save_dir, package_name)
        utils.update_ros2_launchfile(save_dir, robot_name)

        # Generate STl files        
        utils.export_stl(app, save_dir)   

        ui.messageBox(msg, title)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

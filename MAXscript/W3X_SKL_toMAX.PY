
# 一定要在3DSMAX环境里跑这个脚本！

import os
import xml.etree.ElementTree as ET
import pymxs
from PySide2 import QtWidgets, QtCore

rt = pymxs.runtime

# ------------------------------
# --不知为何MAX环境里用不了NUMPY，把辅助方程抄过来
# ------------------------------
def cross(v1, v2):  
    """Return the cross product of two 3D vectors.""" #3D向量叉乘
    return (
        v1[1]*v2[2] - v1[2]*v2[1],
        v1[2]*v2[0] - v1[0]*v2[2],
        v1[0]*v2[1] - v1[1]*v2[0]
    )

def add_vectors(v1, v2):
    """Add two 3D vectors.""" #3D位置相加
    return (v1[0] + v2[0], v1[1] + v2[1], v1[2] + v2[2])

def multiply_quaternions(q1, q2):   #两个四元数的旋转叠加
    """ 
    Multiply two quaternions.
    Each quaternion is a tuple (x, y, z, w). The result is computed as:
      world_quat = parent_quat * local_quat.
    """
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 - x1*z2 + y1*w2 + z1*x2
    z = w1*z2 + x1*y2 - y1*x2 + z1*w2
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    return (x, y, z, w)

def rotate_vector_by_quat(v, q):    #把3D向量用四元数转一下，SHADER里有差不多的
    """
    Rotate a vector v (tuple of 3 floats) by quaternion q (tuple (x, y, z, w)).
    Using the formula: v' = v + 2*q.w*(q.xyz x v) + 2*(q.xyz x (q.xyz x v))
    """
    q_vec = (q[0], q[1], q[2])
    t = tuple(2 * val for val in cross(q_vec, v))
    qwx_t = tuple(q[3] * val for val in t)
    qv_cross_t = cross(q_vec, t)
    return add_vectors(v, add_vectors(qwx_t, qv_cross_t))

# ------------------------------
# 提取XML信息
# ------------------------------
def extract_w3d_hierarchy_section(file_path):
    """
    Reads the file as text and extracts the <W3DHierarchy>...</W3DHierarchy> block.
    Returns the XML string or None if not found.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        rt.print(f"Error reading the file: {e}")
        return None

    start_tag = "<W3DHierarchy"
    end_tag = "</W3DHierarchy>"
    start_idx = content.find(start_tag)
    if start_idx == -1:
        rt.print("Error: <W3DHierarchy> tag not found.")
        return None
    end_idx = content.find(end_tag, start_idx)
    if end_idx == -1:
        rt.print("Error: </W3DHierarchy> tag not found.")
        return None
    end_idx += len(end_tag)
    return content[start_idx:end_idx]

# ------------------------------
# 搓个方盒子作为骨骼的替代品，以后加上真正的骨骼
# ------------------------------
def create_box_from_transform(name, translation, rotation):
    """
    Creates a box in 3ds Max with fixed dimensions (2, 1, 0.5) and green wirecolor.
    
    In this revised function, the box is first created at the origin, its rotation is set,
    and then it is moved to its world position. This ensures the rotation is applied about its own center.
    """
    # Create the box at the origin.
    box = rt.box(width=1, length=0.5, height=0.0)
    box.name = name
    box.wirecolor = rt.color(0, 255, 0)
    # Set box position to origin first.
    box.position = rt.Point3(0, 0, 0)
    # Apply rotation.
    box.rotation = rt.quat(rotation[0], rotation[1], rotation[2], rotation[3])
    # Now move the box to its world position.
    box.position = rt.Point3(translation[0], translation[1], translation[2])
    return box

# ------------------------------
# 遍历地旋转和挪骨骼（归递不好用）然后记录
# ------------------------------
def process_w3d_hierarchy(xml_file_path, create_max_objects=True):
    """
    Parses the W3DHierarchy section from the file and builds an indexed list of pivot info.
    Each pivot record is a dictionary with the following keys:
      index, name, parent_index, parent_name, local_translation, local_rotation,
      world_position, world_quaternion
    World transform is computed iteratively.
    
    If create_max_objects is True, create boxes in Max and set parent links.
    Returns the pivot list and total count.
    """
    w3d_xml = extract_w3d_hierarchy_section(xml_file_path)
    if not w3d_xml:
        return None, 0

    try:
        w3d_root = ET.fromstring(w3d_xml)
    except Exception as e:
        rt.print(f"Error parsing W3DHierarchy XML: {e}")
        return None, 0

    pivot_list = []
    # Build pivot_list from each Pivot element.
    for i, pivot in enumerate(w3d_root.findall('Pivot')):
        name = pivot.get("Name")
        parent_idx_str = pivot.get("Parent")
        try:
            parent_index = int(parent_idx_str)
        except:
            parent_index = -1
        trans_elem = pivot.find('Translation')
        rot_elem = pivot.find('Rotation')
        if trans_elem is None or rot_elem is None:
            rt.print(f"Skipping Pivot {name}: missing Translation or Rotation.")
            continue
        try:
            local_translation = (
                float(trans_elem.get("X")),
                float(trans_elem.get("Y")),
                float(trans_elem.get("Z"))
            )
            local_rotation = (
                float(rot_elem.get("X")),
                float(rot_elem.get("Y")),
                float(rot_elem.get("Z")),
                float(rot_elem.get("W"))
            )
        except Exception as e:
            rt.print(f"Error parsing Pivot {name}: {e}")
            continue

        pivot_list.append({
            "index": i,
            "name": name,
            "parent_index": parent_index,
            "parent_name": "",  # To be filled later.
            "local_translation": local_translation,
            "local_rotation": local_rotation,
            "world_position": (0.0, 0.0, 0.0),    # Initialize.
            "world_quaternion": (0.0, 0.0, 0.0, 1.0)  # Initialize.
        })

    if not pivot_list:
        return None, 0

    # Ensure that the ROOTTRANSFORM pivot is at index 0.
    if pivot_list[0]["name"] != "ROOTTRANSFORM":
        for j in range(len(pivot_list)):
            if pivot_list[j]["name"] == "ROOTTRANSFORM":
                pivot_list[0], pivot_list[j] = pivot_list[j], pivot_list[0]
                pivot_list[0]["index"] = 0
                pivot_list[j]["index"] = j
                break

    # Iteratively compute world transforms.
    for pivot in pivot_list:
        if pivot["index"] == 0:
            # For ROOTTRANSFORM, assume local is world.
            pivot["world_position"] = pivot["local_translation"]
            pivot["world_quaternion"] = pivot["local_rotation"]
        else:
            parent_idx = pivot["parent_index"]
            if parent_idx < 0 or parent_idx >= len(pivot_list):
                pivot["world_position"] = pivot["local_translation"]
                pivot["world_quaternion"] = pivot["local_rotation"]
            else:
                parent = pivot_list[parent_idx]
                rotated_local = rotate_vector_by_quat(pivot["local_translation"], parent["world_quaternion"])
                pivot["world_position"] = add_vectors(parent["world_position"], rotated_local)
                pivot["world_quaternion"] = multiply_quaternions(parent["world_quaternion"], pivot["local_rotation"])

    # Fill in parent's name for each pivot.
    for pivot in pivot_list:
        p_idx = pivot["parent_index"]
        if p_idx >= 0 and p_idx < len(pivot_list):
            pivot["parent_name"] = pivot_list[p_idx]["name"]
        else:
            pivot["parent_name"] = ""

    # If requested, create Max objects and set parent links.
    if create_max_objects:
        for pivot in pivot_list:
            box = create_box_from_transform(pivot["name"], pivot["world_position"], pivot["world_quaternion"])
            # If this pivot is ROOTTRANSFORM, set its box color to blue.
            if pivot["name"] == "ROOTTRANSFORM":
                box.wirecolor = rt.color(0, 0, 255)
            pivot["box"] = box
        for pivot in pivot_list:
            p_idx = pivot["parent_index"]
            if p_idx >= 0 and p_idx < len(pivot_list):
                child_box = pivot.get("box")
                parent_box = pivot_list[p_idx].get("box")
                if child_box and parent_box:
                    child_box.parent = parent_box

    return pivot_list, len(pivot_list)

# ------------------------------
# 把W3X数据结构和刚刚算出来的世界坐标都搓成INI
# ------------------------------
def export_ini_file(pivot_list, original_file_path):
    """
    Exports the pivot_list as an INI file.
    The INI file is saved in the same folder as the original file, with the original filename
    appended with ".SKL.ini".
    """
    if not pivot_list:
        return

    folder = os.path.dirname(original_file_path)
    base_name = os.path.basename(original_file_path)
    ini_filename = os.path.join(folder, base_name + ".SKL.ini")

    try:
        with open(ini_filename, 'w', encoding='utf-8') as f:
            for pivot in pivot_list:
                f.write(f"[Pivot{pivot['index']}]\n")
                f.write(f"Index={pivot['index']}\n")
                f.write(f"Name={pivot['name']}\n")
                f.write(f"ParentIndex={pivot['parent_index']}\n")
                f.write(f"ParentName={pivot['parent_name']}\n")
                lt = ",".join(str(x) for x in pivot["local_translation"])
                f.write(f"LocalTranslation={lt}\n")
                lr = ",".join(str(x) for x in pivot["local_rotation"])
                f.write(f"LocalRotation={lr}\n")
                wp = ",".join(str(x) for x in pivot["world_position"])
                f.write(f"WorldPosition={wp}\n")
                wq = ",".join(str(x) for x in pivot["world_quaternion"])
                f.write(f"WorldQuaternion={wq}\n\n")
        rt.print(f"INI file exported to: {ini_filename}")
    except Exception as e:
        rt.print(f"Error exporting INI file: {e}")

# ------------------------------
# GUI
# ------------------------------
class W3DImporterUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(W3DImporterUI, self).__init__(parent)
        self.setWindowTitle("W3D Hierarchy Importer")
        self.resize(500, 350)
        self.file_path = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Create four buttons with the desired labels.
        self.select_button = QtWidgets.QPushButton("Select W3X SKL File")
        self.import_button = QtWidgets.QPushButton("Import Hierarchy from W3X")
        self.w3x_to_ini_button = QtWidgets.QPushButton("W3X to INI")
        self.ini_to_max_button = QtWidgets.QPushButton("INI to MAX")

        # Message display area.
        self.message_display = QtWidgets.QTextEdit()
        self.message_display.setReadOnly(True)

        # Add widgets to the layout.
        layout.addWidget(self.select_button)
        layout.addWidget(self.import_button)
        layout.addWidget(self.w3x_to_ini_button)
        layout.addWidget(self.ini_to_max_button)
        layout.addWidget(self.message_display)

        # Connect button signals.
        self.select_button.clicked.connect(self.select_file)
        self.import_button.clicked.connect(self.import_hierarchy_from_w3x)
        self.w3x_to_ini_button.clicked.connect(self.w3x_to_ini)
        self.ini_to_max_button.clicked.connect(self.ini_to_max)

    def select_file(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select a .w3x file", "", "W3X Files (*.w3x)"
        )
        if file_path:
            self.file_path = file_path
            self.append_message(f"Selected file: {file_path}")
            # Immediately check for W3DHierarchy and count pivots.
            w3d_xml = extract_w3d_hierarchy_section(file_path)
            if w3d_xml:
                try:
                    w3d_root = ET.fromstring(w3d_xml)
                    pivots = w3d_root.findall('Pivot')
                    pivot_count = len(pivots)
                    self.append_message(f"W3DHierarchy found with {pivot_count} pivot(s).")
                except Exception as e:
                    self.append_message(f"Error parsing W3DHierarchy: {e}")
            else:
                self.append_message("No W3DHierarchy found in the file.")
        else:
            self.append_message("No file selected.")

    def import_hierarchy_from_w3x(self):
        if not self.file_path or not os.path.exists(self.file_path):
            self.append_message("Error: No valid file selected.")
            return

        self.append_message("Importing hierarchy from W3X, please wait...")
        pivot_list, total = process_w3d_hierarchy(self.file_path, create_max_objects=True)
        if not pivot_list:
            self.append_message("Error occurred during import.")
        else:
            self.append_message(f"Successfully imported {total} object(s) into Max.")
            export_ini_file(pivot_list, self.file_path)
            self.append_message("INI file exported.")

    def w3x_to_ini(self):
        if not self.file_path or not os.path.exists(self.file_path):
            self.append_message("Error: No valid file selected.")
            return

        self.append_message("Processing W3X to generate INI file, please wait...")
        pivot_list, total = process_w3d_hierarchy(self.file_path, create_max_objects=False)
        if not pivot_list:
            self.append_message("Error occurred during processing.")
        else:
            export_ini_file(pivot_list, self.file_path)
            self.append_message(f"INI file exported for {total} pivot(s).")

    def ini_to_max(self):
        self.append_message("INI to MAX function is not yet implemented.")

    def append_message(self, msg):
        self.message_display.append(msg)

if __name__ == '__main__':
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication([])

    dialog = W3DImporterUI()
    dialog.show()

# 还需要加的功能：生成有IK的骨骼，从INI读取等等
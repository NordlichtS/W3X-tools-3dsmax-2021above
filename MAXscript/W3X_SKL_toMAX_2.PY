import os
import xml.etree.ElementTree as ET
import pymxs
from PySide2 import QtWidgets, QtCore

rt = pymxs.runtime

# ------------------------------
# Quaternion and Vector Math Helpers
# ------------------------------
def cross(v1, v2):
    """Return the cross product of two 3D vectors."""
    return (
        v1[1]*v2[2] - v1[2]*v2[1],
        v1[2]*v2[0] - v1[0]*v2[2],
        v1[0]*v2[1] - v1[1]*v2[0]
    )

def add_vectors(v1, v2):
    """Add two 3D vectors."""
    return (v1[0] + v2[0], v1[1] + v2[1], v1[2] + v2[2])

def multiply_quaternions(q1, q2):
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

def rotate_vector_by_quat(v, q):
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
# XML Extraction Helper
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
# Object Creation Helpers
# ------------------------------
def create_box_from_transform(name, translation, rotation):
    """
    Creates a box in 3ds Max with fixed dimensions (2, 1, 0.5) and green wirecolor.
    The box is created at the origin, rotated, and then moved to its world position.
    """
    box = rt.box(width=2, length=1, height=0.5)
    box.name = name
    box.wirecolor = rt.color(0, 255, 0)
    # Create at origin first, apply rotation, then translate.
    box.position = rt.Point3(0, 0, 0)
    box.rotation = rt.quat(rotation[0], rotation[1], rotation[2], rotation[3])
    box.position = rt.Point3(translation[0], translation[1], translation[2])
    return box

def create_bone_from_transform(name, translation, rotation):
    """
    Creates a bone in 3ds Max with length 1.0, width 0.25, height 0.5.
    The bone is created by computing its start at the given translation,
    and its end is computed by adding the rotated local Y axis (scaled by length).
    """
    length = 1.0
    width = 0.25
    height = 0.5
    start = rt.Point3(translation[0], translation[1], translation[2])
    local_dir = (0, 1, 0)  # Bone's direction.
    rotated_dir = rotate_vector_by_quat(local_dir, rotation)
    end = rt.Point3(start.x + rotated_dir[0]*length, start.y + rotated_dir[1]*length, start.z + rotated_dir[2]*length)
    cross_vector = rt.Point3(0, 0, 1)
    bone = rt.BoneSys.createBone(start, end, cross_vector)
    bone.name = name
    bone.rotation = rt.quat(rotation[0], rotation[1], rotation[2], rotation[3])
    try:
        bone.width = width
        bone.height = height
    except Exception as e:
        rt.print("Could not set bone dimensions: " + str(e))
    return bone

def create_helper_from_transform(name, translation, rotation):
    """
    Creates a dummy helper object in 3ds Max.
    Uses rt.Dummy() to create a dummy helper.
    """
    helper = rt.Dummy()
    helper.name = name
    helper.position = rt.Point3(translation[0], translation[1], translation[2])
    helper.rotation = rt.quat(rotation[0], rotation[1], rotation[2], rotation[3])
    helper.wirecolor = rt.color(255, 255, 0)  # Yellow
    return helper

# ------------------------------
# Process W3D Hierarchy Iteratively
# ------------------------------
def process_w3d_hierarchy(xml_file_path, create_max_objects=True, object_type="box"):
    """
    Parses the W3DHierarchy section from the file and builds an indexed list of pivot info.
    Each pivot record is a dictionary with the following keys:
      index, name, parent_index, parent_name, local_translation, local_rotation,
      world_position, world_quaternion
    World transforms are computed iteratively.
    
    If create_max_objects is True, creates objects in Max of type specified by object_type.
    object_type can be "bone", "box", or "helper".
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
            if object_type == "bone":
                obj = create_bone_from_transform(pivot["name"], pivot["world_position"], pivot["world_quaternion"])
            elif object_type == "box":
                obj = create_box_from_transform(pivot["name"], pivot["world_position"], pivot["world_quaternion"])
                if pivot["name"] == "ROOTTRANSFORM":
                    obj.wirecolor = rt.color(0, 0, 255)
            elif object_type == "helper":
                obj = create_helper_from_transform(pivot["name"], pivot["world_position"], pivot["world_quaternion"])
            else:
                obj = create_box_from_transform(pivot["name"], pivot["world_position"], pivot["world_quaternion"])
                if pivot["name"] == "ROOTTRANSFORM":
                    obj.wirecolor = rt.color(0, 0, 255)
            pivot["object"] = obj
        for pivot in pivot_list:
            p_idx = pivot["parent_index"]
            if p_idx >= 0 and p_idx < len(pivot_list):
                child_obj = pivot.get("object")
                parent_obj = pivot_list[p_idx].get("object")
                if child_obj and parent_obj:
                    child_obj.parent = parent_obj

    return pivot_list, len(pivot_list)

# ------------------------------
# INI Export Function
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
        self.resize(500, 450)
        self.file_path = ""
        self.import_object_type = "box"  # Default type.
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Main buttons.
        self.select_button = QtWidgets.QPushButton("Select W3X SKL File")
        self.import_button = QtWidgets.QPushButton("Import Hierarchy from W3X")
        self.w3x_to_ini_button = QtWidgets.QPushButton("W3X to INI")
        self.ini_to_max_button = QtWidgets.QPushButton("INI to MAX")

        layout.addWidget(self.select_button)
        layout.addWidget(self.import_button)
        layout.addWidget(self.w3x_to_ini_button)
        layout.addWidget(self.ini_to_max_button)

        # New row of three small buttons.
        buttonLayout = QtWidgets.QHBoxLayout()
        self.as_bone_button = QtWidgets.QPushButton("As Bone")
        self.as_box_button = QtWidgets.QPushButton("As Box")
        self.as_helper_button = QtWidgets.QPushButton("As Helper")
        buttonLayout.addWidget(self.as_bone_button)
        buttonLayout.addWidget(self.as_box_button)
        buttonLayout.addWidget(self.as_helper_button)
        layout.addLayout(buttonLayout)

        # Message display area.
        self.message_display = QtWidgets.QTextEdit()
        self.message_display.setReadOnly(True)
        layout.addWidget(self.message_display)

        # Connect button signals.
        self.select_button.clicked.connect(self.select_file)
        self.import_button.clicked.connect(self.import_hierarchy_from_w3x)
        self.w3x_to_ini_button.clicked.connect(self.w3x_to_ini)
        self.ini_to_max_button.clicked.connect(self.ini_to_max)
        self.as_bone_button.clicked.connect(self.as_bone)
        self.as_box_button.clicked.connect(self.as_box)
        self.as_helper_button.clicked.connect(self.as_helper)

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

        self.append_message(f"Importing hierarchy as '{self.import_object_type}', please wait...")
        pivot_list, total = process_w3d_hierarchy(self.file_path, create_max_objects=True, object_type=self.import_object_type)
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

    def as_bone(self):
        self.import_object_type = "bone"
        self.append_message("Import type set to: Bone")

    def as_box(self):
        self.import_object_type = "box"
        self.append_message("Import type set to: Box")

    def as_helper(self):
        self.import_object_type = "helper"
        self.append_message("Import type set to: Helper")

    def append_message(self, msg):
        self.message_display.append(msg)

if __name__ == '__main__':
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication([])

    dialog = W3DImporterUI()
    dialog.show()

## Concept Document: Python/Qt Memory Map Editor

### 1\. Project Vision and Goals

**Vision:** To create a standalone, performant, and intuitive desktop application using Python and the Qt framework for visually editing IP core memory maps. The tool will be the single source of truth for the hardware specification, loading from and exporting to a clean, standardized YAML file.

**Core Goals:**

  * **Intuitive Editing:** Provide a best-in-class visual interface for a task typically handled by text editors.
  * **Error Prevention:** Eliminate YAML syntax and logical errors (e.g., address overlaps) through a guided UI.
  * **Seamless Integration:** Allow engineers to easily load existing YAML memory maps, modify them, and save them back.
  * **Cross-Platform:** Leverage the power of Python and Qt to create a single application that runs on Windows, macOS, and Linux.

### 2\. Core Architecture: Model-View-Controller (MVC) with Python/Qt

To ensure the application is robust, testable, and maintainable, a Model-View-Controller (MVC) architecture is the ideal choice. This separates the application's data and business logic from its user interface.

#### **Model (`memory_map_core.py`)**

This is the non-graphical "brain" of the application. It's a pure Python library with no Qt dependencies.

  * **Data Structures:** Uses Python's `dataclasses` to define the `Register`, `RegisterArray`, and `BitField` objects.
  * **Business Logic:** Contains all validation rules, such as detecting overlapping address ranges or conflicting bit-fields.
  * **Serialization:**
      * A `load_from_yaml(file_path)` function that uses the `PyYAML` library to parse a file and populate the data classes.
      * A `save_to_yaml(data, file_path)` function that takes the current state of the data classes and generates a clean YAML file.

#### **View (Qt Widgets)**

This is the user-facing part of the application, built from Qt widgets.

  * **Main Window:** A `QMainWindow` that contains the main layout and menus.
  * **Memory Map Outline:** A `QListWidget` or `QTreeView` to display the list of registers and arrays.
  * **Detail Forms:** A `QWidget` containing various input widgets like `QLineEdit` for names, `QSpinBox` for offsets (with hex display enabled), and `QTextEdit` for descriptions.
  * **The Bit Field Visualizer:** This is the key feature and will be a **custom `QWidget`**. It will override the `paintEvent()` method to manually draw rectangles and text, giving us complete control over the visual representation of the bit-fields.

#### **Controller (Application Logic)**

This is the glue that connects the Model and the View. It's the main Python application code that handles user interactions.

  * **Event Handling:** Uses Qt's powerful **signals and slots** mechanism. For example, a `clicked()` signal from a "Save" button is connected to a `save_map()` slot in the controller.
  * **State Management:** When a user edits a field in the View (e.g., changes a register's name), the Controller updates the corresponding object in the Model. It then tells the View to refresh if needed.
  * **Coordination:** The Controller orchestrates the loading and saving process, interacting with both the Model and file dialogs (`QFileDialog`).

### 3\. Key Feature: Loading and Saving YAML Files

The ability to start from an existing memory map is crucial.

#### **Loading Workflow**

1.  **User Action:** The user clicks a menu item (`File -> Open...`) or an "Open File" button on a welcome screen.
2.  **Controller Action:** The Controller creates and shows a `QFileDialog`, filtering for `.yaml` files.
3.  **File Selection:** The user selects a valid YAML file.
4.  **Model Update:** The Controller passes the selected `file_path` to the `memory_map_core.load_from_yaml()` function. The core library handles the file reading, parsing, and populating its internal data objects. It then returns a fully populated memory map object.
5.  **View Population:** The Controller receives the new data object from the Model. It then iterates through the data, clearing and populating the `QListWidget` (the outline) and other UI elements to reflect the contents of the file.

#### **Saving Workflow**

The saving process is the reverse. The Controller takes the current state of the Model, passes it to the `save_to_yaml()` function, and writes the output to a file, again using a `QFileDialog` for the "Save As..." operation.

### 4\. UI/UX Implementation with Qt

The three-pane layout remains the ideal design, implemented with dockable or resizable Qt widgets.

```
+-----------------------------------------------------------------------------------+
| File  Edit  View  Help                                                            |
| [Open...] [Save]                                                                  |
+-----------------------------------------------------------------------------------+
| [ QListWidget        ] | [           QWidget with Form Layout                 ]  |
| (Memory Map Outline) | |                                                          |
|                        | |  Name:     [ QLineEdit        ]                           |
|  - control             | |  Offset:   [ QSpinBox         ]                           |
|  - status              | |                                                          |
| >[ lut_entry (Array)  ] | | +--------------------------------------------------+ |
|                        | | |     Custom BitFieldVisualizerWidget              | |
| [ QPushButton 'Add'  ] | | | (Overrides paintEvent() to draw fields)        | |
|                        | | +--------------------------------------------------+ |
|                        | |                                                          |
|                        | | [ QTableWidget for Bit Field Properties          ] |
|                        | |                                                          |
+-----------------------------------------------------------------------------------+
```

### 5\. User Workflow Example

1.  **Launch App:** The user opens the application.
2.  **Open File:** The user navigates to `File -> Open...` and selects their existing `ip_core_map.yaml`.
3.  **Data Population:** The UI instantly populates. The Outline shows `control`, `status`, and `lut_entry`.
4.  **Select Register:** The user clicks on `status` in the Outline.
5.  **View Details:** The Detail View populates with the offset (0x04). The Bit Field Visualizer graphically displays the `ready` and `error_code` fields. The table below lists their properties.
6.  **Modify a Field:** The user selects the `error_code` field and changes its **Bits** from `[7:4]` to `[9:4]`. The visualizer immediately updates, showing the block widening, and flags it in red if it now overlaps another field.
7.  **Save Changes:** The user clicks `File -> Save`. The application overwrites the original `ip_core_map.yaml` with the updated, correctly formatted data.

### 6\. Development and Technology Stack

  * **Language:** Python 3.9+
  * **GUI Framework:** **PySide6** (the official, LGPL-licensed Qt for Python bindings from The Qt Company).
  * **Core Libraries:**
      * `PyYAML`: For robust YAML parsing and generation.
      * `dataclasses`: For clean and simple data model definition.
  * **Packaging:** `PyInstaller` or `cx_Freeze` will be used to package the application, its Python interpreter, and all dependencies into a standalone, distributable executable for each target OS.

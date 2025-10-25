###对话框
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLabel, QLineEdit, QPushButton, QListWidget, QComboBox,
                             QSpinBox, QColorDialog, QFileDialog, QMessageBox,
                             QDialogButtonBox, QTextEdit, QInputDialog, QListWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFontDatabase


class AddFontDialog(QDialog):
    """字体添加对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加字体")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.font_name = QLineEdit()
        form_layout.addRow("字体名称:", self.font_name)
        
        self.font_path = QLineEdit()
        self.font_path.setReadOnly(True)
        form_layout.addRow("字体文件:", self.font_path)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_font)
        form_layout.addRow("", self.browse_btn)
        
        layout.addLayout(form_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse_font(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择字体文件", "", "TrueType字体 (*.ttf *.ttc);;所有文件 (*)"
        )
        if file_path:
            self.font_path.setText(file_path)
            if not self.font_name.text():
                font_name = os.path.splitext(os.path.basename(file_path))[0]
                self.font_name.setText(font_name)


class TextEditDialog(QDialog):
    """文字编辑对话框"""
    def __init__(self, text_item, font_manager, parent=None):
        super().__init__(parent)
        self.text_item = text_item
        self.font_manager = font_manager
        self.setWindowTitle("编辑文字")
        self.setModal(True)
        self.setup_ui()
        self.load_current_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 文字内容
        content_layout = QHBoxLayout()
        content_layout.addWidget(QLabel("文字内容:"))
        self.text_input = QTextEdit()
        self.text_input.setMaximumHeight(80)
        content_layout.addWidget(self.text_input)
        layout.addLayout(content_layout)
        
        # 字体选择
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字体:"))
        self.font_combo = QComboBox()
        self.font_combo.addItems(self.font_manager.fonts.keys())
        font_layout.addWidget(self.font_combo)
        
        self.add_font_btn = QPushButton("+")
        self.add_font_btn.setFixedWidth(30)
        self.add_font_btn.clicked.connect(self.add_font)
        font_layout.addWidget(self.add_font_btn)
        layout.addLayout(font_layout)
        
        # 字体大小和颜色
        control_layout = QHBoxLayout()
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 200)
        control_layout.addWidget(QLabel("大小:"))
        control_layout.addWidget(self.font_size)
        
        self.color_btn = QPushButton("颜色")
        self.color_btn.clicked.connect(self.choose_color)
        self.current_color = QColor(Qt.black)
        control_layout.addWidget(self.color_btn)
        layout.addLayout(control_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_current_settings(self):
        if self.text_item:
            text_content = self.text_item.toPlainText()
            self.text_input.setPlainText(text_content)
            current_font = self.text_item.font()
            font_family = current_font.family()
            font_size = current_font.pointSize()
            self.font_size.setValue(font_size)
            
            # 查找当前字体
            current_font_path = None
            for name, path in self.font_manager.fonts.items():
                if path and os.path.exists(path):
                    try:
                        font_id = QFontDatabase.addApplicationFont(path)
                        if font_id != -1:
                            font_families = QFontDatabase.applicationFontFamilies(font_id)
                            if font_families and font_family in font_families:
                                self.font_combo.setCurrentText(name)
                                current_font_path = path
                                break
                    except:
                        pass
            
            if not current_font_path:
                for name, path in self.font_manager.fonts.items():
                    if path == font_family:
                        self.font_combo.setCurrentText(name)
                        current_font_path = path
                        break
            
            if not current_font_path:
                self.font_combo.setCurrentText("默认字体")
            
            self.current_color = self.text_item.defaultTextColor()
            self.update_color_button()

    def add_font(self):
        dialog = AddFontDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            font_name = dialog.font_name.text()
            font_path = dialog.font_path.text()
            if font_name and font_path and os.path.exists(font_path):
                self.font_manager.add_font(font_name, font_path)
                self.font_combo.addItem(font_name)
                self.font_combo.setCurrentText(font_name)
                if hasattr(self.parent(), 'update_font_combo'):
                    self.parent().update_font_combo()

    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self.update_color_button()

    def update_color_button(self):
        self.color_btn.setStyleSheet(f"background-color: {self.current_color.name()}; border: 1px solid black;")

    def get_text_data(self):
        return {
            'text': self.text_input.toPlainText(),
            'font_name': self.font_combo.currentText(),
            'font_size': self.font_size.value(),
            'color': self.current_color
        }


class MultiFolderDialog(QDialog):
    """多文件夹选择对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加多个图片文件夹")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        self.folders = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        info_label = QLabel("选择多个图片文件夹，每个文件夹可以设置不同的类别名称：")
        layout.addWidget(info_label)
        
        self.folder_list = QListWidget()
        self.folder_list.setMaximumHeight(200)
        layout.addWidget(QLabel("已选择的文件夹："))
        layout.addWidget(self.folder_list)
        
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("添加文件夹")
        self.add_btn.clicked.connect(self.add_folder)
        button_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("移除选中")
        self.remove_btn.clicked.connect(self.remove_folder)
        button_layout.addWidget(self.remove_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def add_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "选择图片文件夹")
        if folder_path:
            existing_paths = [folder[0] for folder in self.folders]
            if folder_path in existing_paths:
                QMessageBox.information(self, "提示", "该文件夹已经添加过了")
                return
            
            default_name = os.path.basename(folder_path)
            category_name, ok = QInputDialog.getText(
                self, "输入类别名称", 
                f"请输入文件夹 '{default_name}' 的类别名称:", 
                text=default_name
            )
            if ok and category_name:
                self.folders.append((folder_path, category_name))
                self.update_folder_list()

    def remove_folder(self):
        current_row = self.folder_list.currentRow()
        if current_row >= 0:
            del self.folders[current_row]
            self.update_folder_list()

    def update_folder_list(self):
        self.folder_list.clear()
        for folder_path, category_name in self.folders:
            folder_name = os.path.basename(folder_path)
            item_text = f"{category_name} ({folder_name})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, (folder_path, category_name))
            self.folder_list.addItem(item)

    def get_selected_folders(self):
        return self.folders

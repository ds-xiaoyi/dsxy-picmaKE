"""
dsxy-picmaKE - maimai封面制作工具
主程序 - 本人和朋友用来做舞萌手元封面的
素材是从SDEZ1.60解包的QWQ，曲绘按id搜
"""
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QSpinBox, 
                             QColorDialog, QFileDialog, QMessageBox, QTextEdit, QGroupBox,
                             QAction, QMenuBar)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIcon

# 导入自定义模块
from dialogs import AddFontDialog, TextEditDialog
from template import CoverTemplate, MovableImageItem
from editor import TemplateEditor
from managers import LayerManager, ImageLibrary, FontManager

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("错误：缺少PIL库，请安装Pillow：pip install Pillow")
    sys.exit(1)


class MainWindow(QMainWindow):
    """主窗口类"""
    def __init__(self):
        super().__init__()
        self.font_manager = FontManager()
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("dsxy-picmaKE")
        self.setGeometry(100, 100, 1400, 800)
        
        # 中间
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        #左边
        left_panel = QVBoxLayout()
        left_panel.setContentsMargins(0, 0, 0, 0)
        
        # 文本编辑
        text_group = QGroupBox("文本编辑")
        text_layout = QVBoxLayout()
        text_group.setLayout(text_layout)
        
        self.text_input = QTextEdit()
        self.text_input.setMaximumHeight(60)
        text_layout.addWidget(QLabel("文本内容:"))
        text_layout.addWidget(self.text_input)
        
        # 字体
        font_layout = QHBoxLayout()
        self.font_combo = QComboBox()
        self.font_combo.addItems(self.font_manager.fonts.keys())
        font_layout.addWidget(QLabel("字体:"))
        font_layout.addWidget(self.font_combo)
        
        self.add_font_btn = QPushButton("+")
        self.add_font_btn.setFixedWidth(30)
        self.add_font_btn.clicked.connect(self.add_font)
        font_layout.addWidget(self.add_font_btn)
        text_layout.addLayout(font_layout)
        
        # 字体大小和颜色
        control_layout = QHBoxLayout()
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 200)
        self.font_size.setValue(24)
        control_layout.addWidget(QLabel("大小:"))
        control_layout.addWidget(self.font_size)
        
        self.color_btn = QPushButton("颜色")
        self.color_btn.clicked.connect(self.choose_color)
        self.current_color = QColor(Qt.black)
        control_layout.addWidget(self.color_btn)
        text_layout.addLayout(control_layout)
        
        self.add_text_btn = QPushButton("添加文本到模板")
        self.add_text_btn.clicked.connect(self.add_text_to_template)
        text_layout.addWidget(self.add_text_btn)
        left_panel.addWidget(text_group)
        
        # 模板
        template_group = QGroupBox("模板操作")
        template_layout = QVBoxLayout()
        template_group.setLayout(template_layout)
        
        # 比例
        ratio_layout = QHBoxLayout()
        ratio_layout.addWidget(QLabel("比例:"))
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(["16:9", "4:3"])
        self.ratio_combo.setCurrentText("16:9")
        self.ratio_combo.currentTextChanged.connect(self.change_aspect_ratio)
        ratio_layout.addWidget(self.ratio_combo)
        template_layout.addLayout(ratio_layout)
        
        # 背景和操作按钮
        bg_color_layout = QHBoxLayout()
        bg_color_layout.addWidget(QLabel("背景颜色:"))
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedSize(30, 30)
        self.bg_color_btn.setStyleSheet("background-color: white; border: 1px solid black;")
        self.bg_color_btn.clicked.connect(self.choose_bg_color)
        bg_color_layout.addWidget(self.bg_color_btn)
        
        self.show_4_3_guide_btn = QPushButton("显示4:3参考框")
        self.show_4_3_guide_btn.setCheckable(True)
        self.show_4_3_guide_btn.setChecked(False)
        self.show_4_3_guide_btn.clicked.connect(self.toggle_4_3_guide)
        bg_color_layout.addWidget(self.show_4_3_guide_btn)
        
        self.undo_btn = QPushButton("撤销")
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self.undo_action)
        bg_color_layout.addWidget(self.undo_btn)
        
        self.redo_btn = QPushButton("重做")
        self.redo_btn.setEnabled(False)
        self.redo_btn.clicked.connect(self.redo_action)
        bg_color_layout.addWidget(self.redo_btn)
        bg_color_layout.addStretch()
        template_layout.addLayout(bg_color_layout)
        
        self.edit_mode_btn = QPushButton("背景编辑模式")
        self.edit_mode_btn.setCheckable(True)
        self.edit_mode_btn.clicked.connect(self.toggle_edit_mode)
        template_layout.addWidget(self.edit_mode_btn)
        
        self.delete_btn = QPushButton("删除选中元素")
        self.delete_btn.clicked.connect(self.delete_selected_elements)
        template_layout.addWidget(self.delete_btn)
        
        self.save_template_btn = QPushButton("保存模板")
        self.save_template_btn.clicked.connect(self.save_template)
        template_layout.addWidget(self.save_template_btn)
        
        self.load_template_btn = QPushButton("加载模板")
        self.load_template_btn.clicked.connect(self.load_template)
        template_layout.addWidget(self.load_template_btn)
        
        left_panel.addWidget(template_group)
        
        # 右边
        right_panel = QVBoxLayout()
        self.template_editor = TemplateEditor()
        self.template_editor.font_manager = self.font_manager
        right_panel.addWidget(self.template_editor)
        self.template_editor.set_aspect_ratio("16:9")
        
        ##
        self.image_library = ImageLibrary()
        self.addDockWidget(Qt.RightDockWidgetArea, self.image_library)
        
        self.layer_manager = LayerManager(self.template_editor)
        self.addDockWidget(Qt.RightDockWidgetArea, self.layer_manager)
        
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 3)
        
        # 连接
        self.image_library.add_bg_btn.clicked.connect(self.set_background_from_library)
        self.image_library.add_foreground_btn.clicked.connect(self.add_foreground_image)
        self.image_library.replace_btn.clicked.connect(self.replace_selected_image)
        self.image_library.image_list.itemDoubleClicked.connect(self.use_selected_image)
        
        # 创建菜单和快捷键
        self.create_menu()
        self.setup_shortcuts()
        self.setup_undo_shortcuts()
        

    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        new_action = QAction('新建模板', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_template)
        file_menu.addAction(new_action)
        
        open_action = QAction('打开模板', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.load_template)
        file_menu.addAction(open_action)
        
        save_action = QAction('保存模板', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_template)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        export_action = QAction('导出封面', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_cover)
        file_menu.addAction(export_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑')
        delete_action = QAction('删除选中', self)
        delete_action.setShortcut('Delete')
        delete_action.triggered.connect(self.delete_selected_elements)
        edit_menu.addAction(delete_action)
        
        # 视图菜单
        view_menu = menubar.addMenu('视图')
        view_menu.addAction(self.image_library.toggleViewAction())
        view_menu.addAction(self.layer_manager.toggleViewAction())

    def setup_shortcuts(self):
        """设置快捷键"""
        delete_action = QAction(self)
        delete_action.setShortcut(Qt.Key_Delete)
        delete_action.triggered.connect(self.delete_selected_elements)
        self.addAction(delete_action)
        
        delete_action2 = QAction(self)
        delete_action2.setShortcut(Qt.Key_Backspace)
        delete_action2.triggered.connect(self.delete_selected_elements)
        self.addAction(delete_action2)

    def setup_undo_shortcuts(self):
        """设置撤销重做快捷键"""
        undo_action = QAction(self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_action)
        self.addAction(undo_action)
        
        redo_action = QAction(self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo_action)
        self.addAction(redo_action)

    def add_font(self):
        """添加字体"""
        dialog = AddFontDialog(self)
        if dialog.exec_() == dialog.Accepted:
            font_name = dialog.font_name.text()
            font_path = dialog.font_path.text()
            if font_name and font_path and os.path.exists(font_path):
                self.font_manager.add_font(font_name, font_path)
                self.update_font_combo()

    def update_font_combo(self):
        """更新字体下拉框"""
        self.font_combo.clear()
        self.font_combo.addItems(self.font_manager.fonts.keys())

    def choose_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self.color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")

    def add_text_to_template(self):
        """添加文字到模板"""
        text = self.text_input.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "警告", "请输入文字内容")
            return
        
        font_name = self.font_combo.currentText()
        font_path = self.font_manager.get_font_path(font_name)
        font_size = self.font_size.value()
        
        self.template_editor.add_text_element(text, font_path, font_size, self.current_color)
        self.text_input.clear()

    def change_aspect_ratio(self, ratio):
        """改变画布比例"""
        self.template_editor.set_aspect_ratio(ratio)

    def choose_bg_color(self):
        """选择背景颜色"""
        color = QColorDialog.getColor(self.template_editor.current_bg_color, self)
        if color.isValid():
            self.template_editor.set_background_color(color)
            self.bg_color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")

    def toggle_4_3_guide(self):
        """切换4:3参考线"""
        self.template_editor.show_4_3_guide = self.show_4_3_guide_btn.isChecked()
        self.template_editor.update_canvas_border()

    def toggle_edit_mode(self):
        """切换编辑模式"""
        self.template_editor.edit_mode = self.edit_mode_btn.isChecked()

    def delete_selected_elements(self):
        """删除选中元素"""
        self.template_editor.remove_selected_elements()

    def undo_action(self):
        """撤销操作"""
        self.template_editor.undo()

    def redo_action(self):
        """重做操作"""
        self.template_editor.redo()

    def new_template(self):
        """新建模板"""
        reply = QMessageBox.question(self, "新建模板", "确定要新建模板吗？当前未保存的更改将丢失。",
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.template_editor.clear_all_elements()
            self.template_editor.template = CoverTemplate()
            self.template_editor.template.width = 800
            self.template_editor.template.height = 450
            self.template_editor.template.aspect_ratio = "16:9"
            self.template_editor.set_aspect_ratio("16:9")
            self.template_editor.undo_stack.clear()
            self.template_editor.redo_stack.clear()
            self.template_editor.update_undo_buttons()

    def save_template(self):
        """保存模板"""
        file_path, _ = QFileDialog.getSaveFileName(self, "保存模板", "", "模板文件 (*.json)")
        if file_path:
            try:
                template_data = {
                    'width': self.template_editor.template.width,
                    'height': self.template_editor.template.height,
                    'aspect_ratio': self.template_editor.template.aspect_ratio,
                    'background_image': self.template_editor.template.background_image,
                    'elements': self.template_editor.template.elements
                }
                
                # 处理相对路径
                if template_data['background_image']:
                    try:
                        template_data['background_image'] = os.path.relpath(template_data['background_image'], os.path.dirname(file_path))
                    except ValueError:
                        pass
                
                for element in template_data.get('elements', []):
                    if element.get('type') == 'image' and element.get('image_path'):
                        try:
                            element['image_path'] = os.path.relpath(element['image_path'], os.path.dirname(file_path))
                        except ValueError:
                            pass
                
                import json
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=4, ensure_ascii=False)
                self.statusBar().showMessage(f"模板已保存: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存模板失败: {str(e)}")

    def load_template(self):
        """加载模板"""
        file_path, _ = QFileDialog.getOpenFileName(self, "加载模板", "", "模板文件 (*.json)")
        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                self.template_editor.template = CoverTemplate(
                    template_data['width'], template_data['height']
                )
                self.template_editor.template.aspect_ratio = template_data['aspect_ratio']
                self.template_editor.template.background_image = template_data['background_image']
                self.template_editor.template.elements = template_data['elements']
                
                self.ratio_combo.setCurrentText(template_data['aspect_ratio'])
                
                #绝对路径
                if template_data['background_image']:
                    if not os.path.isabs(template_data['background_image']):
                        template_data['background_image'] = os.path.join(os.path.dirname(file_path), template_data['background_image'])
                
                for element in template_data.get('elements', []):
                    if element.get('type') == 'image' and element.get('image_path'):
                        if not os.path.isabs(element['image_path']):
                            element['image_path'] = os.path.join(os.path.dirname(file_path), element['image_path'])
                
                # 设置背景
                if template_data['background_image'] and os.path.exists(template_data['background_image']):
                    self.template_editor.set_background_image(template_data['background_image'])
                    background_info = template_data.get('background_info')
                    if (background_info and self.template_editor.background_item and 
                        isinstance(self.template_editor.background_item, MovableImageItem)):
                        self.template_editor.background_item.setPos(*background_info['position'])
                        self.template_editor.background_item.current_scale = background_info['scale']
                        if background_info['scale'] != 1.0:
                            from PyQt5.QtGui import QTransform
                            transform = QTransform().scale(background_info['scale'], background_info['scale'])
                            self.template_editor.background_item.setTransform(transform)
                
                self.template_editor.load_template_elements(template_data['elements'])
                self.layer_manager.update_layers()
                self.template_editor.undo_stack.clear()
                self.template_editor.redo_stack.clear()
                self.statusBar().showMessage(f"模板已加载: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载模板失败: {str(e)}")

    def export_cover(self):
        """导出封面"""
        ###############如果你选择了元素那么这个框也会保存进去#############
        ###############懒得改了TAT o(TヘTo)#############################
        file_path, _ = QFileDialog.getSaveFileName(self, "导出封面", "", "PNG图片 (*.png)")
        if file_path:
            try:
                if file_path.lower().endswith('.png'):
                    success = self.template_editor.render_to_png(file_path)
                else:
                    self.template_editor.template.render(file_path, 'jpg')
                    success = True
                
                if success:
                    self.statusBar().showMessage(f"封面已导出: {file_path}")
                else:
                    QMessageBox.critical(self, "错误", "导出封面失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出封面失败: {str(e)}")

    def set_background_from_library(self):
        """从素材设置背景"""
        current_item = self.image_library.image_list.currentItem()
        if current_item:
            image_path = current_item.data(Qt.UserRole)
            if image_path and os.path.exists(image_path):
                self.template_editor.set_background_image(image_path)

    def add_foreground_image(self):
        """添加前景图片"""
        current_item = self.image_library.image_list.currentItem()
        if current_item:
            image_path = current_item.data(Qt.UserRole)
            if image_path and os.path.exists(image_path):
                self.template_editor.add_image_element(image_path)

    def replace_selected_image(self):
        """替换选中图片"""
        current_item = self.image_library.image_list.currentItem()
        if current_item:
            image_path = current_item.data(Qt.UserRole)
            if image_path and os.path.exists(image_path):
                success = self.template_editor.replace_selected_image(image_path)
                if not success:
                    QMessageBox.information(self, "提示", "请先选中要替换的图片元素")

    def use_selected_image(self, item):
        """使用选中图片"""
        image_path = item.data(Qt.UserRole)
        if image_path and os.path.exists(image_path):
            self.template_editor.add_image_element(image_path)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

"""
模块
"""
import os
import json
from PyQt5.QtWidgets import (QDockWidget, QListWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QListWidget, QPushButton, QGroupBox, QComboBox,
                             QTreeWidget, QTreeWidgetItem, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QIcon


class LayerManager(QDockWidget):
    """图层管理器 - 管理元素的图层顺序"""
    def __init__(self, template_editor):
        super().__init__("图层管理")
        self.template_editor = template_editor
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.layer_list = QListWidget()
        self.layer_list.setDragDropMode(QListWidget.InternalMove)
        self.layer_list.itemChanged.connect(self.on_item_changed)
        self.layer_list.itemSelectionChanged.connect(self.on_layer_selection_changed)
        
        layout.addWidget(QLabel("图层顺序（从上到下）:"))
        layout.addWidget(self.layer_list)
        
        # 图层操作按钮
        button_layout = QHBoxLayout()
        self.move_up_btn = QPushButton("上移")
        self.move_up_btn.clicked.connect(self.move_up)
        button_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("下移")
        self.move_down_btn.clicked.connect(self.move_down)
        button_layout.addWidget(self.move_down_btn)
        
        self.move_top_btn = QPushButton("置顶")
        self.move_top_btn.clicked.connect(self.move_to_top)
        button_layout.addWidget(self.move_top_btn)
        
        self.move_bottom_btn = QPushButton("置底")
        self.move_bottom_btn.clicked.connect(self.move_to_bottom)
        button_layout.addWidget(self.move_bottom_btn)
        layout.addLayout(button_layout)
        
        # 刷新按钮
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("刷新图层")
        self.refresh_btn.clicked.connect(self.update_layers)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)

    def update_layers(self):
        """更新图层列表显示"""
        try:
            self.layer_list.clear()
            all_items = []
            
            # 收集文字项
            for text_id, text_item in list(self.template_editor.text_items.items()):
                try:
                    if text_item and text_item.scene() is not None:
                        all_items.append((text_item.zValue(), text_id, "文字", text_item))
                    else:
                        del self.template_editor.text_items[text_id]
                except:
                    if text_id in self.template_editor.text_items:
                        del self.template_editor.text_items[text_id]
            
            # 收集图片项
            for image_id, image_item in list(self.template_editor.image_items.items()):
                try:
                    if image_item and image_item.scene() is not None:
                        all_items.append((image_item.zValue(), image_id, "图片", image_item))
                    else:
                        del self.template_editor.image_items[image_id]
                except:
                    if image_id in self.template_editor.image_items:
                        del self.template_editor.image_items[image_id]
            
            # 收集背景项
            if self.template_editor.background_item:
                try:
                    if self.template_editor.background_item.scene() is not None:
                        self.template_editor.background_item.setZValue(-1)
                        all_items.append((-1, "background", "背景", self.template_editor.background_item))
                    else:
                        self.template_editor.background_item = None
                except:
                    self.template_editor.background_item = None
            
            # 按z值排序
            all_items.sort(key=lambda x: x[0], reverse=True)
            
            # 添加到列表
            for z_value, item_id, item_type, item in all_items:
                try:
                    if item_type == "文字":
                        text_content = item.toPlainText()
                        if len(text_content) > 20:
                            text_content = text_content[:20] + "..."
                        item_text = f"{item_type}: {text_content}"
                    elif item_type == "图片":
                        image_path = ""
                        for element in self.template_editor.template.elements:
                            if element['id'] == item_id:
                                image_path = element.get('image_path', item_id)
                                break
                        if image_path:
                            item_text = f"{item_type}: {os.path.basename(image_path)}"
                        else:
                            item_text = f"{item_type}: {item_id}"
                    elif item_type == "背景":
                        if self.template_editor.template.background_image:
                            item_text = f"{item_type}: {os.path.basename(self.template_editor.template.background_image)}"
                        else:
                            item_text = f"{item_type}: 纯色背景"
                    
                    list_item = QListWidgetItem(item_text)
                    list_item.setData(Qt.UserRole, (item_id, item_type, item))
                    self.layer_list.addItem(list_item)
                except Exception as e:
                    print(f"添加图层项时出错: {e}")
                    continue
        except Exception as e:
            print(f"更新图层列表时出错: {e}")

    def on_item_changed(self, item):
        """图层项改变时的处理"""
        pass

    def on_layer_selection_changed(self):
        """图层选择改变时同步到画布"""
        try:
            if hasattr(self.template_editor, 'syncing_selection') and self.template_editor.syncing_selection:
                return
            
            self.template_editor.scene.clearSelection()
            current_item = self.layer_list.currentItem()
            if current_item:
                item_id, item_type, item_obj = current_item.data(Qt.UserRole)
                if item_type == "文字":
                    if item_obj and item_obj in self.template_editor.text_items.values():
                        item_obj.setSelected(True)
                elif item_type == "图片":
                    if item_obj and item_obj in self.template_editor.image_items.values():
                        item_obj.setSelected(True)
                elif item_type == "背景":
                    if item_obj and item_obj == self.template_editor.background_item:
                        item_obj.setSelected(True)
        except Exception as e:
            print(f"同步选中时出错: {e}")

    def move_up(self):
        """上移图层"""
        current_row = self.layer_list.currentRow()
        if current_row > 0:
            item = self.layer_list.item(current_row)
            if item:
                item_id, item_type, item_obj = item.data(Qt.UserRole)
                if item_type == "背景":
                    return
            
            item = self.layer_list.takeItem(current_row)
            self.layer_list.insertItem(current_row - 1, item)
            self.layer_list.setCurrentRow(current_row - 1)
            self.update_z_values()

    def move_down(self):
        """下移图层"""
        current_row = self.layer_list.currentRow()
        if current_row < self.layer_list.count() - 1:
            item = self.layer_list.item(current_row)
            if item:
                item_id, item_type, item_obj = item.data(Qt.UserRole)
                if item_type == "背景":
                    return
            
            item = self.layer_list.takeItem(current_row)
            self.layer_list.insertItem(current_row + 1, item)
            self.layer_list.setCurrentRow(current_row + 1)
            self.update_z_values()

    def move_to_top(self):
        """置顶图层"""
        current_row = self.layer_list.currentRow()
        if current_row > 0:
            item = self.layer_list.item(current_row)
            if item:
                item_id, item_type, item_obj = item.data(Qt.UserRole)
                if item_type == "背景":
                    return
                item_obj.setZValue(self.template_editor.get_next_z_value())
            
            item = self.layer_list.takeItem(current_row)
            self.layer_list.insertItem(0, item)
            self.layer_list.setCurrentRow(0)
            self.update_z_values()

    def move_to_bottom(self):
        """置底图层"""
        current_row = self.layer_list.currentRow()
        if current_row < self.layer_list.count() - 1:
            item = self.layer_list.item(current_row)
            if item:
                item_id, item_type, item_obj = item.data(Qt.UserRole)
                if item_type == "背景":
                    return
                item_obj.setZValue(0)
            
            item = self.layer_list.takeItem(current_row)
            insert_row = self.layer_list.count() - 1
            self.layer_list.insertItem(insert_row, item)
            self.layer_list.setCurrentRow(insert_row)
            self.update_z_values()

    def update_z_values(self):
        """更新所有图层的z值"""
        for i in range(self.layer_list.count()):
            item = self.layer_list.item(i)
            if item:
                item_id, item_type, item_obj = item.data(Qt.UserRole)
                if item_type == "背景":
                    item_obj.setZValue(-1)
                else:
                    z_value = 1000 - i
                    item_obj.setZValue(z_value)


class ImageLibrary(QDockWidget):
    """图片资源库 - 管理图片文件夹和图片选择"""
    def __init__(self):
        super().__init__("图片资源库")
        self.folders_data = []
        self.setup_ui()
        self.load_folders_data()

    def setup_ui(self):
        central_widget = QWidget()
        self.setWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 添加文件夹按钮
        self.add_folder_btn = QPushButton("添加图片文件夹（支持多选）")
        self.add_folder_btn.clicked.connect(self.add_multiple_folders)
        layout.addWidget(self.add_folder_btn)
        
        # 文件夹树
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabel("图片分类")
        self.folder_tree.itemDoubleClicked.connect(self.on_folder_double_clicked)
        layout.addWidget(self.folder_tree)
        
        # 图片列表
        layout.addWidget(QLabel("图片列表:"))
        self.image_list = QListWidget()
        self.image_list.itemDoubleClicked.connect(self.on_image_double_clicked)
        layout.addWidget(self.image_list)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.add_bg_btn = QPushButton("设为背景")
        self.add_bg_btn.clicked.connect(self.set_as_background)
        button_layout.addWidget(self.add_bg_btn)
        
        self.add_foreground_btn = QPushButton("添加前景")
        self.add_foreground_btn.clicked.connect(self.add_as_foreground)
        button_layout.addWidget(self.add_foreground_btn)
        
        self.replace_btn = QPushButton("替换选中")
        self.replace_btn.clicked.connect(self.replace_selected)
        button_layout.addWidget(self.replace_btn)
        layout.addLayout(button_layout)

    def add_multiple_folders(self):
        """添加多个图片文件夹"""
        from dialogs import MultiFolderDialog
        dialog = MultiFolderDialog(self)
        if dialog.exec_() == dialog.Accepted:
            folders = dialog.get_selected_folders()
            for folder_path, category_name in folders:
                self.add_folder(folder_path, category_name)
            self.save_folders_data()

    def add_folder(self, folder_path, category_name):
        """添加单个文件夹"""
        if not os.path.exists(folder_path):
            return
        
        # 检查是否已存在
        for folder_data in self.folders_data:
            if folder_data['path'] == folder_path:
                return
        
        self.folders_data.append({
            'path': folder_path,
            'category': category_name
        })
        self.refresh_folder_tree()

    def refresh_folder_tree(self):
        """刷新文件夹树"""
        self.folder_tree.clear()
        
        # 按分类组织
        categories = {}
        for folder_data in self.folders_data:
            category = folder_data['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(folder_data)
        
        # 添加到树中
        for category, folders in categories.items():
            category_item = QTreeWidgetItem([category])
            self.folder_tree.addTopLevelItem(category_item)
            
            for folder_data in folders:
                folder_name = os.path.basename(folder_data['path'])
                folder_item = QTreeWidgetItem([folder_name])
                folder_item.setData(0, Qt.UserRole, folder_data)
                category_item.addChild(folder_item)

    def on_folder_double_clicked(self, item, column):
        """文件夹双击事件"""
        if item.parent():
            folder_data = item.data(0, Qt.UserRole)
            if folder_data:
                self.load_images_from_folder(folder_data['path'])

    def load_images_from_folder(self, folder_path):
        """从文件夹加载图片"""
        self.image_list.clear()
        if not os.path.exists(folder_path):
            return
        
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'}
        for filename in os.listdir(folder_path):
            if os.path.splitext(filename.lower())[1] in image_extensions:
                item = QListWidgetItem(filename)
                item.setData(Qt.UserRole, os.path.join(folder_path, filename))
                self.image_list.addItem(item)

    def on_image_double_clicked(self, item):
        """图片双击事件"""
        image_path = item.data(Qt.UserRole)
        if image_path and os.path.exists(image_path):
            self.use_image(image_path)

    def use_image(self, image_path):
        """使用图片"""
     #这个方法会被主窗口重写
        pass

    def set_as_background(self):
        """设为背景"""
        current_item = self.image_list.currentItem()
        if current_item:
            image_path = current_item.data(Qt.UserRole)
            if image_path and os.path.exists(image_path):
                self.use_image_as_background(image_path)

    def add_as_foreground(self):
        """添加为前景"""
        current_item = self.image_list.currentItem()
        if current_item:
            image_path = current_item.data(Qt.UserRole)
            if image_path and os.path.exists(image_path):
                self.use_image_as_foreground(image_path)

    def replace_selected(self):
        """替换选中的图片"""
        current_item = self.image_list.currentItem()
        if current_item:
            image_path = current_item.data(Qt.UserRole)
            if image_path and os.path.exists(image_path):
                self.replace_selected_image(image_path)

    def use_image_as_background(self, image_path):
        """使用图片作为背景"""
        pass  # 由主窗口实现

    def use_image_as_foreground(self, image_path):
        """使用图片作为前景"""
        pass  #同上

    def replace_selected_image(self, image_path):
        """替换选中的图片"""
        pass  #+1

    def save_folders_data(self):
        """保存文件夹数据"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), 'folders_config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.folders_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存文件夹配置失败: {e}")

    def load_folders_data(self):
        """加载文件夹数据"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), 'folders_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.folders_data = json.load(f)
                self.refresh_folder_tree()
        except Exception as e:
            print(f"加载文件夹配置失败: {e}")


class FontManager:
    """字体管理器 - 管理字体文件和配置"""
    def __init__(self):
        self.fonts = {}
        self.config_file = os.path.join(os.path.dirname(__file__), 'fonts_config.json')
        self.load_basic_fonts()
        self.load_fonts_config()

    def load_basic_fonts(self):
        """加载基础字体"""
        self.fonts["默认字体"] = ""
        self.fonts["Arial"] = "Arial"

    def add_font(self, name, path):
        """添加字体"""
        self.fonts[name] = path
        self.save_fonts_config()

    def get_font_path(self, name):
        """获取字体路径"""
        return self.fonts.get(name, "")

    def save_fonts_config(self):
        """保存字体配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.fonts, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存字体配置失败: {e}")

    def load_fonts_config(self):
        """加载字体配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_fonts = json.load(f)
                    for name, path in saved_fonts.items():
                        if not path or os.path.exists(path):
                            self.fonts[name] = path
                        else:
                            print(f"字体文件不存在，跳过: {name} -> {path}")
        except Exception as e:
            print(f"加载字体配置失败: {e}")

    def remove_font(self, name):
        """移除字体"""
        if name in self.fonts:
            del self.fonts[name]
            self.save_fonts_config()

import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QListWidget, QComboBox,
                             QFontComboBox, QSpinBox, QColorDialog, QFileDialog, QMessageBox,
                             QTabWidget, QSplitter, QGraphicsView, QGraphicsScene, QToolBar,
                             QStatusBar, QAction, QDockWidget, QTextEdit, QGroupBox, QTreeWidget,
                             QTreeWidgetItem, QDialog, QDialogButtonBox, QFormLayout, QInputDialog,
                             QGraphicsTextItem, QGraphicsRectItem, QGraphicsPixmapItem, QSizePolicy, QListWidgetItem,
                             QMenu, QToolButton)
from PyQt5.QtCore import Qt, QRectF, QSize, QPointF, QTimer
from PyQt5.QtGui import QFont, QColor, QPixmap, QImage, QPainter, QIcon, QPainterPath, QBrush, QPen, QTransform, QFontDatabase
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("错误：缺少PIL库，请安装Pillow：pip install Pillow")
    sys.exit(1)
class AddFontDialog(QDialog):
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
        self.font_file = QLineEdit()
        self.font_file.setReadOnly(True)
        form_layout.addRow("字体文件:", self.font_file)
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
            self.font_file.setText(file_path)
            if not self.font_name.text():
                font_name = os.path.splitext(os.path.basename(file_path))[0]
                self.font_name.setText(font_name)
class TextEditDialog(QDialog):
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
        content_layout = QHBoxLayout()
        content_layout.addWidget(QLabel("文字内容:"))
        self.text_input = QTextEdit()
        self.text_input.setMaximumHeight(80)
        content_layout.addWidget(self.text_input)
        layout.addLayout(content_layout)
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
        """加载当前文字设置"""
        if self.text_item:
            self.text_input.setPlainText(self.text_item.toPlainText())
            current_font = self.text_item.font()
            font_family = current_font.family()
            font_size = current_font.pointSize()
            self.font_size.setValue(font_size)
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
        """添加新字体"""
        dialog = AddFontDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            font_name = dialog.font_name.text()
            font_path = dialog.font_file.text()
            if font_name and font_path and os.path.exists(font_path):
                self.font_manager.add_font(font_name, font_path)
                self.font_combo.addItem(font_name)
                self.font_combo.setCurrentText(font_name)
                if hasattr(self.parent(), 'update_font_combo'):
                    self.parent().update_font_combo()
    def choose_color(self):
        """选择颜色"""
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
            self.update_color_button()
    def update_color_button(self):
        """更新颜色按钮显示"""
        self.color_btn.setStyleSheet(f"background-color: {self.current_color.name()}; border: 1px solid black;")
    def get_text_data(self):
        """获取编辑后的文字数据"""
        return {
            'text': self.text_input.toPlainText(),
            'font_name': self.font_combo.currentText(),
            'font_size': self.font_size.value(),
            'color': self.current_color
        }
class MultiFolderDialog(QDialog):
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
class CoverTemplate:
    def __init__(self, width=800, height=600):
        self.elements = []
        self.background_image = None
        self.foreground_images = []
        self.width = width
        self.height = height
        self.aspect_ratio = "16:9"
    def add_text_element(self, id, text, font_path, font_size, color, position, max_width, alignment="left", scale=1.0):
        for i, element in enumerate(self.elements):
            if element['id'] == id:
                self.elements[i] = {
                    'id': id,
                    'type': 'text',
                    'text': text,
                    'font_path': font_path,
                    'font_size': font_size,
                    'color': color,
                    'position': position,
                    'max_width': max_width,
                    'alignment': alignment,
                    'scale': scale
                }
                return
        element = {
            'id': id,
            'type': 'text',
            'text': text,
            'font_path': font_path,
            'font_size': font_size,
            'color': color,
            'position': position,
            'max_width': max_width,
            'alignment': alignment,
            'scale': scale
        }
        self.elements.append(element)
    def add_image_element(self, id, image_path, position, size, scale=1.0):
        for i, element in enumerate(self.elements):
            if element['id'] == id:
                self.elements[i] = {
                    'id': id,
                    'type': 'image',
                    'image_path': image_path,
                    'position': position,
                    'size': size,
                    'scale': scale
                }
                return
        element = {
            'id': id,
            'type': 'image',
            'image_path': image_path,
            'position': position,
            'size': size,
            'scale': scale
        }
        self.elements.append(element)
    def set_background(self, image_path):
        self.background_image = image_path
    def remove_element(self, element_id):
        self.elements = [e for e in self.elements if e['id'] != element_id]
    def render(self, output_path, file_format='jpg', text_data=None, image_data=None):
        if self.background_image and os.path.exists(self.background_image):
            img = Image.open(self.background_image)
            img = img.resize((self.width, self.height), Image.Resampling.LANCZOS)
            if file_format == 'jpg':
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
            else:
                if img.mode not in ['RGB', 'RGBA']:
                    img = img.convert('RGBA')
        else:
            if file_format == 'jpg':
                img = Image.new('RGB', (self.width, self.height), color='white')
            else:
                img = Image.new('RGBA', (self.width, self.height), color=(255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        for element in self.elements:
            if element['type'] == 'text':
                text = element['text']
                if text_data and element['id'] in text_data:
                    text = text_data[element['id']]
                try:
                    if os.path.exists(element['font_path']):
                        scale = element.get('scale', 1.0)
                        scaled_font_size = int(element['font_size'] * scale)
                        font = ImageFont.truetype(element['font_path'], scaled_font_size)
                    else:
                        font = ImageFont.load_default()
                except:
                    font = ImageFont.load_default()
                color = tuple(element['color'][:3])
                position = tuple(element['position'])
                draw.text(position, text, font=font, fill=color)
            elif element['type'] == 'image':
                if os.path.exists(element['image_path']):
                    try:
                        element_img = Image.open(element['image_path'])
                        new_size = (int(element_img.width * element['scale']), 
                                  int(element_img.height * element['scale']))
                        element_img = element_img.resize(new_size, Image.Resampling.LANCZOS)
                        x, y = element['position']
                        if file_format == 'jpg':
                            if element_img.mode == 'RGBA':
                                element_bg = Image.new('RGB', element_img.size, (255, 255, 255))
                                element_bg.paste(element_img, mask=element_img.split()[-1])
                                element_img = element_bg
                            elif element_img.mode != 'RGB':
                                element_img = element_img.convert('RGB')
                            img.paste(element_img, (int(x), int(y)))
                        else:
                            if element_img.mode == 'RGBA':
                                img.paste(element_img, (int(x), int(y)), element_img)
                            else:
                                if element_img.mode != 'RGB':
                                    element_img = element_img.convert('RGB')
                                img.paste(element_img, (int(x), int(y)))
                    except Exception as e:
                        print(f"处理图片元素时出错: {e}")
                        pass
        img.save(output_path, quality=95)
class MovableTextItem(QGraphicsTextItem):
    def __init__(self, text, font, parent=None):
        super().__init__(text, parent)
        self.setFont(font)
        self.setFlags(QGraphicsTextItem.ItemIsMovable | 
                     QGraphicsTextItem.ItemIsSelectable |
                     QGraphicsTextItem.ItemIsFocusable)
        self.current_scale = 1.0
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            if hasattr(view, 'text_position_changed'):
                view.text_position_changed(self)
            if hasattr(view, 'movement_saved'):
                view.movement_saved = False
    def mouseDoubleClickEvent(self, event):
        """双击打开编辑对话框"""
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            if hasattr(view, 'edit_text_item'):
                view.edit_text_item(self)
    def contextMenuEvent(self, event):
        """右键菜单"""
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            if hasattr(view, 'show_text_context_menu'):
                scene_pos = event.scenePos()
                global_pos = view.mapToGlobal(view.mapFromScene(scene_pos))
                view.show_text_context_menu(self, global_pos)
    def wheelEvent(self, event):
        try:
            if event.modifiers() & Qt.ControlModifier:
                delta = event.angleDelta().y()
                if delta == 0:
                    super().wheelEvent(event)
                    return
                base_scale = 1.02
                speed_factor = min(abs(delta) / 120.0, 3.0)
                scale_factor = base_scale ** speed_factor if delta > 0 else (1.0 / base_scale) ** speed_factor
                new_scale = self.current_scale * scale_factor
                if 0.1 <= new_scale <= 10.0:
                    self.current_scale = new_scale
                    transform = QTransform().scale(self.current_scale, self.current_scale)
                    self.setTransform(transform)
                    if self.scene() and self.scene().views():
                        view = self.scene().views()[0]
                        if hasattr(view, 'text_scale_changed'):
                            try:
                                view.text_scale_changed(self, self.current_scale)
                            except Exception as e:
                                print(f"通知父视图文字缩放改变时出错: {e}")
                    print(f"文字缩放至: {self.current_scale:.3f}倍 (缩放因子: {scale_factor:.3f})")
                    event.accept()
                else:
                    print(f"文字缩放超出范围: {new_scale:.2f}")
                    event.ignore()
            else:
                super().wheelEvent(event)
        except Exception as e:
            print(f"文字wheelEvent处理时出错: {e}")
            try:
                super().wheelEvent(event)
            except:
                event.ignore()
class MovableImageItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, parent=None):
        super().__init__(pixmap, parent)
        self.setFlags(QGraphicsPixmapItem.ItemIsMovable | 
                     QGraphicsPixmapItem.ItemIsSelectable |
                     QGraphicsPixmapItem.ItemIsFocusable)
        self.setTransformationMode(Qt.SmoothTransformation)
        self.current_scale = 1.0
        self.is_background = False
    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            if hasattr(view, 'image_position_changed'):
                view.image_position_changed(self)
            if hasattr(view, 'movement_saved'):
                view.movement_saved = False
    def contextMenuEvent(self, event):
        """右键菜单"""
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            if hasattr(view, 'show_image_context_menu'):
                scene_pos = event.scenePos()
                global_pos = view.mapToGlobal(view.mapFromScene(scene_pos))
                view.show_image_context_menu(self, global_pos)
    def wheelEvent(self, event):
        try:
            if self.is_background and self.scene() and self.scene().views():
                view = self.scene().views()[0]
                if hasattr(view, 'edit_mode') and not view.edit_mode:
                    super().wheelEvent(event)
                    return
            if event.modifiers() & Qt.ControlModifier:
                delta = event.angleDelta().y()
                if delta == 0:
                    super().wheelEvent(event)
                    return
                base_scale = 1.02
                speed_factor = min(abs(delta) / 120.0, 3.0)
                scale_factor = base_scale ** speed_factor if delta > 0 else (1.0 / base_scale) ** speed_factor
                new_scale = self.current_scale * scale_factor
                if 0.1 <= new_scale <= 10.0:
                    self.current_scale = new_scale
                    transform = QTransform().scale(self.current_scale, self.current_scale)
                    self.setTransform(transform)
                    if self.scene() and self.scene().views():
                        view = self.scene().views()[0]
                        if hasattr(view, 'image_scale_changed'):
                            try:
                                view.image_scale_changed(self, self.current_scale)
                            except Exception as e:
                                print(f"通知父视图缩放改变时出错: {e}")
                    print(f"图片缩放至: {self.current_scale:.3f}倍 (缩放因子: {scale_factor:.3f})")
                    event.accept()
                else:
                    print(f"缩放超出范围: {new_scale:.2f}")
                    event.ignore()
            else:
                super().wheelEvent(event)
        except Exception as e:
            print(f"wheelEvent处理时出错: {e}")
            try:
                super().wheelEvent(event)
            except:
                event.ignore()
class TemplateEditor(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.template = CoverTemplate()
        self.template.width = 800
        self.template.height = 450
        self.template.aspect_ratio = "16:9"
        self.current_bg_color = Qt.white
        self.setRenderHint(QPainter.Antialiasing)
        self.text_items = {}
        self.image_items = {}
        self.background_item = None
        self.current_category_images = []
        self.border_item = None
        self.ratio_guide_item = None
        self.show_4_3_guide = False
        self.update_canvas_border()
        self.update_background()
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setInteractive(True)
        self.scale_factor = 1.0
        self.min_scale = 0.1
        self.max_scale = 10.0
        self.edit_mode = False
        self.scene.selectionChanged.connect(self.on_selection_changed)
        self.syncing_selection = False
        self.setFocusPolicy(Qt.StrongFocus)
        self.scene.selectionChanged.connect(self.ensure_focus)
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_steps = 50
        self.movement_saved = False
        self.scale_timer = None
        self.template_initial_state = None
        self.scaling_elements = set()
    def get_next_z_value(self):
        """获取下一个可用的Z值，确保新元素在最上层"""
        max_z = 1000
        for item in self.scene.items():
            if hasattr(item, 'zValue'):
                max_z = max(max_z, item.zValue())
        return max_z + 1
    def get_next_text_id(self):
        """获取下一个可用的文字元素ID"""
        max_id = 0
        for text_id in self.text_items.keys():
            if text_id.startswith("text_"):
                try:
                    id_num = int(text_id.split("_")[1])
                    max_id = max(max_id, id_num)
                except (ValueError, IndexError):
                    continue
        return f"text_{max_id + 1}"
    def get_next_image_id(self):
        """获取下一个可用的图片元素ID"""
        max_id = 0
        for image_id in self.image_items.keys():
            if image_id.startswith("image_"):
                try:
                    id_num = int(image_id.split("_")[1])
                    max_id = max(max_id, id_num)
                except (ValueError, IndexError):
                    continue
        return f"image_{max_id + 1}"
    def update_canvas_border(self):
        """更新画布边框，使其可见"""
        try:
            if self.border_item:
                self.scene.removeItem(self.border_item)
            if hasattr(self, 'ratio_guide_item') and self.ratio_guide_item:
                self.scene.removeItem(self.ratio_guide_item)
        except:
            pass
        rect = QRectF(0, 0, self.template.width, self.template.height)
        self.border_item = QGraphicsRectItem(rect)
        self.border_item.setPen(QPen(Qt.black, 2, Qt.DashLine))
        self.border_item.setZValue(1000)
        self.scene.addItem(self.border_item)
        if self.template.aspect_ratio == "16:9" and self.show_4_3_guide:
            self.add_4_3_guide()
    def add_4_3_guide(self):
        """在16:9模式下添加4:3参考框"""
        if hasattr(self, 'ratio_guide_item') and self.ratio_guide_item:
            self.scene.removeItem(self.ratio_guide_item)
            self.ratio_guide_item = None
        canvas_width = self.template.width
        canvas_height = self.template.height
        guide_height = canvas_height
        guide_width = int(guide_height * 4 / 3)
        if guide_width > canvas_width:
            guide_width = canvas_width
            guide_height = int(guide_width * 3 / 4)
        x_offset = (canvas_width - guide_width) / 2
        y_offset = (canvas_height - guide_height) / 2
        guide_rect = QRectF(x_offset, y_offset, guide_width, guide_height)
        self.ratio_guide_item = QGraphicsRectItem(guide_rect)
        pen = QPen(Qt.red, 1, Qt.DashLine)
        pen.setDashPattern([5, 5])
        self.ratio_guide_item.setPen(pen)
        self.ratio_guide_item.setZValue(500)
        self.scene.addItem(self.ratio_guide_item)
    def update_background(self):
        try:
            if self.background_item:
                self.scene.removeItem(self.background_item)
                self.background_item = None
        except:
            self.background_item = None
        rect = QRectF(0, 0, self.template.width, self.template.height)
        self.background_item = QGraphicsRectItem(rect)
        self.background_item.setBrush(QBrush(self.current_bg_color))
        self.background_item.setZValue(-1)
        self.scene.addItem(self.background_item)
        self.template.background_image = None
    def set_background_color(self, color):
        self.current_bg_color = color
        if not self.template.background_image:
            self.update_background()
    def set_background_image(self, image_path):
        if os.path.exists(image_path):
            self.template.set_background(image_path)
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                QMessageBox.warning(self, "错误", "无法加载图片文件")
                return
            if self.background_item:
                self.scene.removeItem(self.background_item)
                self.background_item = None
            self.background_item = MovableImageItem(pixmap)
            self.background_item.is_background = True
            self.background_item.setZValue(-1)
            self.background_item.setFlags(QGraphicsPixmapItem.ItemIsSelectable | 
                                        QGraphicsPixmapItem.ItemIsFocusable)
            x_pos = (self.template.width - pixmap.width()) / 2
            y_pos = (self.template.height - pixmap.height()) / 2
            self.background_item.setPos(x_pos, y_pos)
            self.scene.addItem(self.background_item)
            self.update_canvas_border()
            if hasattr(self, 'layer_manager'):
                self.layer_manager.update_layers()
    def set_aspect_ratio(self, ratio):
        if ratio == "16:9":
            self.template.width = 800
            self.template.height = 450
        else:
            self.template.width = 800
            self.template.height = 600
        self.template.aspect_ratio = ratio
        self.scene.setSceneRect(0, 0, self.template.width, self.template.height)
        self.update_canvas_border()
        if self.template.background_image and os.path.exists(self.template.background_image):
            self.set_background_image(self.template.background_image)
        else:
            self.update_background()
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
    def add_text_element(self, text, font_path, font_size, color):
        if font_path and os.path.exists(font_path):
            font = QFont()
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_families = QFontDatabase.applicationFontFamilies(font_id)
                if font_families:
                    font.setFamily(font_families[0])
                    font.setPointSize(font_size)
                else:
                    font = QFont(font_path, font_size)
            else:
                font = QFont(font_path, font_size)
        else:
            font = QFont(font_path if font_path else "Arial", font_size)
        text_item = MovableTextItem(text, font)
        text_item.setDefaultTextColor(color)
        text_width = text_item.boundingRect().width()
        x_pos = (self.template.width - text_width) / 2
        text_item.setPos(x_pos, 50)
        base_z = self.get_next_z_value()
        text_item.setZValue(base_z)
        self.scene.addItem(text_item)
        text_id = self.get_next_text_id()
        self.text_items[text_id] = text_item
        position = (text_item.pos().x(), text_item.pos().y())
        color_tuple = (color.red(), color.green(), color.blue(), color.alpha())
        self.template.add_text_element(text_id, text, font_path, font_size, color_tuple, position, 0)
        if hasattr(self, 'layer_manager'):
            self.layer_manager.update_layers()
    def add_image_element(self, image_path):
        if not os.path.exists(image_path):
            return
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return
        image_item = MovableImageItem(pixmap)
        x_pos = (self.template.width - pixmap.width()) / 2
        y_pos = (self.template.height - pixmap.height()) / 2
        image_item.setPos(x_pos, y_pos)
        base_z = self.get_next_z_value()
        image_item.setZValue(base_z)
        self.scene.addItem(image_item)
        image_id = self.get_next_image_id()
        self.image_items[image_id] = image_item
        position = (image_item.pos().x(), image_item.pos().y())
        size = (pixmap.width(), pixmap.height())
        self.template.add_image_element(image_id, image_path, position, size, 1.0)
        if hasattr(self, 'layer_manager'):
            self.layer_manager.update_layers()
    def replace_selected_image(self, new_image_path):
        """替换选中的图片"""
        selected_items = self.scene.selectedItems()
        if not selected_items:
            return False
        for item in selected_items:
            if isinstance(item, MovableImageItem):
                if item == self.background_item:
                    if os.path.exists(new_image_path):
                        pixmap = QPixmap(new_image_path)
                        if not pixmap.isNull():
                            current_pos = item.pos()
                            current_scale = item.current_scale
                            item.setPixmap(pixmap)
                            self.template.background_image = new_image_path
                            return True
                else:
                    for image_id, image_item in self.image_items.items():
                        if image_item == item:
                            if os.path.exists(new_image_path):
                                pixmap = QPixmap(new_image_path)
                                if not pixmap.isNull():
                                    image_item.setPixmap(pixmap)
                                    for element in self.template.elements:
                                        if element['id'] == image_id:
                                            element['image_path'] = new_image_path
                                            element['size'] = (pixmap.width(), pixmap.height())
                                            break
                                    return True
        return False
    def remove_selected_elements(self):
        """删除选中的元素"""
        selected_items = self.scene.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            if item == self.background_item:
                continue
            self.scene.removeItem(item)
            if isinstance(item, MovableTextItem):
                for text_id, text_item in self.text_items.items():
                    if text_item == item:
                        del self.text_items[text_id]
                        self.template.remove_element(text_id)
                        break
            elif isinstance(item, MovableImageItem):
                for image_id, image_item in self.image_items.items():
                    if image_item == item:
                        del self.image_items[image_id]
                        self.template.remove_element(image_id)
                        break
        if hasattr(self, 'layer_manager'):
            self.layer_manager.update_layers()
    def text_position_changed(self, text_item):
        """当文本位置改变时更新模板数据"""
        try:
            for text_id, item in self.text_items.items():
                if item == text_item:
                    for element in self.template.elements:
                        if element['id'] == text_id:
                            old_pos = element['position']
                            new_pos = (item.pos().x(), item.pos().y())
                            if old_pos != new_pos:
                                if not self.movement_saved:
                                    self.save_state("move_elements", "移动元素")
                                    self.movement_saved = True
                                element['position'] = new_pos
                            break
                    break
        except Exception as e:
            print(f"更新文本位置数据时出错: {e}")
    def image_position_changed(self, image_item):
        """当图片位置改变时更新模板数据"""
        try:
            for image_id, item in self.image_items.items():
                if item == image_item:
                    for element in self.template.elements:
                        if element['id'] == image_id:
                            old_pos = element['position']
                            new_pos = (item.pos().x(), item.pos().y())
                            if old_pos != new_pos:
                                if not self.movement_saved:
                                    self.save_state("move_elements", "移动元素")
                                    self.movement_saved = True
                                element['position'] = new_pos
                            break
                    break
        except Exception as e:
            print(f"更新图片位置数据时出错: {e}")
    def image_scale_changed(self, image_item, scale):
        """当图片缩放改变时更新模板数据"""
        try:
            for image_id, item in self.image_items.items():
                if item == image_item:
                    for element in self.template.elements:
                        if element['id'] == image_id:
                            old_scale = element.get('scale', 1.0)
                            if abs(old_scale - scale) > 0.001:
                                if image_id not in self.scaling_elements:
                                    import time
                                    timestamp = int(time.time() * 1000)
                                    self.save_state("scale_elements", f"缩放图片元素: {image_id} ({timestamp})")
                                    self.scaling_elements.add(image_id)
                                element['scale'] = scale
                                self.reset_scale_timer()
                            break
                    break
        except Exception as e:
            print(f"更新图片缩放数据时出错: {e}")
    def text_scale_changed(self, text_item, scale):
        """当文字缩放改变时更新模板数据"""
        try:
            for text_id, item in self.text_items.items():
                if item == text_item:
                    for element in self.template.elements:
                        if element['id'] == text_id:
                            old_scale = element.get('scale', 1.0)
                            if abs(old_scale - scale) > 0.001:
                                if text_id not in self.scaling_elements:
                                    import time
                                    timestamp = int(time.time() * 1000)
                                    self.save_state("scale_elements", f"缩放文字元素: {text_id} ({timestamp})")
                                    self.scaling_elements.add(text_id)
                                element['scale'] = scale
                                self.reset_scale_timer()
                            break
                    break
        except Exception as e:
            print(f"更新文字缩放数据时出错: {e}")
    def reset_scale_timer(self):
        """重置缩放定时器，用于检测缩放结束"""
        try:
            if self.scale_timer:
                self.scale_timer.stop()
            self.scale_timer = QTimer()
            self.scale_timer.setSingleShot(True)
            self.scale_timer.timeout.connect(self.on_scale_end)
            self.scale_timer.start(500)
        except Exception as e:
            print(f"设置缩放定时器时出错: {e}")
    def on_scale_end(self):
        """缩放结束时的处理"""
        try:
            self.scaling_elements.clear()
            print("缩放操作结束，清空正在缩放的元素集合")
        except Exception as e:
            print(f"缩放结束处理时出错: {e}")
    def load_template_elements(self, elements):
        """加载模板元素到编辑器"""
        for item in list(self.text_items.values()) + list(self.image_items.values()):
            self.scene.removeItem(item)
        self.text_items.clear()
        self.image_items.clear()
        self.movement_saved = False
        for index, element in enumerate(elements):
            if element['type'] == 'text':
                color = QColor(*element['color'])
                font_path = element['font_path']
                font_size = element['font_size']
                if font_path and os.path.exists(font_path):
                    font = QFont()
                    font_id = QFontDatabase.addApplicationFont(font_path)
                    if font_id != -1:
                        font_families = QFontDatabase.applicationFontFamilies(font_id)
                        if font_families:
                            font.setFamily(font_families[0])
                            font.setPointSize(font_size)
                        else:
                            font = QFont(font_path, font_size)
                    else:
                        font = QFont(font_path, font_size)
                else:
                    font = QFont(font_path if font_path else "Arial", font_size)
                text_item = MovableTextItem(element['text'], font)
                text_item.setDefaultTextColor(color)
                text_item.setPos(*element['position'])
                text_item.current_scale = element.get('scale', 1.0)
                if text_item.current_scale != 1.0:
                    transform = QTransform().scale(text_item.current_scale, text_item.current_scale)
                    text_item.setTransform(transform)
                z_value = 1000 + index
                text_item.setZValue(z_value)
                self.scene.addItem(text_item)
                self.text_items[element['id']] = text_item
            elif element['type'] == 'image':
                if os.path.exists(element['image_path']):
                    pixmap = QPixmap(element['image_path'])
                    if not pixmap.isNull():
                        image_item = MovableImageItem(pixmap)
                        image_item.setPos(*element['position'])
                        image_item.current_scale = element.get('scale', 1.0)
                        if image_item.current_scale != 1.0:
                            transform = QTransform().scale(image_item.current_scale, image_item.current_scale)
                            image_item.setTransform(transform)
                        z_value = 1000 + index
                        image_item.setZValue(z_value)
                        self.scene.addItem(image_item)
                        self.image_items[element['id']] = image_item
        self.update_canvas_border()
        self.template_initial_state = {
            'action_type': 'template_loaded',
            'description': '模板加载完成',
            'timestamp': self.get_timestamp(),
            'elements': self.get_elements_snapshot(),
            'background': self.get_background_snapshot()
        }
        print(f"保存模板初始状态: {len(self.template_initial_state['elements'])} 个元素")
    def wheelEvent(self, event):
        """处理鼠标滚轮事件，支持视图缩放和元素缩放"""
        try:
            selected_items = self.scene.selectedItems()
            image_items = [item for item in selected_items if isinstance(item, MovableImageItem)]
            text_items = [item for item in selected_items if isinstance(item, MovableTextItem)]
            if event.modifiers() & Qt.ControlModifier:
                if image_items or text_items:
                    for image_item in image_items:
                        try:
                            image_item.wheelEvent(event)
                        except Exception as e:
                            print(f"缩放图片元素时出错: {e}")
                    for text_item in text_items:
                        try:
                            text_item.wheelEvent(event)
                        except Exception as e:
                            print(f"缩放文字元素时出错: {e}")
                else:
                    self.zoom_view(event)
            else:
                self.zoom_view(event)
        except Exception as e:
            print(f"wheelEvent处理时出错: {e}")
            try:
                super().wheelEvent(event)
            except:
                event.ignore()
    def zoom_view(self, event):
        """缩放整个视图"""
        try:
            delta = event.angleDelta().y()
            if delta == 0:
                event.ignore()
                return
            base_scale = 1.02
            speed_factor = min(abs(delta) / 120.0, 3.0)
            scale_factor = base_scale ** speed_factor if delta > 0 else (1.0 / base_scale) ** speed_factor
            new_scale = self.scale_factor * scale_factor
            if self.min_scale <= new_scale <= self.max_scale:
                self.scale_factor = new_scale
                self.scale(scale_factor, scale_factor)
                print(f"视图缩放至: {self.scale_factor:.3f}倍 (缩放因子: {scale_factor:.3f})")
                event.accept()
            else:
                print(f"视图缩放超出范围: {new_scale:.2f}")
                event.ignore()
        except Exception as e:
            print(f"视图缩放时出错: {e}")
            try:
                event.ignore()
            except:
                pass
    def set_edit_mode(self, enabled):
        """设置编辑模式（只对背景图片生效）"""
        self.edit_mode = enabled
        if self.background_item and isinstance(self.background_item, MovableImageItem):
            if enabled:
                self.background_item.setFlags(self.background_item.flags() | QGraphicsPixmapItem.ItemIsMovable)
            else:
                self.background_item.setFlags(self.background_item.flags() & ~QGraphicsPixmapItem.ItemIsMovable)
    def edit_text_item(self, text_item):
        """编辑文字项"""
        if not hasattr(self, 'font_manager'):
            return
        dialog = TextEditDialog(text_item, self.font_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            text_data = dialog.get_text_data()
            text_item.setPlainText(text_data['text'])
            font_name = text_data['font_name']
            font_path = self.font_manager.get_font_path(font_name)
            font_size = text_data['font_size']
            if font_path and os.path.exists(font_path):
                font = QFont()
                font_id = QFontDatabase.addApplicationFont(font_path)
                if font_id != -1:
                    font_families = QFontDatabase.applicationFontFamilies(font_id)
                    if font_families:
                        font.setFamily(font_families[0])
                        font.setPointSize(font_size)
                    else:
                        font = QFont(font_path, font_size)
                else:
                    font = QFont(font_path, font_size)
            else:
                font = QFont(font_path if font_path else "Arial", font_size)
            text_item.setFont(font)
            text_item.setDefaultTextColor(text_data['color'])
            for text_id, item in self.text_items.items():
                if item == text_item:
                    for element in self.template.elements:
                        if element['id'] == text_id:
                            element['text'] = text_data['text']
                            element['font_path'] = font_path
                            element['font_size'] = font_size
                            element['color'] = (text_data['color'].red(), text_data['color'].green(), 
                                              text_data['color'].blue(), text_data['color'].alpha())
                            break
                    break
    def show_text_context_menu(self, text_item, position):
        """显示文字右键菜单"""
        menu = QMenu(self)
        edit_action = QAction("编辑文字", self)
        edit_action.triggered.connect(lambda: self.edit_text_item(text_item))
        menu.addAction(edit_action)
        copy_action = QAction("复制", self)
        copy_action.triggered.connect(lambda: self.copy_text_item(text_item))
        menu.addAction(copy_action)
        menu.addSeparator()
        layer_menu = menu.addMenu("图层顺序")
        move_up_action = QAction("上移一层", self)
        move_up_action.triggered.connect(lambda: self.move_text_up(text_item))
        layer_menu.addAction(move_up_action)
        move_down_action = QAction("下移一层", self)
        move_down_action.triggered.connect(lambda: self.move_text_down(text_item))
        layer_menu.addAction(move_down_action)
        move_top_action = QAction("置顶", self)
        move_top_action.triggered.connect(lambda: self.move_text_to_top(text_item))
        layer_menu.addAction(move_top_action)
        move_bottom_action = QAction("置底", self)
        move_bottom_action.triggered.connect(lambda: self.move_text_to_bottom(text_item))
        layer_menu.addAction(move_bottom_action)
        menu.addSeparator()
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_text_item(text_item))
        menu.addAction(delete_action)
        menu.exec_(position)
    def copy_text_item(self, text_item):
        """复制文字项"""
        try:
            text_id = None
            for tid, item in self.text_items.items():
                if item == text_item:
                    text_id = tid
                    break
            if not text_id:
                return
            text = text_item.toPlainText()
            font = text_item.font()
            color = text_item.defaultTextColor()
            scale = text_item.current_scale
            current_pos = text_item.pos()
            new_pos = QPointF(current_pos.x() + 20, current_pos.y() + 20)
            self.save_state("copy_text", f"复制文字: {text[:20]}...")
            new_text_item = MovableTextItem(text, font)
            new_text_item.setDefaultTextColor(color)
            new_text_item.setPos(new_pos)
            new_text_item.current_scale = scale
            if scale != 1.0:
                transform = QTransform().scale(scale, scale)
                new_text_item.setTransform(transform)
            base_z = self.get_next_z_value()
            new_text_item.setZValue(base_z)
            self.scene.addItem(new_text_item)
            new_text_id = self.get_next_text_id()
            self.text_items[new_text_id] = new_text_item
            position = (new_text_item.pos().x(), new_text_item.pos().y())
            color_tuple = (color.red(), color.green(), color.blue(), color.alpha())
            font_path = ""
            for element in self.template.elements:
                if element['id'] == text_id:
                    font_path = element.get('font_path', "")
                    break
            self.template.add_text_element(new_text_id, text, font_path, font.pointSize(), color_tuple, position, 0, scale=scale)
            if hasattr(self, 'layer_manager'):
                self.layer_manager.update_layers()
        except Exception as e:
            print(f"复制文字项时出错: {e}")
    def delete_text_item(self, text_item):
        """删除文字项"""
        reply = QMessageBox.question(
            self, "确认删除", 
            "确定要删除这个文字元素吗？\n此操作无法撤销。", 
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        self.scene.removeItem(text_item)
        for text_id, item in self.text_items.items():
            if item == text_item:
                del self.text_items[text_id]
                self.template.remove_element(text_id)
                break
        if hasattr(self, 'layer_manager'):
            self.layer_manager.update_layers()
    def move_text_up(self, text_item):
        """上移文字一层"""
        current_z = text_item.zValue()
        text_item.setZValue(current_z + 1)
        if hasattr(self, 'layer_manager'):
            self.layer_manager.update_layers()
    def move_text_down(self, text_item):
        """下移文字一层"""
        current_z = text_item.zValue()
        text_item.setZValue(current_z - 1)
        if hasattr(self, 'layer_manager'):
            self.layer_manager.update_layers()
    def move_text_to_top(self, text_item):
        """置顶文字"""
        text_item.setZValue(self.get_next_z_value())
        if hasattr(self, 'layer_manager'):
            self.layer_manager.update_layers()
    def move_text_to_bottom(self, text_item):
        """置底文字"""
        text_item.setZValue(0)
        if hasattr(self, 'layer_manager'):
            self.layer_manager.update_layers()
    def show_image_context_menu(self, image_item, position):
        """显示图片右键菜单"""
        menu = QMenu(self)
        copy_action = QAction("复制", self)
        copy_action.triggered.connect(lambda: self.copy_image_item(image_item))
        menu.addAction(copy_action)
        menu.addSeparator()
        layer_menu = menu.addMenu("图层顺序")
        move_up_action = QAction("上移一层", self)
        move_up_action.triggered.connect(lambda: self.move_image_up(image_item))
        layer_menu.addAction(move_up_action)
        move_down_action = QAction("下移一层", self)
        move_down_action.triggered.connect(lambda: self.move_image_down(image_item))
        layer_menu.addAction(move_down_action)
        move_top_action = QAction("置顶", self)
        move_top_action.triggered.connect(lambda: self.move_image_to_top(image_item))
        layer_menu.addAction(move_top_action)
        move_bottom_action = QAction("置底", self)
        move_bottom_action.triggered.connect(lambda: self.move_image_to_bottom(image_item))
        layer_menu.addAction(move_bottom_action)
        menu.addSeparator()
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(lambda: self.delete_image_item(image_item))
        menu.addAction(delete_action)
        menu.exec_(position)
    def copy_image_item(self, image_item):
        """复制图片项"""
        try:
            image_id = None
            for iid, item in self.image_items.items():
                if item == image_item:
                    image_id = iid
                    break
            if not image_id:
                return
            pixmap = image_item.pixmap()
            scale = image_item.current_scale
            current_pos = image_item.pos()
            new_pos = QPointF(current_pos.x() + 20, current_pos.y() + 20)
            self.save_state("copy_image", f"复制图片: {image_id}")
            new_image_item = MovableImageItem(pixmap)
            new_image_item.setPos(new_pos)
            new_image_item.current_scale = scale
            if scale != 1.0:
                transform = QTransform().scale(scale, scale)
                new_image_item.setTransform(transform)
            base_z = self.get_next_z_value()
            new_image_item.setZValue(base_z)
            self.scene.addItem(new_image_item)
            new_image_id = self.get_next_image_id()
            self.image_items[new_image_id] = new_image_item
            position = (new_image_item.pos().x(), new_image_item.pos().y())
            size = (pixmap.width(), pixmap.height())
            image_path = ""
            for element in self.template.elements:
                if element['id'] == image_id:
                    image_path = element.get('image_path', "")
                    break
            self.template.add_image_element(new_image_id, image_path, position, size, scale)
            if hasattr(self, 'layer_manager'):
                self.layer_manager.update_layers()
        except Exception as e:
            print(f"复制图片项时出错: {e}")
    def move_image_up(self, image_item):
        """上移图片一层"""
        current_z = image_item.zValue()
        image_item.setZValue(current_z + 1)
        if hasattr(self, 'layer_manager'):
            self.layer_manager.update_layers()
    def move_image_down(self, image_item):
        """下移图片一层"""
        current_z = image_item.zValue()
        image_item.setZValue(current_z - 1)
        if hasattr(self, 'layer_manager'):
            self.layer_manager.update_layers()
    def move_image_to_top(self, image_item):
        """置顶图片"""
        image_item.setZValue(self.get_next_z_value())
        if hasattr(self, 'layer_manager'):
            self.layer_manager.update_layers()
    def move_image_to_bottom(self, image_item):
        """置底图片"""
        image_item.setZValue(0)
        if hasattr(self, 'layer_manager'):
            self.layer_manager.update_layers()
    def delete_image_item(self, image_item):
        """删除图片项"""
        reply = QMessageBox.question(
            self, "确认删除", 
            "确定要删除这个图片元素吗？\n此操作无法撤销。", 
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        self.scene.removeItem(image_item)
        for image_id, item in self.image_items.items():
            if item == image_item:
                del self.image_items[image_id]
                self.template.remove_element(image_id)
                break
        if hasattr(self, 'layer_manager'):
            self.layer_manager.update_layers()
    def on_selection_changed(self):
        """当场景选择改变时，同步更新图层管理面板的选中状态"""
        try:
            if not hasattr(self, 'layer_manager') or not self.layer_manager:
                return
            if self.syncing_selection:
                return
            selected_items = self.scene.selectedItems()
            if not selected_items:
                self.layer_manager.layer_list.clearSelection()
                return
            selected_item = selected_items[0]
            for i in range(self.layer_manager.layer_list.count()):
                list_item = self.layer_manager.layer_list.item(i)
                if list_item:
                    item_id, item_type, item_obj = list_item.data(Qt.UserRole)
                    if item_obj == selected_item:
                        self.syncing_selection = True
                        self.layer_manager.layer_list.setCurrentRow(i)
                        self.syncing_selection = False
                        break
        except Exception as e:
            print(f"同步图层选择时出错: {e}")
            self.syncing_selection = False
    def ensure_focus(self):
        """确保模板编辑器获得焦点，以便接收键盘事件"""
        self.setFocus()
        selected_items = self.scene.selectedItems()
        if selected_items:
            count = len(selected_items)
            self.update_status_message(f"已选中 {count} 个元素 - 使用方向键进行1像素微调")
        else:
            self.update_status_message("就绪 - 提示：选中元素后可使用方向键进行1像素微调")
    def update_status_message(self, message):
        """更新状态栏消息"""
        try:
            main_window = self.window()
            if main_window and hasattr(main_window, 'statusBar'):
                main_window.statusBar().showMessage(message)
        except Exception as e:
            print(f"更新状态栏消息时出错: {e}")
    def save_state(self, action_type, description=""):
        """保存当前状态到撤销栈"""
        try:
            state = {
                'action_type': action_type,
                'description': description,
                'timestamp': self.get_timestamp(),
                'elements': self.get_elements_snapshot(),
                'background': self.get_background_snapshot()
            }
            if self.undo_stack and self.states_are_same(self.undo_stack[-1], state):
                print(f"跳过重复状态: {description}")
                return
            self.undo_stack.append(state)
            if len(self.undo_stack) > self.max_undo_steps:
                self.undo_stack.pop(0)
            self.redo_stack.clear()
            self.update_undo_buttons()
            print(f"保存状态: {description}, 撤销栈大小: {len(self.undo_stack)}")
        except Exception as e:
            print(f"保存状态时出错: {e}")
    def states_are_same(self, state1, state2):
        """比较两个状态是否相同"""
        try:
            if len(state1['elements']) != len(state2['elements']):
                return False
            if state1['background'] != state2['background']:
                return False
            for i, elem1 in enumerate(state1['elements']):
                elem2 = state2['elements'][i]
                if (elem1['type'] != elem2['type'] or 
                    elem1['pos'] != elem2['pos'] or
                    elem1['z_value'] != elem2['z_value']):
                    return False
                if elem1['type'] == 'text':
                    if (elem1['text'] != elem2['text'] or 
                        elem1['scale'] != elem2['scale']):
                        return False
                elif elem1['type'] == 'image':
                    if (elem1['scale'] != elem2['scale'] or
                        elem1['pixmap_path'] != elem2['pixmap_path']):
                        return False
            return True
        except:
            return False
    def get_timestamp(self):
        """获取当前时间戳"""
        import time
        return time.time()
    def get_elements_snapshot(self):
        """获取元素快照"""
        elements = []
        for text_id, text_item in self.text_items.items():
            if text_item and text_item.scene() is not None:
                elements.append({
                    'type': 'text',
                    'id': text_id,
                    'text': text_item.toPlainText(),
                    'pos': (text_item.pos().x(), text_item.pos().y()),
                    'font': text_item.font(),
                    'color': text_item.defaultTextColor(),
                    'scale': text_item.current_scale,
                    'z_value': text_item.zValue()
                })
        for image_id, image_item in self.image_items.items():
            if image_item and image_item.scene() is not None:
                elements.append({
                    'type': 'image',
                    'id': image_id,
                    'pos': (image_item.pos().x(), image_item.pos().y()),
                    'scale': image_item.current_scale,
                    'z_value': image_item.zValue(),
                    'pixmap_path': self.get_image_path_from_element(image_id)
                })
        return elements
    def get_background_snapshot(self):
        """获取背景快照"""
        if self.background_item:
            if isinstance(self.background_item, MovableImageItem):
                return {
                    'type': 'image',
                    'pos': (self.background_item.pos().x(), self.background_item.pos().y()),
                    'scale': self.background_item.current_scale,
                    'image_path': self.template.background_image
                }
            else:
                return {
                    'type': 'color',
                    'color': self.current_bg_color
                }
        return None
    def get_image_path_from_element(self, image_id):
        """从模板元素中获取图片路径"""
        for element in self.template.elements:
            if element['id'] == image_id:
                return element.get('image_path', '')
        return ''
    def undo(self):
        """撤销操作"""
        try:
            if not self.undo_stack:
                self.update_status_message("没有可撤销的操作")
                return
            print(f"撤销前 - 撤销栈大小: {len(self.undo_stack)}")
            current_state = {
                'action_type': 'current',
                'description': 'current state',
                'timestamp': self.get_timestamp(),
                'elements': self.get_elements_snapshot(),
                'background': self.get_background_snapshot()
            }
            self.redo_stack.append(current_state)
            state = self.undo_stack.pop()
            print(f"撤销: {state['description']}, 撤销后栈大小: {len(self.undo_stack)}")
            if self.undo_stack:
                prev_state = self.undo_stack[-1]
                self.restore_state(prev_state)
            else:
                self.restore_template_state()
            self.update_undo_buttons()
            self.update_status_message(f"已撤销: {state['description']}")
        except Exception as e:
            print(f"撤销操作时出错: {e}")
    def restore_empty_state(self):
        """恢复到空状态（没有任何元素）"""
        try:
            self.clear_all_elements()
            self.template.background_type = "color"
            self.template.background_color = QColor(255, 255, 255)
            self.template.background_image = None
            self.set_background_color(QColor(255, 255, 255))
            print("恢复到空状态")
        except Exception as e:
            print(f"恢复空状态时出错: {e}")
    def restore_template_state(self):
        """恢复到模板加载时的初始状态"""
        try:
            if self.template_initial_state:
                self.restore_state(self.template_initial_state)
                print("恢复到模板加载时的状态")
            else:
                self.restore_empty_state()
                print("没有模板初始状态，恢复到空状态")
        except Exception as e:
            print(f"恢复模板状态时出错: {e}")
    def redo(self):
        """重做操作"""
        try:
            if not self.redo_stack:
                self.update_status_message("没有可重做的操作")
                return
            state = self.redo_stack.pop()
            current_state = {
                'action_type': 'current',
                'description': 'current state',
                'timestamp': self.get_timestamp(),
                'elements': self.get_elements_snapshot(),
                'background': self.get_background_snapshot()
            }
            self.undo_stack.append(current_state)
            self.restore_state(state)
            self.update_undo_buttons()
            self.update_status_message(f"已重做: {state['description']}")
        except Exception as e:
            print(f"重做操作时出错: {e}")
    def restore_state(self, state):
        """恢复状态"""
        try:
            self.clear_all_elements()
            self.template.elements.clear()
            if state['background']:
                if state['background']['type'] == 'image':
                    self.template.background_image = state['background']['image_path']
                    if os.path.exists(state['background']['image_path']):
                        self.set_background_image(state['background']['image_path'])
                        if self.background_item and isinstance(self.background_item, MovableImageItem):
                            self.background_item.setPos(*state['background']['pos'])
                            self.background_item.current_scale = state['background']['scale']
                            if state['background']['scale'] != 1.0:
                                transform = QTransform().scale(state['background']['scale'], state['background']['scale'])
                                self.background_item.setTransform(transform)
                elif state['background']['type'] == 'color':
                    self.set_background_color(state['background']['color'])
            for element_data in state['elements']:
                if element_data['type'] == 'text':
                    self.restore_text_element(element_data)
                elif element_data['type'] == 'image':
                    self.restore_image_element(element_data)
            if hasattr(self, 'layer_manager'):
                self.layer_manager.update_layers()
            print(f"恢复状态完成: {len(state['elements'])} 个元素")
        except Exception as e:
            print(f"恢复状态时出错: {e}")
    def clear_all_elements(self):
        """清除所有元素"""
        for text_item in list(self.text_items.values()):
            if text_item and text_item.scene():
                self.scene.removeItem(text_item)
        self.text_items.clear()
        for image_item in list(self.image_items.values()):
            if image_item and image_item.scene():
                self.scene.removeItem(image_item)
        self.image_items.clear()
        if self.background_item and self.background_item.scene():
            self.scene.removeItem(self.background_item)
        self.background_item = None
        self.template.background_image = None
        self.template.elements.clear()
    def restore_text_element(self, element_data):
        """恢复文字元素"""
        try:
            text_item = MovableTextItem(element_data['text'], element_data['font'])
            text_item.setDefaultTextColor(element_data['color'])
            text_item.setPos(*element_data['pos'])
            text_item.current_scale = element_data['scale']
            text_item.setZValue(element_data['z_value'])
            if element_data['scale'] != 1.0:
                transform = QTransform().scale(element_data['scale'], element_data['scale'])
                text_item.setTransform(transform)
            self.scene.addItem(text_item)
            self.text_items[element_data['id']] = text_item
            color_tuple = (element_data['color'].red(), element_data['color'].green(), 
                          element_data['color'].blue(), element_data['color'].alpha())
            self.template.add_text_element(
                element_data['id'], 
                element_data['text'], 
                "",
                element_data['font'].pointSize(), 
                color_tuple, 
                element_data['pos'], 
                0,
                scale=element_data['scale']
            )
        except Exception as e:
            print(f"恢复文字元素时出错: {e}")
    def restore_image_element(self, element_data):
        """恢复图片元素"""
        try:
            image_path = element_data['pixmap_path']
            if not image_path or not os.path.exists(image_path):
                return
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                return
            image_item = MovableImageItem(pixmap)
            image_item.setPos(*element_data['pos'])
            image_item.current_scale = element_data['scale']
            image_item.setZValue(element_data['z_value'])
            if element_data['scale'] != 1.0:
                transform = QTransform().scale(element_data['scale'], element_data['scale'])
                image_item.setTransform(transform)
            self.scene.addItem(image_item)
            self.image_items[element_data['id']] = image_item
            self.template.add_image_element(
                element_data['id'],
                image_path,
                element_data['pos'],
                (pixmap.width(), pixmap.height()),
                element_data['scale']
            )
        except Exception as e:
            print(f"恢复图片元素时出错: {e}")
    def update_undo_buttons(self):
        """更新撤销/重做按钮状态"""
        try:
            main_window = self.window()
            if main_window and hasattr(main_window, 'undo_btn') and hasattr(main_window, 'redo_btn'):
                main_window.undo_btn.setEnabled(len(self.undo_stack) > 0)
                main_window.redo_btn.setEnabled(len(self.redo_stack) > 0)
        except Exception as e:
            print(f"更新撤销按钮状态时出错: {e}")
    def keyPressEvent(self, event):
        """处理键盘按键事件，实现方向键微调功能"""
        try:
            key = event.key()
            modifiers = event.modifiers()
            if modifiers & Qt.ControlModifier:
                if key == Qt.Key_Z:
                    self.undo()
                    event.accept()
                    return
                elif key == Qt.Key_Y:
                    self.redo()
                    event.accept()
                    return
            selected_items = self.scene.selectedItems()
            if not selected_items:
                super().keyPressEvent(event)
                return
            if key in [Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right]:
                self.save_state("move_elements", f"移动元素 ({len(selected_items)} 个)")
                dx = 0
                dy = 0
                if key == Qt.Key_Up:
                    dy = -1
                elif key == Qt.Key_Down:
                    dy = 1
                elif key == Qt.Key_Left:
                    dx = -1
                elif key == Qt.Key_Right:
                    dx = 1
                for item in selected_items:
                    if isinstance(item, (MovableTextItem, MovableImageItem)):
                        current_pos = item.pos()
                        new_pos = QPointF(current_pos.x() + dx, current_pos.y() + dy)
                        item.setPos(new_pos)
                        if isinstance(item, MovableTextItem):
                            self.text_position_changed(item)
                        elif isinstance(item, MovableImageItem):
                            self.image_position_changed(item)
                if hasattr(self, 'layer_manager'):
                    self.layer_manager.update_layers()
                self.update_status_message(f"元素已移动 ({dx}, {dy}) 像素")
                event.accept()
                return
            super().keyPressEvent(event)
        except Exception as e:
            print(f"处理键盘事件时出错: {e}")
            super().keyPressEvent(event)
    def mousePressEvent(self, event):
        """处理鼠标点击事件，确保获得焦点"""
        super().mousePressEvent(event)
        self.setFocus()
        self.setFocusPolicy(Qt.StrongFocus)
    def render_scene_to_png(self, file_path):
        """将场景渲染为PNG文件，1K分辨率，与编辑器显示完全一致"""
        try:
            guide_visible = False
            border_visible = False
            selection_boxes_visible = []
            if hasattr(self, 'ratio_guide_item') and self.ratio_guide_item:
                guide_visible = self.ratio_guide_item.isVisible()
                self.ratio_guide_item.setVisible(False)
            if hasattr(self, 'border_item') and self.border_item:
                border_visible = self.border_item.isVisible()
                self.border_item.setVisible(False)
            for item in self.scene.items():
                if hasattr(item, 'selection_handles'):
                    handles_visible = []
                    for handle in item.selection_handles:
                        handles_visible.append(handle.isVisible())
                        handle.setVisible(False)
                    selection_boxes_visible.append((item, handles_visible))
            canvas_width = self.template.width
            canvas_height = self.template.height
            if canvas_width > canvas_height:
                export_width = 1024
                export_height = int(1024 * canvas_height / canvas_width)
            else:
                export_height = 1024
                export_width = int(1024 * canvas_width / canvas_height)
            pixmap = QPixmap(export_width, export_height)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.setRenderHint(QPainter.TextAntialiasing)
            canvas_rect = QRectF(0, 0, canvas_width, canvas_height)
            output_rect = QRectF(0, 0, export_width, export_height)
            self.scene.render(painter, output_rect, canvas_rect)
            painter.end()
            if hasattr(self, 'ratio_guide_item') and self.ratio_guide_item:
                self.ratio_guide_item.setVisible(guide_visible)
            if hasattr(self, 'border_item') and self.border_item:
                self.border_item.setVisible(border_visible)
            for item, handles_visible in selection_boxes_visible:
                if hasattr(item, 'selection_handles'):
                    for i, handle in enumerate(item.selection_handles):
                        if i < len(handles_visible):
                            handle.setVisible(handles_visible[i])
            pixmap.save(file_path, "PNG", 100)
        except Exception as e:
            print(f"渲染场景到PNG时出错: {e}")
            raise e
class LayerManager(QDockWidget):
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
        refresh_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("刷新图层")
        self.refresh_btn.clicked.connect(self.update_layers)
        refresh_layout.addWidget(self.refresh_btn)
        refresh_layout.addStretch()
        layout.addLayout(refresh_layout)
    def update_layers(self):
        """更新图层列表"""
        try:
            self.layer_list.clear()
            all_items = []
            for text_id, text_item in list(self.template_editor.text_items.items()):
                try:
                    if text_item and text_item.scene() is not None:
                        all_items.append((text_item.zValue(), text_id, "文字", text_item))
                    else:
                        del self.template_editor.text_items[text_id]
                except:
                    if text_id in self.template_editor.text_items:
                        del self.template_editor.text_items[text_id]
            for image_id, image_item in list(self.template_editor.image_items.items()):
                try:
                    if image_item and image_item.scene() is not None:
                        all_items.append((image_item.zValue(), image_id, "图片", image_item))
                    else:
                        del self.template_editor.image_items[image_id]
                except:
                    if image_id in self.template_editor.image_items:
                        del self.template_editor.image_items[image_id]
            if self.template_editor.background_item:
                try:
                    if self.template_editor.background_item.scene() is not None:
                        self.template_editor.background_item.setZValue(-1)
                        all_items.append((-1, "background", "背景", self.template_editor.background_item))
                    else:
                        self.template_editor.background_item = None
                except:
                    self.template_editor.background_item = None
            all_items.sort(key=lambda x: x[0], reverse=True)
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
        """当项目顺序改变时更新Z值"""
        pass
    def on_layer_selection_changed(self):
        """当图层列表选择改变时，同步选中封面编辑器中的元素"""
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
        """上移选中项"""
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
        """下移选中项"""
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
        """置顶选中项"""
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
        """置底选中项"""
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
        """根据列表顺序更新Z值"""
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
    def __init__(self):
        super().__init__("图片资源库")
        self.folders_data = []
        self.setup_ui()
        self.load_folders_data()
    def setup_ui(self):
        central_widget = QWidget()
        self.setWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.add_folder_btn = QPushButton("添加图片文件夹（支持多选）")
        layout.addWidget(self.add_folder_btn)
        self.folder_tree = QTreeWidget()
        self.folder_tree.setHeaderLabel("图片分类")
        layout.addWidget(self.folder_tree)
        preview_group = QGroupBox("图片预览")
        preview_layout = QVBoxLayout()
        preview_group.setLayout(preview_layout)
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(200, 150)
        self.preview_label.setStyleSheet("border: 1px solid gray; background-color:")
        self.preview_label.setText("预览区域")
        preview_layout.addWidget(self.preview_label)
        button_layout = QHBoxLayout()
        self.add_bg_btn = QPushButton("设为背景")
        self.add_foreground_btn = QPushButton("添加到封面")
        self.replace_btn = QPushButton("替换选中")
        button_layout.addWidget(self.add_bg_btn)
        button_layout.addWidget(self.add_foreground_btn)
        button_layout.addWidget(self.replace_btn)
        preview_layout.addLayout(button_layout)
        layout.addWidget(preview_group)
        self.image_list = QListWidget()
        layout.addWidget(QLabel("图片列表:"))
        layout.addWidget(self.image_list)
        self.folder_tree.itemSelectionChanged.connect(self.on_folder_selected)
        self.image_list.itemSelectionChanged.connect(self.on_image_selected)
        self.add_folder_btn.clicked.connect(self.add_image_folder)
        self.folder_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.folder_tree.customContextMenuRequested.connect(self.show_folder_context_menu)
        self.image_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.image_list.customContextMenuRequested.connect(self.show_image_context_menu)
    def add_image_folder(self):
        dialog = MultiFolderDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            folders = dialog.get_selected_folders()
            for folder_path, category_name in folders:
                if folder_path and category_name:
                    self.add_image_folder_item(folder_path, category_name)
    def add_image_folder_item(self, folder_path, category_name):
        if not os.path.exists(folder_path):
            return
        existing_items = self.folder_tree.findItems(category_name, Qt.MatchExactly)
        if existing_items:
            category_item = existing_items[0]
        else:
            category_item = QTreeWidgetItem(self.folder_tree, [category_name])
        category_item.setData(0, Qt.UserRole, folder_path)
        if (folder_path, category_name) not in self.folders_data:
            self.folders_data.append((folder_path, category_name))
            self.save_folders_data()
        self.folder_tree.expandAll()
    def on_folder_selected(self):
        selected_items = self.folder_tree.selectedItems()
        if not selected_items:
            return
        folder_path = selected_items[0].data(0, Qt.UserRole)
        if not folder_path or not os.path.exists(folder_path):
            return
        self.image_list.clear()
        self.preview_label.clear()
        self.preview_label.setText("选择图片查看预览")
        image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp']
        try:
            for file_name in sorted(os.listdir(folder_path)):
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path) and any(file_name.lower().endswith(ext) for ext in image_extensions):
                    item = QListWidgetItem(file_name)
                    item.setData(Qt.UserRole, file_path)
                    self.image_list.addItem(item)
        except PermissionError:
            QMessageBox.warning(self, "权限错误", f"无法访问文件夹: {folder_path}")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"加载图片时出错: {str(e)}")
    def on_image_selected(self):
        selected_items = self.image_list.selectedItems()
        if not selected_items:
            return
        image_path = selected_items[0].data(Qt.UserRole)
        if not image_path or not os.path.exists(image_path):
            return
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.width() - 10,
                    self.preview_label.height() - 10,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
            else:
                self.preview_label.setText("无法加载图片")
        except Exception as e:
            self.preview_label.setText("预览加载失败")
    def get_selected_image_path(self):
        """获取当前选中的图片路径"""
        selected_items = self.image_list.selectedItems()
        if selected_items:
            return selected_items[0].data(Qt.UserRole)
        return None
    def save_folders_data(self):
        """保存文件夹数据到文件"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), 'image_folders.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.folders_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存文件夹数据失败: {e}")
    def load_folders_data(self):
        """从文件加载文件夹数据"""
        try:
            config_file = os.path.join(os.path.dirname(__file__), 'image_folders.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.folders_data = json.load(f)
                for folder_path, category_name in self.folders_data:
                    if os.path.exists(folder_path):
                        self.add_image_folder_item(folder_path, category_name)
        except Exception as e:
            print(f"加载文件夹数据失败: {e}")
            self.folders_data = []
    def show_folder_context_menu(self, position):
        """显示文件夹右键菜单"""
        item = self.folder_tree.itemAt(position)
        if not item:
            return
        menu = QMenu(self)
        delete_action = QAction("删除分类", self)
        delete_action.triggered.connect(lambda: self.delete_folder_category(item))
        menu.addAction(delete_action)
        menu.exec_(self.folder_tree.mapToGlobal(position))
    def show_image_context_menu(self, position):
        """显示图片右键菜单"""
        item = self.image_list.itemAt(position)
        if not item:
            return
        menu = QMenu(self)
        delete_action = QAction("删除图片", self)
        delete_action.triggered.connect(lambda: self.delete_image_file(item))
        menu.addAction(delete_action)
        menu.exec_(self.image_list.mapToGlobal(position))
    def delete_folder_category(self, item):
        """删除文件夹分类"""
        folder_path = item.data(0, Qt.UserRole)
        category_name = item.text(0)
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除分类 '{category_name}' 吗？\n此操作将从资源库中移除该分类。", 
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.folders_data = [(path, name) for path, name in self.folders_data 
                               if not (path == folder_path and name == category_name)]
            self.save_folders_data()
            self.folder_tree.takeTopLevelItem(self.folder_tree.indexOfTopLevelItem(item))
            self.image_list.clear()
            self.preview_label.clear()
            self.preview_label.setText("选择图片查看预览")
    def delete_image_file(self, item):
        """删除图片文件"""
        image_path = item.data(Qt.UserRole)
        image_name = item.text()
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除图片 '{image_name}' 吗？\n此操作将永久删除文件，无法恢复。", 
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
                self.image_list.takeItem(self.image_list.row(item))
                self.preview_label.clear()
                self.preview_label.setText("选择图片查看预览")
                QMessageBox.information(self, "完成", f"图片 '{image_name}' 已删除")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除图片时出错: {str(e)}")
class FontManager:
    def __init__(self):
        self.fonts = {}
        self.config_file = os.path.join(os.path.dirname(__file__), 'fonts_config.json')
        self.load_basic_fonts()
        self.load_fonts_config()
    def load_basic_fonts(self):
        self.fonts["默认字体"] = ""
        self.fonts["Arial"] = "Arial"
    def add_font(self, name, path):
        self.fonts[name] = path
        self.save_fonts_config()
    def get_font_path(self, name):
        return self.fonts.get(name, "")
    def save_fonts_config(self):
        """保存字体配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.fonts, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存字体配置失败: {e}")
    def load_fonts_config(self):
        """从文件加载字体配置"""
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
        """删除字体"""
        if name in self.fonts:
            del self.fonts[name]
            self.save_fonts_config()
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.font_manager = FontManager()
        self.workspace_root = os.path.dirname(os.path.abspath(__file__))
        self.init_ui()
    def get_workspace_root(self):
        return self.workspace_root
    def to_relative_path(self, absolute_path):
        if not absolute_path or not os.path.isabs(absolute_path):
            return absolute_path
        try:
            abs_path = os.path.normpath(absolute_path)
            workspace = os.path.normpath(self.workspace_root)
            if abs_path.startswith(workspace):
                rel_path = os.path.relpath(abs_path, workspace)
                return rel_path.replace('\\', '/')
            else:
                return absolute_path
        except Exception as e:
            print(f"转换路径失败: {e}")
            return absolute_path
    def to_absolute_path(self, path):
        if not path:
            return path
        if os.path.isabs(path) and os.path.exists(path):
            return path
        try:
            abs_path = os.path.normpath(os.path.join(self.workspace_root, path))
            if os.path.exists(abs_path):
                return abs_path
        except Exception as e:
            print(f"解析路径失败: {e}")
        if os.path.isabs(path):
            return path
        return path
    def init_ui(self):
        self.setWindowTitle("封面批量生成软件")
        self.setGeometry(100, 100, 1400, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        left_panel = QVBoxLayout()
        left_panel.setContentsMargins(0, 0, 0, 0)
        text_group = QGroupBox("文本编辑")
        text_layout = QVBoxLayout()
        text_group.setLayout(text_layout)
        self.text_input = QTextEdit()
        self.text_input.setMaximumHeight(60)
        text_layout.addWidget(QLabel("文本内容:"))
        text_layout.addWidget(self.text_input)
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
        template_group = QGroupBox("模板操作")
        template_layout = QVBoxLayout()
        template_group.setLayout(template_layout)
        ratio_layout = QHBoxLayout()
        ratio_layout.addWidget(QLabel("比例:"))
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(["16:9", "4:3"])
        self.ratio_combo.setCurrentText("16:9")
        self.ratio_combo.currentTextChanged.connect(self.change_aspect_ratio)
        ratio_layout.addWidget(self.ratio_combo)
        template_layout.addLayout(ratio_layout)
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
        right_panel = QVBoxLayout()
        self.template_editor = TemplateEditor()
        self.template_editor.font_manager = self.font_manager
        right_panel.addWidget(self.template_editor)
        self.template_editor.set_aspect_ratio("16:9")
        self.image_library = ImageLibrary()
        self.addDockWidget(Qt.RightDockWidgetArea, self.image_library)
        self.layer_manager = LayerManager(self.template_editor)
        self.addDockWidget(Qt.RightDockWidgetArea, self.layer_manager)
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 3)
        self.image_library.add_bg_btn.clicked.connect(self.set_background_from_library)
        self.image_library.add_foreground_btn.clicked.connect(self.add_foreground_image)
        self.image_library.replace_btn.clicked.connect(self.replace_selected_image)
        self.image_library.image_list.itemDoubleClicked.connect(self.use_selected_image)
        self.create_menu()
        self.statusBar().showMessage("就绪 - 提示：选中元素后可使用方向键进行1像素微调")
        self.setup_shortcuts()
        self.setup_undo_shortcuts()
    def setup_shortcuts(self):
        delete_action = QAction(self)
        delete_action.setShortcut(Qt.Key_Delete)
        delete_action.triggered.connect(self.delete_selected_elements)
        self.addAction(delete_action)
        delete_action2 = QAction(self)
        delete_action2.setShortcut(Qt.Key_Backspace)
        delete_action2.triggered.connect(self.delete_selected_elements)
        self.addAction(delete_action2)
    def setup_undo_shortcuts(self):
        """设置撤销/重做快捷键"""
        undo_action = QAction(self)
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo_action)
        self.addAction(undo_action)
        redo_action = QAction(self)
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo_action)
        self.addAction(redo_action)
    def create_menu(self):
        menubar = self.menuBar()
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
        edit_menu = menubar.addMenu('编辑')
        delete_action = QAction('删除选中', self)
        delete_action.setShortcut('Delete')
        delete_action.triggered.connect(self.delete_selected_elements)
        edit_menu.addAction(delete_action)
        view_menu = menubar.addMenu('视图')
        view_menu.addAction(self.image_library.toggleViewAction())
        view_menu.addAction(self.layer_manager.toggleViewAction())
    def add_font(self):
        dialog = AddFontDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            font_name = dialog.font_name.text()
            font_path = dialog.font_file.text()
            if font_name and font_path and os.path.exists(font_path):
                self.font_manager.add_font(font_name, font_path)
                self.update_font_combo()
                self.font_combo.setCurrentText(font_name)
                self.statusBar().showMessage(f"已添加字体: {font_name}")
            else:
                QMessageBox.warning(self, "错误", "字体名称或路径无效")
    def update_font_combo(self):
        """更新字体组合框"""
        current_text = self.font_combo.currentText()
        self.font_combo.clear()
        self.font_combo.addItems(self.font_manager.fonts.keys())
        if current_text in self.font_manager.fonts:
            self.font_combo.setCurrentText(current_text)
    def choose_color(self):
        color = QColorDialog.getColor(self.current_color, self)
        if color.isValid():
            self.current_color = color
    def choose_bg_color(self):
        color = QColorDialog.getColor(self.template_editor.current_bg_color, self)
        if color.isValid():
            self.template_editor.save_state("set_background_color", f"设置背景颜色: {color.name()}")
            self.template_editor.set_background_color(color)
            self.bg_color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")
    def add_text_to_template(self):
        text = self.text_input.toPlainText()
        if not text:
            QMessageBox.warning(self, "警告", "请输入文本内容")
            return
        font_name = self.font_combo.currentText()
        font_path = self.font_manager.get_font_path(font_name)
        font_size = self.font_size.value()
        self.template_editor.add_text_element(text, font_path, font_size, self.current_color)
        self.template_editor.save_state("add_text", f"添加文字: {text[:20]}...")
    def change_aspect_ratio(self, ratio):
        has_elements = (len(self.template_editor.text_items) > 0 or 
                       len(self.template_editor.image_items) > 0 or 
                       self.template_editor.background_item is not None)
        if has_elements:
            reply = QMessageBox.question(
                self, "确认更换比例", 
                f"确定要更换比例为 {ratio} 吗？\n当前画布上的所有元素位置可能会发生变化。", 
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                current_ratio = self.template_editor.template.aspect_ratio
                self.ratio_combo.setCurrentText(current_ratio)
                return
        self.template_editor.set_aspect_ratio(ratio)
        if ratio == "16:9":
            pass
        else:
            self.template_editor.show_4_3_guide = False
            if hasattr(self.template_editor, 'ratio_guide_item') and self.template_editor.ratio_guide_item:
                self.template_editor.scene.removeItem(self.template_editor.ratio_guide_item)
                self.template_editor.ratio_guide_item = None
            self.show_4_3_guide_btn.setChecked(False)
            self.show_4_3_guide_btn.setText("显示4:3参考框")
    def toggle_edit_mode(self):
        """切换编辑模式"""
        is_checked = self.edit_mode_btn.isChecked()
        self.template_editor.set_edit_mode(is_checked)
        if is_checked:
            self.edit_mode_btn.setText("退出背景编辑")
            self.statusBar().showMessage("背景编辑模式已启用 - 可以移动和缩放背景图片")
        else:
            self.edit_mode_btn.setText("背景编辑模式")
            self.statusBar().showMessage("背景编辑模式已关闭")
    def toggle_4_3_guide(self):
        """切换4:3参考框显示"""
        is_checked = self.show_4_3_guide_btn.isChecked()
        if is_checked:
            self.show_4_3_guide_btn.setText("隐藏4:3参考框")
            if self.template_editor.template.aspect_ratio == "16:9":
                self.template_editor.show_4_3_guide = True
                self.template_editor.add_4_3_guide()
            else:
                QMessageBox.information(self, "提示", "4:3参考框只在16:9模式下有效")
                self.show_4_3_guide_btn.setChecked(False)
                self.show_4_3_guide_btn.setText("显示4:3参考框")
        else:
            self.show_4_3_guide_btn.setText("显示4:3参考框")
            self.template_editor.show_4_3_guide = False
            if hasattr(self.template_editor, 'ratio_guide_item') and self.template_editor.ratio_guide_item:
                self.template_editor.scene.removeItem(self.template_editor.ratio_guide_item)
                self.template_editor.ratio_guide_item = None
    def undo_action(self):
        """撤销操作"""
        self.template_editor.undo()
    def redo_action(self):
        """重做操作"""
        self.template_editor.redo()
    def new_template(self):
        """新建模板"""
        try:
            reply = QMessageBox.question(
                self, "新建模板", 
                "确定要新建模板吗？当前未保存的更改将丢失。", 
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.template_editor.text_items.clear()
                self.template_editor.image_items.clear()
                self.template_editor.background_item = None
                self.template_editor.border_item = None
                self.template_editor.scene.clear()
                self.template_editor.template = CoverTemplate()
                self.template_editor.update_canvas_border()
                self.template_editor.update_background()
                self.edit_mode_btn.setChecked(False)
                self.template_editor.set_edit_mode(False)
                self.template_editor.undo_stack.clear()
                self.template_editor.redo_stack.clear()
                if hasattr(self, 'layer_manager'):
                    self.layer_manager.update_layers()
                self.statusBar().showMessage("已新建模板")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"新建模板时出错: {str(e)}")
            print(f"新建模板错误: {e}")
    def export_cover(self):
        """导出封面为PNG格式，1K分辨率"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存封面", "cover.png", "PNG文件 (*.png)"
        )
        if not file_path:
            return
        try:
            self.template_editor.render_scene_to_png(file_path)
            QMessageBox.information(self, "完成", f"封面已导出到 {file_path}")
            self.statusBar().showMessage(f"封面已导出: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出封面时出错: {str(e)}")
    def set_background_from_library(self):
        image_path = self.image_library.get_selected_image_path()
        if image_path:
            has_background = (self.template_editor.background_item is not None or 
                            self.template_editor.template.background_image is not None)
            if has_background:
                reply = QMessageBox.question(
                    self, "确认更换背景", 
                    "确定要更换背景图片吗？\n当前背景将被替换。", 
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            self.template_editor.set_background_image(image_path)
            image_name = os.path.basename(image_path)
            self.template_editor.save_state("set_background", f"设置背景: {image_name}")
    def add_foreground_image(self):
        image_path = self.image_library.get_selected_image_path()
        if image_path:
            self.template_editor.add_image_element(image_path)
            image_name = os.path.basename(image_path)
            self.template_editor.save_state("add_image", f"添加图片: {image_name}")
    def replace_selected_image(self):
        image_path = self.image_library.get_selected_image_path()
        if image_path:
            selected_items = self.template_editor.scene.selectedItems()
            if not selected_items:
                QMessageBox.information(self, "提示", "请先选中一个图片元素")
                return
            is_background = any(item == self.template_editor.background_item for item in selected_items)
            if is_background:
                reply = QMessageBox.question(
                    self, "确认更换背景", 
                    "确定要更换背景图片吗？\n当前背景将被替换。", 
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            success = self.template_editor.replace_selected_image(image_path)
            if not success:
                QMessageBox.information(self, "提示", "替换失败，请检查图片文件")
    def delete_selected_elements(self):
        selected_items = self.template_editor.scene.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "提示", "请先选中要删除的元素")
            return
        text_count = sum(1 for item in selected_items if isinstance(item, MovableTextItem))
        image_count = sum(1 for item in selected_items if isinstance(item, MovableImageItem))
        message_parts = []
        if text_count > 0:
            message_parts.append(f"{text_count} 个文本元素")
        if image_count > 0:
            message_parts.append(f"{image_count} 个图片元素")
        message = f"确定要删除选中的 {', '.join(message_parts)} 吗？\n此操作无法撤销。"
        reply = QMessageBox.question(
            self, "确认删除", 
            message, 
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.template_editor.remove_selected_elements()
            self.template_editor.save_state("delete_elements", f"删除 {len(selected_items)} 个元素")
    def use_selected_image(self, item):
        if item:
            image_path = item.data(Qt.UserRole)
            self.template_editor.set_background_image(image_path)
    def save_template(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "保存模板", "", "模板文件 (*.json)")
        if file_path:
            try:
                # 获取模板文件所在目录
                template_dir = os.path.dirname(file_path)
                
                background_info = None
                if (self.template_editor.background_item and 
                    isinstance(self.template_editor.background_item, MovableImageItem)):
                    background_info = {
                        'position': (self.template_editor.background_item.pos().x(), 
                                   self.template_editor.background_item.pos().y()),
                        'scale': self.template_editor.background_item.current_scale
                    }
                
                # 转换背景图片路径为相对路径
                background_image_path = None
                if self.template_editor.template.background_image:
                    try:
                        background_image_path = os.path.relpath(self.template_editor.template.background_image, template_dir)
                        background_image_path = background_image_path.replace('\\', '/')
                    except ValueError:
                        # 如果无法转换为相对路径（在不同驱动器），保持绝对路径
                        background_image_path = self.template_editor.template.background_image
                
                elements = []
                for element in self.template_editor.template.elements:
                    new_element = element.copy()
                    if element.get('type') == 'image' and 'image_path' in element:
                        # 转换图片路径为相对路径
                        try:
                            new_element['image_path'] = os.path.relpath(element['image_path'], template_dir).replace('\\', '/')
                        except ValueError:
                            new_element['image_path'] = element['image_path']
                    if element.get('type') == 'text' and 'font_path' in element:
                        # 转换字体路径为相对路径
                        try:
                            new_element['font_path'] = os.path.relpath(element['font_path'], template_dir).replace('\\', '/')
                        except ValueError:
                            new_element['font_path'] = element['font_path']
                    elements.append(new_element)
                
                template_data = {
                    'width': self.template_editor.template.width,
                    'height': self.template_editor.template.height,
                    'aspect_ratio': self.template_editor.template.aspect_ratio,
                    'background_image': background_image_path,
                    'background_info': background_info,
                    'elements': elements
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(template_data, f, indent=4, ensure_ascii=False)
                self.statusBar().showMessage(f"模板已保存: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存模板失败: {str(e)}")
    def load_template(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "加载模板", "", "模板文件 (*.json)")
        if file_path:
            try:
                # 获取模板文件所在目录
                template_dir = os.path.dirname(file_path)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                
                # 转换相对路径为绝对路径
                background_image_path = None
                if template_data.get('background_image'):
                    bg_path = template_data['background_image']
                    if not os.path.isabs(bg_path):
                        background_image_path = os.path.normpath(os.path.join(template_dir, bg_path))
                    else:
                        background_image_path = bg_path
                
                elements = []
                for element in template_data.get('elements', []):
                    new_element = element.copy()
                    if element.get('type') == 'image' and 'image_path' in element:
                        img_path = element['image_path']
                        if not os.path.isabs(img_path):
                            new_element['image_path'] = os.path.normpath(os.path.join(template_dir, img_path))
                        else:
                            new_element['image_path'] = img_path
                    if element.get('type') == 'text' and 'font_path' in element:
                        font_path = element['font_path']
                        if font_path and not os.path.isabs(font_path):
                            new_element['font_path'] = os.path.normpath(os.path.join(template_dir, font_path))
                        else:
                            new_element['font_path'] = font_path
                    elements.append(new_element)
                self.template_editor.template = CoverTemplate(
                    template_data['width'], template_data['height']
                )
                self.template_editor.template.aspect_ratio = template_data['aspect_ratio']
                self.template_editor.template.background_image = background_image_path
                self.template_editor.template.elements = elements
                self.ratio_combo.setCurrentText(template_data['aspect_ratio'])
                if background_image_path and os.path.exists(background_image_path):
                    self.template_editor.set_background_image(background_image_path)
                    background_info = template_data.get('background_info')
                    if (background_info and self.template_editor.background_item and 
                        isinstance(self.template_editor.background_item, MovableImageItem)):
                        self.template_editor.background_item.setPos(*background_info['position'])
                        self.template_editor.background_item.current_scale = background_info['scale']
                        if background_info['scale'] != 1.0:
                            transform = QTransform().scale(background_info['scale'], background_info['scale'])
                            self.template_editor.background_item.setTransform(transform)
                self.template_editor.load_template_elements(elements)
                self.layer_manager.update_layers()
                self.template_editor.undo_stack.clear()
                self.template_editor.redo_stack.clear()
                self.statusBar().showMessage(f"模板已加载: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载模板失败: {str(e)}")
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
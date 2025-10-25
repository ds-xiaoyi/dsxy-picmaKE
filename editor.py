######编辑器#######
######图层是傻逼，我不会做######
import os
import time
from PyQt5.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsRectItem, 
                             QGraphicsPixmapItem, QMessageBox, QMenu, QAction)
from PyQt5.QtCore import Qt, QRectF, QPointF, QTimer
from PyQt5.QtGui import (QPainter, QFont, QColor, QPixmap, QPen, QBrush, 
                         QTransform, QFontDatabase)
from template import CoverTemplate, MovableTextItem, MovableImageItem


class TemplateEditor(QGraphicsView):
    """模板编辑器 - 核心编辑功能"""
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # 模板和状态
        self.template = CoverTemplate()
        self.template.width = 800
        self.template.height = 450
        self.template.aspect_ratio = "16:9"
        self.current_bg_color = Qt.white
        
        # 渲染设置
        self.setRenderHint(QPainter.Antialiasing)
        
        # 元素管理
        self.text_items = {}
        self.image_items = {}
        self.background_item = None
        
        # UI状态
        self.border_item = None
        self.ratio_guide_item = None
        self.show_4_3_guide = False
        self.edit_mode = False
        self.syncing_selection = False
        
        # 缩放和交互
        self.scale_factor = 1.0
        self.min_scale = 0.1
        self.max_scale = 10.0
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setInteractive(True)
        self.setFocusPolicy(Qt.StrongFocus)
        
        # 撤销重做
        self.undo_stack = []
        self.redo_stack = []
        self.max_undo_steps = 50
        self.movement_saved = False
        self.scaling_elements = set()
        
        # 初始化
        self.update_canvas_border()
        self.update_background()
        self.scene.selectionChanged.connect(self.on_selection_changed)
        self.scene.selectionChanged.connect(self.ensure_focus)

    def get_next_z_value(self):
        """获取下一个z值"""
        max_z = 1000
        for item in self.scene.items():
            if hasattr(item, 'zValue'):
                max_z = max(max_z, item.zValue())
        return max_z + 1

    def get_next_text_id(self):
        """获取下一个文字ID"""
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
        """获取下一个图片ID"""
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
        """更新画布边框"""
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
        """添加4:3比例参考线"""
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
        """更新背景"""
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
        """设置背景颜色"""
        self.current_bg_color = color
        if not self.template.background_image:
            self.update_background()

    def set_background_image(self, image_path):
        """设置背景图片"""
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
        """设置画布比例"""
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
        """添加文字元素"""
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
        """添加图片元素"""
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
        """文字位置改变时的处理"""
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
        """图片位置改变时的处理"""
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

    def on_selection_changed(self):
        """选择改变时的处理"""
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
        """确保焦点"""
        self.setFocus()
        selected_items = self.scene.selectedItems()
        if selected_items:
            count = len(selected_items)
            msg = f"已选中 {count} 个元素 - 使用方向键进行1像素微调"
            self.update_status_message(msg)
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
        """保存状态到撤销栈"""
        try:
            state = {
                'action_type': action_type,
                'description': description,
                'timestamp': time.time(),
                'elements': self.get_elements_snapshot(),
                'background': self.get_background_snapshot()
            }
            
            if self.undo_stack and self.states_are_same(self.undo_stack[-1], state):
                return
            
            self.undo_stack.append(state)
            if len(self.undo_stack) > self.max_undo_steps:
                self.undo_stack.pop(0)
            
            self.redo_stack.clear()
            self.update_undo_buttons()
        except Exception as e:
            print(f"保存状态时出错: {e}")

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
        """从元素获取图片路径"""
        for element in self.template.elements:
            if element['id'] == image_id:
                return element.get('image_path', '')
        return ''

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

    def update_undo_buttons(self):
        """更新撤销重做按钮状态"""
        try:
            main_window = self.window()
            if main_window and hasattr(main_window, 'undo_btn'):
                main_window.undo_btn.setEnabled(len(self.undo_stack) > 0)
            if main_window and hasattr(main_window, 'redo_btn'):
                main_window.redo_btn.setEnabled(len(self.redo_stack) > 0)
        except Exception as e:
            print(f"更新撤销按钮时出错: {e}")

    def undo(self):
        """撤销操作"""
        try:
            if not self.undo_stack:
                self.update_status_message("没有可撤销的操作")
                return
            
            current_state = {
                'action_type': 'current',
                'description': 'current state',
                'timestamp': time.time(),
                'elements': self.get_elements_snapshot(),
                'background': self.get_background_snapshot()
            }
            self.redo_stack.append(current_state)
            
            state = self.undo_stack.pop()
            if self.undo_stack:
                prev_state = self.undo_stack[-1]
                self.restore_state(prev_state)
            else:
                self.restore_template_state()
            
            self.update_undo_buttons()
            self.update_status_message(f"已撤销: {state['description']}")
        except Exception as e:
            print(f"撤销操作时出错: {e}")

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
                'timestamp': time.time(),
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
            
            # 恢复元素
            for element_data in state['elements']:
                if element_data['type'] == 'text':
                    self.restore_text_element(element_data)
                elif element_data['type'] == 'image':
                    self.restore_image_element(element_data)
            
            if hasattr(self, 'layer_manager'):
                self.layer_manager.update_layers()
        except Exception as e:
            print(f"恢复状态时出错: {e}")

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
            
            # 添加到模板
            color_tuple = (element_data['color'].red(), element_data['color'].green(), 
                          element_data['color'].blue(), element_data['color'].alpha())
            font_path = ""
            for element in self.template.elements:
                if element['id'] == element_data['id']:
                    font_path = element.get('font_path', "")
                    break
            
            self.template.add_text_element(element_data['id'], element_data['text'], 
                                         font_path, element_data['font'].pointSize(), 
                                         color_tuple, element_data['pos'], 0, 
                                         scale=element_data['scale'])
        except Exception as e:
            print(f"恢复文字元素时出错: {e}")

    def restore_image_element(self, element_data):
        """恢复图片元素"""
        try:
            if os.path.exists(element_data['pixmap_path']):
                pixmap = QPixmap(element_data['pixmap_path'])
                if not pixmap.isNull():
                    image_item = MovableImageItem(pixmap)
                    image_item.setPos(*element_data['pos'])
                    image_item.current_scale = element_data['scale']
                    image_item.setZValue(element_data['z_value'])
                    
                    if element_data['scale'] != 1.0:
                        transform = QTransform().scale(element_data['scale'], element_data['scale'])
                        image_item.setTransform(transform)
                    
                    self.scene.addItem(image_item)
                    self.image_items[element_data['id']] = image_item
                    
                    # 添加到模板
                    size = (pixmap.width(), pixmap.height())
                    self.template.add_image_element(element_data['id'], element_data['pixmap_path'], 
                                                   element_data['pos'], size, element_data['scale'])
        except Exception as e:
            print(f"恢复图片元素时出错: {e}")

    def restore_template_state(self):
        """恢复模板初始状态"""
        try:
            self.clear_all_elements()
            self.template.background_image = None
            self.set_background_color(QColor(255, 255, 255))
        except Exception as e:
            print(f"恢复模板状态时出错: {e}")

    def clear_all_elements(self):
        """清空所有元素"""
        try:
            self.scene.clear()
            self.text_items.clear()
            self.image_items.clear()
            self.background_item = None
            self.border_item = None
            self.ratio_guide_item = None
            self.update_canvas_border()
        except Exception as e:
            print(f"清空元素时出错: {e}")

    def load_template_elements(self, elements):
        """加载模板元素"""
        try:
            for element in elements:
                if element['type'] == 'text':
                    self.load_text_element(element)
                elif element['type'] == 'image':
                    self.load_image_element(element)
        except Exception as e:
            print(f"加载模板元素时出错: {e}")

    def load_text_element(self, element):
        """加载文字元素"""
        try:
            font_path = element.get('font_path', '')
            font_size = element['font_size']
            color_tuple = element['color']
            color = QColor(*color_tuple)
            
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
                font = QFont("Arial", font_size)
            
            text_item = MovableTextItem(element['text'], font)
            text_item.setDefaultTextColor(color)
            text_item.setPos(*element['position'])
            text_item.current_scale = element.get('scale', 1.0)
            
            if text_item.current_scale != 1.0:
                transform = QTransform().scale(text_item.current_scale, text_item.current_scale)
                text_item.setTransform(transform)
            
            self.scene.addItem(text_item)
            self.text_items[element['id']] = text_item
        except Exception as e:
            print(f"加载文字元素时出错: {e}")

    def load_image_element(self, element):
        """加载图片元素"""
        try:
            image_path = element['image_path']
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    image_item = MovableImageItem(pixmap)
                    image_item.setPos(*element['position'])
                    image_item.current_scale = element.get('scale', 1.0)
                    
                    if image_item.current_scale != 1.0:
                        transform = QTransform().scale(image_item.current_scale, image_item.current_scale)
                        image_item.setTransform(transform)
                    
                    self.scene.addItem(image_item)
                    self.image_items[element['id']] = image_item
        except Exception as e:
            print(f"加载图片元素时出错: {e}")

    def render_to_png(self, output_path):
        """渲染为PNG"""
        try:
            from PyQt5.QtGui import QImage
            # 创建图片
            img = QImage(self.template.width, self.template.height, QImage.Format_ARGB32)
            img.fill(Qt.transparent)
            painter = QPainter(img)
            painter.setRenderHint(QPainter.Antialiasing)
            self.scene.render(painter)
            painter.end()
            img.save(output_path, "PNG")
            return True
        except Exception as e:
            print(f"渲染场景到PNG时出错: {e}")
            return False

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

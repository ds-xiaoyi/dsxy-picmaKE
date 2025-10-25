#######模板########
import os
from PyQt5.QtWidgets import QGraphicsTextItem, QGraphicsPixmapItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QFont, QTransform
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("错误：缺少PIL库，请安装Pillow：pip install Pillow")


class CoverTemplate:
    """封面模板类 - 管理模板数据和渲染"""
    def __init__(self, width=800, height=600):
        self.elements = []
        self.background_image = None
        self.foreground_images = []
        self.width = width
        self.height = height
        self.aspect_ratio = "16:9"

    def add_text_element(self, id, text, font_path, font_size, color, position, max_width, alignment="left", scale=1.0):
        """添加或更新文字元素"""
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
        """添加或更新图片元素"""
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
        """设置背景图片"""
        self.background_image = image_path

    def remove_element(self, element_id):
        """移除指定元素"""
        self.elements = [e for e in self.elements if e['id'] != element_id]

    def render(self, output_path, file_format='jpg', text_data=None, image_data=None):
        """渲染模板为图片"""
        # 创建基础画布
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
        
        # 渲染所有元素
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
    """可移动的文字项"""
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
        super().mouseDoubleClickEvent(event)
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            if hasattr(view, 'edit_text_item'):
                view.edit_text_item(self)


class MovableImageItem(QGraphicsPixmapItem):
    """可移动的图片项"""
    def __init__(self, pixmap, parent=None):
        super().__init__(pixmap, parent)
        self.setFlags(QGraphicsPixmapItem.ItemIsMovable | 
                     QGraphicsPixmapItem.ItemIsSelectable |
                     QGraphicsPixmapItem.ItemIsFocusable)
        self.current_scale = 1.0

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            if hasattr(view, 'image_position_changed'):
                view.image_position_changed(self)
            if hasattr(view, 'movement_saved'):
                view.movement_saved = False

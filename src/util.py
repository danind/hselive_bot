"""
util.py
"""
import wget
import zipfile
from telebot import types
from typing import Literal
from PIL import Image, ImageDraw
from static import *


def download_font(font_url: str) -> None:
    """
    Скачивает шрифт по заданной ссылке
    :param font_url: ссылка для скачивания шрифта
    """
    if not os.path.exists(FONT_PATH):
        filename = wget.download(font_url)

        with zipfile.ZipFile(filename, 'r') as file:
            file.extractall(os.getcwd())
        os.remove(filename)


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """
    Конвертирует цвет из RGB в HEX
    :param rgb: цветовое значение RGB
    :return: цветовое значение HEX
    """
    return '#{:02x}{:02x}{:02x}'.format(*rgb)


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """
    Конвертирует цвет из RGB в HEX
    :param hex_code: цветовое значение HEX
    :return: цветовое значение RGB
    """
    hex_code = hex_code.lstrip('#')
    r = int(hex_code[0:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:6], 16)
    return r, g, b


def rgb_to_hsl(rgb: Tuple[int, int, int]) -> Tuple[int, float, float]:
    """
    Конвертирует цвет из RGB в HSL
    :param rgb: цветовое значение RGB
    :return: цветовое значение HSL
    """
    r = rgb[0] / 255
    g = rgb[1] / 255
    b = rgb[2] / 255

    col_max = max(r, g, b)
    col_min = min(r, g, b)
    delta = col_max - col_min

    lightness = (col_max + col_min) / 2
    if delta == 0:
        saturation = 0.0
        hue = 0.0
    else:
        saturation = delta / (1 - abs(2 * lightness - 1))
        if col_max == r:
            hue = 60 * (((g - b) / delta) % 6)
        elif col_max == g:
            hue = 60 * (((b - r) / delta) + 2)
        else:
            hue = 60 * (((r - g) / delta) + 4)
    return int(round(hue)), round(saturation*100, 1), round(lightness*100, 1)


def hex_to_hsl(hex_code: str) -> Tuple[int, float, float]:
    """
    Конвертирует цвет из RGB в HEX
    :param hex_code: цветовое значение HEX
    :return: цветовое значение HSL
    """
    return rgb_to_hsl(hex_to_rgb(hex_code))


def find_avg_rgb(path_to_image: str) -> Tuple[int, int, int]:
    """
    Определяет средний цвет изображения
    :param path_to_image: путь к изображению
    :return: средний цвет изображения, цветовое значение RGB
    """
    image = Image.open(path_to_image).convert('RGBA')
    resized = image.resize((1, 1), Image.Resampling.LANCZOS)
    return resized.load()[0, 0][:3]


def rgb_to_greyscale_hex(rgb: Tuple[int, int, int]) -> str:
    """
    Конвертирует цвет из RGB в HEX в оттенках серого
    :param rgb: цветовое значение RGB
    :return: цветовое значение HEX в оттенках серого
    """
    max_rgb = max(rgb)
    return rgb_to_hex((max_rgb, max_rgb, max_rgb))


def create_gradient(hex_code: str, size: Tuple[int, int], reverse: bool = False) -> Image.Image:
    """
    Создаёт чёрно-белый градиент по заданному цвету и размеру
    :param hex_code: цветовое значение HEX
    :param size: размер возвращаемого изображения
    :param reverse: если ложно, градиент от чёрного к светлому (и наоборот)
    :return: изображение с градиентом
    """
    width, height = size
    image = Image.new('L', (width, height))
    brightness = max(hex_to_rgb(hex_code))
    draw = ImageDraw.Draw(image)
    for i in range(1, width):
        color = int(brightness * (i / width))
        draw.line((i, 0, i, height), fill=color)
    if reverse:
        image = image.rotate(180)
    return image


def isbright(hex_code: str) -> bool:
    """
    Определяет, является ли цвет ярким по значению Lightness в цветовой модели HSL
    :param hex_code: цветовое значение HEX
    :return: является ли цвет светлым (истинно, если Lightness больше или равно 50.0)
    """
    hsl = hex_to_hsl(hex_code)
    return True if hsl[2] >= 50.0 else False


def define_fill(background_col: str) -> Tuple[int, int, int]:
    """
    Определяет цвет для текста в зависимости от цвета фона
    :param background_col: цвет фона
    :return: цветовое значение RGB: чёрный, если цвет фона светлый, белый – если фон тёмный
    """
    return (0, 0, 0) if isbright(background_col) else (255, 255, 255)


def calculate_coords_rectangle(i: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Рассчитывает координаты боковых прямоугольников по порядковому номеру прямоугольника
    :param i: порядковый номер прямоугольника
    :return: координаты прямоугольника в формате ``((x1, y1), (x2, y2))``
    """
    if i < RECTANGLE_NUM:
        x1y1 = (0, max(0, RECTANGLE_HEIGHT * i))
        x2y2 = (RECTANGLE_WIDTH - 1, min(PIC_HEIGHT - 1, RECTANGLE_HEIGHT * (i + 1) - 1))
    else:
        x1y1 = (PIC_WIDTH - RECTANGLE_WIDTH, max(0, RECTANGLE_HEIGHT * (i - RECTANGLE_NUM)))
        x2y2 = (PIC_WIDTH - 1, min(PIC_HEIGHT - 1, RECTANGLE_HEIGHT * (i - RECTANGLE_NUM + 1) - 1))
    return x1y1, x2y2


def pick_title_font(text: str, font: ImageFont.FreeTypeFont) -> ImageFont.FreeTypeFont:
    """
    Подбирает ширину заголовочного шрифта в зависимости от ширины текста.\n
    Если надпись слишком широкая, возвращает тот же шрифт
    :param text: заголовочный текст
    :param font: вариативный шрифт с осью ширины
    :return: шрифт с настроенной осью ширины
    """
    if '\n' in text:
        text = find_longest_line(text)
    if not iswide(text, font) or istoowide(text, font):
        return font
    else:
        draw = ImageDraw.Draw(Image.new(mode='RGBA', size=(1000, 1000)))
        font_condensed = font.font_variant()
        condensed_font_axes = TITLE_FONT_AXES[:]
        while draw.textlength(text, font_condensed) > PIC_HEIGHT:
            condensed_font_axes[WIDTH_AXES_INDEX] -= 1
            font_condensed.set_variation_by_axes(condensed_font_axes)
        else:
            return font_condensed


def pick_title_params(text: str, title_type: Literal['upper', 'lower']) -> Dict:
    """
    Устанавливает параметры надписи в зависимости от расположения текста,
    присутствия в нём символов с диакритическими знаками, количества строк.
    Параметры соответствуют аргументам ``ImageDraw.Draw.text()``.
    Параметры сохраняются в словарь с информацией об обложке
    :param text: заголовочный текст
    :param title_type: тип заголовка: ``upper`` – верхний, ``lower`` – нижний
    :return: словарь с параметрами
    """
    params = {
        'xy':      (0, 0),
        'text':    text,
        'font':    TITLE_FONT,
        'spacing': -5 * MULTIPLIER,
        'fill':    None,
        'align':   'center',
        'anchor':  'ms',
        }
    lines = text.split('\n')
    diacritics_in_lines = [any([letter in line for letter in LETTERS_WITH_DIACRITICS]) for line in lines]
    diacritics_first = diacritics_in_lines[0]
    diacritics_other = any(diacritics_in_lines[1:])

    summand_for_lower = PIC_HEIGHT - RECTANGLE_HEIGHT if title_type == 'lower' else 0
    if len(lines) == 1:
        params['xy'] = (PIC_WIDTH / 2, RECTANGLE_HEIGHT) if title_type == 'upper' else (PIC_WIDTH / 2, PIC_HEIGHT)
        params['font'] = pick_title_font(text, TITLE_FONT)
        return params
    elif not any(diacritics_in_lines):
        params['xy'] = (PIC_WIDTH / 2, TITLE_FONT_SIZE_PIXELS + summand_for_lower)
        params['font'] = pick_title_font(text, TITLE_FONT)
        return params

    if diacritics_first and not diacritics_other:
        font_size = int(68 * MULTIPLIER)
        font_size_pixels = 48.5 * MULTIPLIER
        params['xy'] = (PIC_WIDTH / 2, font_size_pixels + 12.5 * MULTIPLIER + summand_for_lower)
        params['spacing'] = -4.5 * MULTIPLIER
    elif not diacritics_first and diacritics_other:
        font_size = int(68 * MULTIPLIER)
        font_size_pixels = 48.5 * MULTIPLIER
        params['xy'] = (PIC_WIDTH / 2, font_size_pixels + summand_for_lower)
        params['spacing'] = 8.25 * MULTIPLIER
    else:
        font_size = int(62 * MULTIPLIER)
        font_size_pixels = 44 * MULTIPLIER
        params['xy'] = (PIC_WIDTH / 2, font_size_pixels + 12 * MULTIPLIER + summand_for_lower)
        params['spacing'] = 6 * MULTIPLIER
    font = ImageFont.truetype(
        font=FONT_PATH,
        size=font_size,
        encoding='unic')
    font.set_variation_by_axes(TITLE_FONT_AXES)
    params['font'] = pick_title_font(text, font)
    return params


def find_longest_line(text: str) -> str:
    """
    Находит в тексте строку с наибольшим количеством символов
    :param text: многострочный текст
    :return: строка с наибольшим количеством символов
    """
    lines = text.split('\n')
    return max(lines, key=len)


def istoowide(text: str, font: ImageFont.FreeTypeFont, min_width: int = MIN_WIDTH) -> bool:
    """
    Определяет, является ли текст, набранный данным шрифтом, слишком широким
    :param text: заголовочный текст
    :param font: заголовочный вариативный шрифт с осью ширины
    :param min_width: минимальная ширина вариативного шрифта
    :return: ``True``, если при минимальном значении ширины у шрифта ``iswide()`` возвращает ``True``. ``False`` – в
    обратном случае
    """
    if '\n' in text:
        text = find_longest_line(text)
    font_condensed = font.font_variant()
    condensed_font_axes = TITLE_FONT_AXES[:]
    condensed_font_axes[WIDTH_AXES_INDEX] = min_width
    font_condensed.set_variation_by_axes(condensed_font_axes)
    if iswide(text, font_condensed):
        return True
    return False


def iswide(text: str, font: ImageFont.FreeTypeFont) -> bool:
    """
    Определяет, превышает ли ширина текста, набранная данным шрифтом, ширину изображения
    :param text: заголовочный текст
    :param font: заголовочный шрифт
    :return: ``True``, если заданное условие выполняется. ``False`` – в обратном случае
    """
    draw = ImageDraw.Draw(Image.new(mode='RGBA', size=(1000, 1000)))
    if draw.textlength(text, font) >= PHOTO_WIDTH:
        return True
    return False


def calculate_copyright_xy(i: int) -> Tuple[int, int]:
    """
    Рассчитывает координаты копирайт-надписи по порядковому номеру, на которой она находится
    :param i: порядковый номер прямоугольника, на котором располагается надпись
    :return: координаты надписи в формате ``(x, y)``
    """
    if i < RECTANGLE_NUM:
        x = 0
        y = RECTANGLE_HEIGHT * (i + 1)
    else:
        x = RECTANGLE_WIDTH * (RECTANGLE_NUM - 1)
        y = RECTANGLE_HEIGHT * (i - RECTANGLE_NUM + 1)
    return x, y + (6 * MULTIPLIER)


def make_corner_type_markup() -> types.InlineKeyboardMarkup:
    """
    Создаёт Inline-клавиатуру для выбора типа расположения прямоугольников
    """
    markup = types.InlineKeyboardMarkup(row_width=4)
    corner_btns = [types.InlineKeyboardButton(str(i), callback_data='corner_'+str(i)) for i in CORNER_COORDS.keys()]
    other_corner_btn = types.InlineKeyboardButton('Собрать самому', callback_data='custom_corner')
    ready_btn = types.InlineKeyboardButton('Готово', callback_data=f'corner_ready')
    markup.row(other_corner_btn)
    markup.add(*corner_btns)
    markup.row(ready_btn)
    return markup


def make_interface_markup(prefix: str, corners: List[int],
                          add_random: bool = True, add_ready: bool = True) -> types.InlineKeyboardMarkup:
    """
    Создаёт Inline-клавиатуру для редактирования расположения прямоугольников
    :param prefix: префикс, который будет передаваться в callback_data у кнопок
    :param corners: список состояний прямоугольников (закрашен – 1, не закрашен – 0)
    :param add_random: если истинно, добавляет кнопку «Рандом»
    :param add_ready: если истинно, добавляет кнопку «Готово»
    :return: Inline-клавиатура
    """
    markup = types.InlineKeyboardMarkup(row_width=6)
    for i in range(RECTANGLE_NUM):
        col_state_left, col_state_right = (f'_{corners[i]}',
                                           f'_{corners[i+RECTANGLE_NUM]}') if prefix == CUSTOM_CORNER_PREFIX else ('',
                                                                                                                   '')
        row = [types.InlineKeyboardButton(str(i+1), callback_data=f'{prefix}_{str(i)}' + col_state_left)]
        for j in range(4):
            row.append(types.InlineKeyboardButton('⬛', callback_data='_'))
        row.append(types.InlineKeyboardButton(str(i+RECTANGLE_NUM+1),
                                              callback_data=f'{prefix}_{str(i+RECTANGLE_NUM)}'+col_state_right))
        markup.add(*row)

    if add_random:
        random_btn = types.InlineKeyboardButton('Рандом', callback_data=f'{prefix}_random')
        markup.row(random_btn)
    if add_ready:
        ready_btn = types.InlineKeyboardButton('Готово', callback_data=f'{prefix}_ready')
        markup.row(ready_btn)
    return markup


def make_photo_bg_markup() -> types.InlineKeyboardMarkup:
    """
    Создаёт Inline-клавиатуру для выбора фона фотографии
    :return: Inline-клавиатура
    """
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_white = types.InlineKeyboardButton('Белый', callback_data=f'bg_white')
    btn_black = types.InlineKeyboardButton('Серый', callback_data=f'bg_grey')
    btn_gradient_white = types.InlineKeyboardButton('Чёрно-белый градиент', callback_data=f'bg_grad-white')
    btn_gradient_grey = types.InlineKeyboardButton('Чёрно-серый градиент', callback_data=f'bg_grad-grey')
    markup.add(btn_white, btn_black, btn_gradient_white, btn_gradient_grey)
    return markup


def edit_custom_message(call: types.CallbackQuery, corners: List[int]) -> None:
    """
    Изменяет сообщение о редактировании расположения прямоугольников
    :param call: запрос, по которому определяется сообщение для редактирования
    :param corners: список состояний прямоугольников (закрашен – 1, не закрашен – 0)
    """
    preview_pic_path = PATH_TO_SAVE + str(call.message.chat.id) + '_' + PREVIEW_PIC_POSTFIX
    BOT.edit_message_media(media=types.InputMediaPhoto(open(preview_pic_path, 'rb'),
                                                       caption='Выбери прямоугольники, которые будут перекрашены'),
                           chat_id=call.message.chat.id,
                           message_id=call.message.message_id,
                           reply_markup=make_interface_markup(CUSTOM_CORNER_PREFIX, corners))

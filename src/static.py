"""
static.py
"""
import os
import telebot
from PIL import ImageFont
from typing import Dict, Tuple, List


BOT: telebot.TeleBot = telebot.TeleBot(token=open('./token.txt', 'r', encoding='utf-8').read())

PATH_TO_SAVE: str = os.getcwd() + '/pictures/'
FONT_URL: str = 'https://github.com/googlefonts/roboto-flex/releases/download/3.200/roboto-flex-fonts.zip'
FONT_PATH: str = os.getcwd() +\
  '/roboto-flex-fonts/fonts/variable/RobotoFlex[GRAD,XOPQ,XTRA,YOPQ,YTAS,YTDE,YTFI,YTLC,YTUC,opsz,slnt,wdth,wght].ttf'

LETTERS_WITH_DIACRITICS: Tuple[str, str] = ('Й', 'Ё')
COPYRIGHT_TEXT: str = '©\nЛАЙВ\nРАБОТАЕТ'
PHOTOGRAPHER_TEXT: str = 'ФОТОГРАФ'
PHOTOGRAPHERS_TEXT: str = 'ФОТОГРАФЫ'
PREFIX2POS: Dict[str, str] = {
    'u': 'верхней',
    'l': 'нижней',
    'i': 'левой',
    'r': 'правой',
}
CUSTOM_CORNER_PREFIX: str = 'custom-corner'
COPYRIGHT_SIGN_PREFIX: str = 'copyright-sign'

PREVIEW_PIC_POSTFIX: str = 'example.png'
RESULT_PIC_POSTFIX: str = 'result.png'

MULTIPLIER: int = 2
PIC_WIDTH: int = 1080 * MULTIPLIER
PIC_HEIGHT: int = 720 * MULTIPLIER
PIC_SIZE: Tuple[int, int] = (PIC_WIDTH, PIC_HEIGHT)

RECTANGLE_NUM: int = 6
RECTANGLE_WIDTH: int = int(PIC_WIDTH / RECTANGLE_NUM)       # 180 if p_w=1080,num=6
RECTANGLE_HEIGHT: int = int(PIC_HEIGHT / RECTANGLE_NUM)     # 120 if p_h=720,num=6
RECTANGLE_SIZE: Tuple[int, int] = (RECTANGLE_WIDTH, RECTANGLE_HEIGHT)

COVER_BASE_INFO: Dict[str, str | bool | int | Dict | List] = {
    'photo':              '',
    'mask':               False,
    'photo_bg':           '',
    'upper_title_params': dict(),
    'upper_title':        '',
    'lower_title_params': dict(),
    'lower_title':        '',
    'corners':            [0 for _ in range(RECTANGLE_NUM * 2)],
    'copyright_sign':     0,
}

PHOTO_WIDTH: int = int(PIC_WIDTH - RECTANGLE_WIDTH * 2)     # 720 if p_w=1080,r_w=180
PHOTO_HEIGHT: int = int(PIC_HEIGHT - RECTANGLE_HEIGHT * 2)  # 480 if p_h=720,r_h=120
PHOTO_SIZE: Tuple[int, int] = (PHOTO_WIDTH, PHOTO_HEIGHT)

UPPER_COORDS: Tuple[Tuple[int, int], Tuple[int, int]] = (
        (RECTANGLE_WIDTH, 0),
        (RECTANGLE_WIDTH * (RECTANGLE_NUM - 1) - 1, RECTANGLE_HEIGHT - 1)
    )
LOWER_COORDS: Tuple[Tuple[int, int], Tuple[int, int]] = (
        (RECTANGLE_WIDTH, RECTANGLE_HEIGHT * (RECTANGLE_NUM - 1)),
        (RECTANGLE_WIDTH * (RECTANGLE_NUM - 1) - 1, RECTANGLE_HEIGHT * RECTANGLE_NUM - 1)
    )

CORNER_COORDS: Dict[int, Tuple[int, int, int, int, int, int, int, int, int, int, int, int]] = {
    1:  (0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0),
    2:  (1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1),
    3:  (0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0),
    4:  (0, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0),
    5:  (0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0),
    6:  (1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0),
    7:  (0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0),
    8:  (1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1),
    9:  (1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1),
    10: (0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1),
    11: (1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0),
    12: (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1),
}

TITLE_FONT_AXES: List[int] = [60, 800, 0, 60, 0, 96, 79, 468, 712, 570, 750, -203, 738]
WIDTH_AXES_INDEX: int = 3
TITLE_FONT_SIZE: int = int(76 * MULTIPLIER)
TITLE_FONT_SIZE_PIXELS: int = int(54 * MULTIPLIER)

INFO_FONT_AXES: List[int] = [8, 523, 0, 151, 0, 96, 79, 468, 712, 570, 750, -203, 738]
INFO_FONT_SIZE: int = int(24 * MULTIPLIER)
INFO_FONT_SIZE_PIXELS: int = int(17 * MULTIPLIER)

TITLE_FONT: ImageFont.FreeTypeFont = ImageFont.truetype(
    font=FONT_PATH,
    size=TITLE_FONT_SIZE,
    encoding='unic')
TITLE_FONT.set_variation_by_axes(TITLE_FONT_AXES)
MIN_WIDTH: int = TITLE_FONT.get_variation_axes()[WIDTH_AXES_INDEX]['minimum']

INFO_FONT: ImageFont.FreeTypeFont = ImageFont.truetype(
    font=FONT_PATH,
    size=INFO_FONT_SIZE,
    encoding='unic')
INFO_FONT.set_variation_by_axes(INFO_FONT_AXES)

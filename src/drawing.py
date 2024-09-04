"""
drawing.py
"""
from PIL import Image, ImageDraw
from static import *
from util import (calculate_coords_rectangle,
                  calculate_copyright_xy,
                  define_fill,
                  find_avg_rgb,
                  rgb_to_greyscale_hex,
                  create_gradient)


def draw_preview_digits(coords: List[int], draw: ImageDraw.ImageDraw, cover_info: Dict) -> None:
    """
    Рисует на превью-изображении цифру / цифры – координаты прямоугольников
    :param coords: координата прямоугольника, где нужно нарисовать цифру
    :param draw: экземпляр ``ImageDraw.Draw`` с превью-изображением
    :param cover_info: параметры обложки
    """
    corners = cover_info['corners']
    for coord in coords:
        xy_rectangle = calculate_coords_rectangle(coord)
        xy_font = (xy_rectangle[0][0] + RECTANGLE_WIDTH / 2, xy_rectangle[0][1] + RECTANGLE_HEIGHT / 2)
        if coord < RECTANGLE_NUM and corners[coord]:
            bg_color = cover_info['left_color']
        elif coord >= RECTANGLE_NUM and corners[coord]:
            bg_color = cover_info['right_color']
        else:
            bg_color = '#000000'
        draw.text(xy=xy_font,
                  text=str(coord+1),
                  font=INFO_FONT,
                  fill=define_fill(bg_color),
                  align='center',
                  anchor='mm')


def draw_photo_bg(image: Image.Image, draw: ImageDraw.ImageDraw, size: Tuple[int, int], photo_bg: str,
                  cover_info: Dict) -> None:
    """
    Рисует на изображении фон для фото
    :param image: экземпляр ``Image.Image`` с обложкой
    :param draw: экземпляр ``ImageDraw.Draw`` с обложкой
    :param size: размер фото в пикселях (ширина, высота)
    :param photo_bg: информация о фоне изображения
    :param cover_info: параметры обложки
    """
    width, height = size
    xy_1 = (
        RECTANGLE_SIZE,
        (int((PIC_WIDTH - width) / 2) - 1, RECTANGLE_HEIGHT + PHOTO_HEIGHT - 1))
    xy_2 = (
        (int((PIC_WIDTH + width) / 2), RECTANGLE_HEIGHT),
        (PIC_WIDTH - RECTANGLE_WIDTH - 1, RECTANGLE_HEIGHT + PHOTO_HEIGHT - 1))
    if '-' not in photo_bg:
        if photo_bg == 'white':
            fill = '#FFFFFF'
        else:
            fill = rgb_to_greyscale_hex(find_avg_rgb(cover_info['photo']))

        draw.rectangle(xy=xy_1,
                       fill=fill)
        draw.rectangle(xy=xy_2,
                       fill=fill)
    else:
        if photo_bg.split('-')[1] == 'white':
            fill = '#FFFFFF'
        else:
            fill = rgb_to_greyscale_hex(find_avg_rgb(cover_info['photo']))

        gradient_size = (int((PHOTO_WIDTH - width) / 2), PHOTO_HEIGHT)
        gradient = create_gradient(fill, gradient_size)
        gradient_reverse = create_gradient(fill, gradient_size, True)
        image.paste(im=gradient, box=xy_1[0])
        image.paste(im=gradient_reverse, box=xy_2[0])


def make_crop_mask(photo: Image.Image, cover_info: Dict) -> Image.Image | None:
    """
    Создаёт маску для обрезания фотографии, если она требуется
    :param photo: фото для обрезания
    :param cover_info: параметры обложки
    """
    if cover_info.get('mask'):
        mask = Image.new('L', photo.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rectangle(xy=(((photo.size[0] - PHOTO_WIDTH) / 2, 0),
                           ((photo.size[0] + PHOTO_WIDTH) / 2 - 1, photo.size[1] - 1)),
                       fill=255)
        return mask
    return None


def draw_photo(draw: ImageDraw.ImageDraw, image: Image.Image, cover_info: Dict) -> None:
    """
    Вставляет на изображение фотографию
    :param draw: экземпляр ``ImageDraw.Draw`` с обложкой
    :param image: экземпляр ``Image.Image`` с обложкой
    :param cover_info: параметры обложки
    """
    photo = Image.open(cover_info['photo'])
    width, height = photo.size
    width *= (PHOTO_HEIGHT / height)
    photo = photo.resize((int(width), PHOTO_HEIGHT))
    image.paste(im=photo,
                box=(int((PIC_WIDTH - width) / 2), RECTANGLE_HEIGHT),
                mask=make_crop_mask(photo, cover_info))
    if photo_bg := cover_info.get('photo_bg'):
        draw_photo_bg(image, draw, (width, height), photo_bg, cover_info)


def draw_upper_lower_rectangles(draw: ImageDraw.ImageDraw, cover_info: Dict) -> None:
    """
    Рисует на изображении верхние и нижние плашки
    :param draw: экземпляр ``ImageDraw.Draw`` с обложкой
    :param cover_info: параметры обложки
    """
    draw.rectangle(xy=UPPER_COORDS,
                   fill=cover_info['upper_color'])

    draw.rectangle(xy=LOWER_COORDS,
                   fill=cover_info['lower_color'])


def redraw_rectangle(coord: int, color_state: int, draw: ImageDraw.ImageDraw, cover_info: Dict,
                     draw_digits: bool = True) -> None:
    """
    Перерисовывает прямоугольник на превью-изображении,
    сохраняет данные о перерисованных прямоугольниках
    :param coord: координата прямоугольника, который нужно перерисовать
    :param color_state: состояние прямоугольника: 0 – не закашенный, 1 – закрашенный
    :param draw: экземпляр ``ImageDraw.Draw`` с обложкой
    :param draw_digits: если истинно, рисует поверх перерисованного прямоугольника цифру с координатой
    :param cover_info: параметры обложки
    """
    corners = cover_info['corners']
    if color_state:
        corners[coord] = 0
        draw.rectangle(xy=calculate_coords_rectangle(coord),
                       fill='#000000')
    else:
        corners[coord] = 1
        fill = cover_info['left_color'] if coord < RECTANGLE_NUM else cover_info['right_color']
        draw.rectangle(xy=calculate_coords_rectangle(coord),
                       fill=fill)
    if draw_digits:
        draw_preview_digits([coord], draw, cover_info)


def draw_corners(draw: ImageDraw.ImageDraw, cover_info: Dict) -> None:
    """
    Рисует на изображении прямоугольники
    :param draw: экземпляр ``ImageDraw.Draw`` с обложкой
    :param cover_info: параметры обложки
    """
    coords = cover_info['corners']

    for i, coord in enumerate(coords):
        if coord:
            fill = cover_info['left_color'] if i < RECTANGLE_NUM else cover_info['right_color']
            draw.rectangle(xy=calculate_coords_rectangle(i),
                           fill=fill)


def draw_upper_title(draw: ImageDraw.ImageDraw, cover_info: Dict) -> None:
    """
    Рисует на изображении верхний заголовок
    :param draw: экземпляр ``ImageDraw.Draw`` с обложкой
    :param cover_info: параметры обложки
    """
    if len(cover_info['upper_title'].split('\n')) == 3:
        draw_upper_rectangle(draw, cover_info)
    params = cover_info['upper_title_params']
    draw.text(**params)


def draw_upper_rectangle(draw: ImageDraw.ImageDraw, cover_info: Dict):
    """
    Рисует на изображении прямоугольник по ширине третьей строки
    :param draw: экземпляр ``ImageDraw.Draw`` с обложкой
    :param cover_info: параметры обложки
    """
    params = cover_info['upper_title_params']
    font = params['font']
    spacing = params['spacing']
    xy = params['xy']

    splitted_text = cover_info['upper_title'].split('\n')
    bbox = draw.textbbox(text='X\nX\n' + splitted_text[-1].strip(), xy=xy, font=font,
                         spacing=spacing, anchor='ms', align='center')
    bbox_bottom = draw.textbbox(text='\n'.join(splitted_text[:2]) + '\nX', xy=xy, font=font,
                                spacing=spacing, anchor='ms', align='center')
    coords = (max(bbox[0], RECTANGLE_WIDTH), bbox[1], min(bbox[2], PIC_WIDTH - RECTANGLE_WIDTH), bbox_bottom[3])
    draw.rectangle(coords, fill=cover_info['upper_color'])


def draw_lower_title(draw: ImageDraw.ImageDraw, cover_info: Dict) -> None:
    """
    Рисует на изображении нижний заголовок, надпись «ФОТОГРАФ» / «ФОТОГРАФЫ»
    :param draw: экземпляр ``ImageDraw.Draw`` с обложкой
    :param cover_info: параметры обложки
    """
    draw_photographer_text(draw, cover_info)
    params = cover_info['lower_title_params']
    draw.text(**params)


def draw_photographer_text(draw: ImageDraw.ImageDraw, cover_info: Dict) -> None:
    """
    Рисует на изображении надпись «ФОТОГРАФ» / «ФОТОГРАФЫ» с цветной подложкой
    :param draw: экземпляр ``ImageDraw.Draw`` с обложкой
    :param cover_info: параметры обложки
    """
    if '\n' not in cover_info['lower_title']:
        draw.text(xy=(PIC_WIDTH / 2, PIC_HEIGHT - RECTANGLE_HEIGHT - 1),
                  text=PHOTOGRAPHER_TEXT,
                  fill=define_fill(cover_info['lower_color']),
                  font=INFO_FONT,
                  align='center',
                  anchor='mt')
    else:
        photographers_textlength = draw.textlength(PHOTOGRAPHERS_TEXT, INFO_FONT)
        rectangle_xy = (
            ((PIC_WIDTH / 2) - (photographers_textlength / 2), PIC_HEIGHT - RECTANGLE_HEIGHT - INFO_FONT_SIZE_PIXELS),
            ((PIC_WIDTH / 2) + (photographers_textlength / 2) - 1, PIC_HEIGHT - RECTANGLE_HEIGHT - 1)
        )
        draw.rectangle(xy=rectangle_xy,
                       fill=cover_info['lower_color'])
        draw.text(xy=(PIC_WIDTH / 2, PIC_HEIGHT - RECTANGLE_HEIGHT - INFO_FONT_SIZE_PIXELS - 1),
                  text=PHOTOGRAPHERS_TEXT,
                  fill=define_fill(cover_info['lower_color']),
                  font=INFO_FONT,
                  align='center',
                  anchor='mt')


def draw_copyright(draw: ImageDraw.ImageDraw, cover_info: Dict) -> None:
    """
    Рисует на изображении надпись-копирайт
    :param draw: экземпляр ``ImageDraw.Draw`` с обложкой
    :param cover_info: параметры обложки
    """
    coord_i = cover_info['copyright_sign']
    coords = cover_info['corners']

    if coords[coord_i] == 0:
        bg_color = '#000000'
    else:
        if coord_i < RECTANGLE_NUM:
            bg_color = cover_info['left_color']
        else:
            bg_color = cover_info['right_color']

    draw.text(xy=calculate_copyright_xy(coord_i),
              text=COPYRIGHT_TEXT,
              fill=define_fill(bg_color),
              spacing=int(INFO_FONT_SIZE_PIXELS / 17),
              font=INFO_FONT,
              align='left',
              anchor='ld')


def create_preview_pic(cover_info: Dict, chat_id: int, drawn_corners: bool = False) -> None:
    """
    «Собирает» превью-изображение
    :param cover_info: параметры обложки
    :param chat_id: айди чата (для сохранения картинки с нужным названием)
    :param drawn_corners: если истинно, рисует прямоугольники
    """
    my_image = Image.new(mode='RGBA',
                         size=(PIC_WIDTH, PIC_HEIGHT),
                         color='#000000')
    draw = ImageDraw.Draw(my_image)

    draw_upper_lower_rectangles(draw, cover_info)
    if drawn_corners:
        draw_corners(draw, cover_info)
    draw_photo(draw, my_image, cover_info)

    my_image.save(PATH_TO_SAVE + str(chat_id) + '_' + PREVIEW_PIC_POSTFIX)

"""
main.py
"""
import copy
import re
import logging
from telebot import types
from random import randint
from PIL import Image, ImageDraw
from typing import Callable, Literal
from static import *
from util import (download_font,
                  pick_title_params,
                  istoowide,
                  define_fill,
                  make_corner_type_markup,
                  make_interface_markup,
                  make_photo_bg_markup,
                  edit_custom_message)
from drawing import (create_preview_pic,
                     redraw_rectangle,
                     draw_preview_digits,
                     draw_upper_lower_rectangles,
                     draw_photo,
                     draw_corners,
                     draw_upper_title,
                     draw_lower_title,
                     draw_copyright)


logging.basicConfig(level=logging.INFO, filename=f'app.log', filemode='w',
                    format='%(asctime)s %(levelname)s %(message)s')
download_font(FONT_URL)
color2hex: Dict[str, str] = {
    '🟦 Голубой':    '#94FCFF',
    '🟩 Зелёный':    '#73E153',
    '🟧 Оранжевый':  '#F06C00',
    '🟨 Жёлтый':     '#FFFA00',
    '🟥 Красный':    '#D9003A',
    '💖 Розовый':    '#E04BCE',
    '🟪 Фиолетовый': '#5E00A2',
}
ids_to_delete: Dict[int, List[int]] = dict()
# ключ – айди чата, значение – список с айди сообщений
covers_info: Dict[int, Dict[str, str | bool | int | List | Dict]] = dict()
# ключ – айди чата, значение – словарь с параметрами обложки


def delete_messages(chat_id: int) -> None:
    """
    Удаляет сообщения из чата по их айди, записанным в ids_to_delete
    :param chat_id: айди чата
    """
    global ids_to_delete
    for i in ids_to_delete[chat_id]:
        BOT.delete_message(chat_id, i)
        logging.info(f'{chat_id} Сообщение удалено, айди: {i}')


def reset_all_info(chat_id: int) -> None:
    """
    «Сбрасывает» информацию об обложке, айди для удаления,
    расположение прямоугольников; удаляет изображения
    """
    global covers_info, ids_to_delete
    ids_to_delete[chat_id] = list()
    logging.warning(f'{chat_id} Сборшена информация об айди для удаления: {ids_to_delete[chat_id]}')
    photo_path = covers_info.get(chat_id, dict()).get('photo', '_')
    preview_pic_path = PATH_TO_SAVE + str(chat_id) + '_' + PREVIEW_PIC_POSTFIX
    result_pic_path = PATH_TO_SAVE + str(chat_id) + '_' + RESULT_PIC_POSTFIX
    for path in (photo_path, preview_pic_path, result_pic_path):
        if os.path.exists(path):
            os.remove(path)
            logging.warning(f'{chat_id} Удалён файл: {path}')
    covers_info[chat_id] = copy.deepcopy(COVER_BASE_INFO)
    logging.warning(f'{chat_id} Сброшена информация об обложке: {covers_info[chat_id]}')


@BOT.message_handler(commands=['start'])
def process_photo(message: types.Message) -> None:
    """
    Этап 1а: начало обработки фотографии.\n
    Переход к проверке фотографии (1б)
    :param message: сообщение пользователя
    """
    chat_id = message.chat.id
    reset_all_info(chat_id)
    msg = BOT.send_message(
        chat_id,
        text='Чтобы начать, отправь мне фотографию в виде документа'
    )
    ids_to_delete[chat_id].append(msg.message_id)
    BOT.register_next_step_handler(message, check_photo)


@BOT.callback_query_handler(func=lambda call: call.data.startswith('photo-other'))
def process_other_photo(call: types.CallbackQuery) -> None:
    """
    Этап 1в: начало обработки другой фотографии.\n
    Переход к проверке фотографии (1б)
    :param call: запрос от «неправильной» фотографии пользователя (1б)
    """
    global ids_to_delete
    chat_id = call.message.chat.id
    ids_to_delete[chat_id].append(int(call.data.split('_')[1]))
    photo_path = covers_info[chat_id]['photo']
    os.remove(photo_path)
    logging.warning(f'{chat_id} Удалено фото: {photo_path}')
    msg = BOT.send_message(
        chat_id,
        text='Чтобы продолжить, отправь другое фото'
    )
    ids_to_delete[chat_id].append(msg.message_id)
    BOT.register_next_step_handler(msg, check_photo)


@BOT.callback_query_handler(func=lambda call: call.data.startswith('bg'))
def save_photo_bg(call: types.CallbackQuery) -> None:
    """
    Этап 1д: сохранение фона фотографии.\n
    Переход к началу обработки верхнего заголовка (2а)
    :param call: запрос от сообщения с выбором фона фотографии (1г)
    """
    chat_id = call.message.chat.id
    photo_bg = call.data.split('_')[1]
    covers_info[chat_id]['photo_bg'] = photo_bg
    logging.info(f'{chat_id} Сохранён фон для фото: {photo_bg}')
    delete_messages(chat_id)
    process_upper_title(call.message)


@BOT.callback_query_handler(func=lambda call: call.data.startswith('photo-bg'))
def process_photo_bg(call: types.CallbackQuery) -> None:
    """
    Этап 1г: выбор фона фотографии.\n
    Переход к этапу сохранения фона фотографии (1д)
    :param call: запрос от сообщения
    """
    chat_id = call.message.chat.id
    msg = BOT.send_message(
        chat_id,
        text='Выбери цвет фона для зоны фото',
        reply_markup=make_photo_bg_markup()
        )
    ids_to_delete[chat_id].append(msg.message_id)


@BOT.callback_query_handler(func=lambda call: call.data.startswith('photo-crop'))
def save_crop(call: types.CallbackQuery) -> None:
    """
    Этап 1е: сохранение маски для обрезания фотографии.\n
    Переход к началу обработки верхнего заголовка (2а)
    :param call: запрос от сообщения
    """
    chat_id = call.message.chat.id
    mask = True
    covers_info[chat_id]['mask'] = mask
    logging.info(f'{chat_id} Включена маска для фотографии: {mask}')
    delete_messages(chat_id)
    process_upper_title(call.message)


def check_photo(message: types.Message) -> None:
    """
    Этап 1б: проверка фотографии, сообщение о несоответствии соотношения сторон,
    сохранение пути к фотографии.\n
    Переход к выбору другого фото (1в), выбору фона фотографии (1г),
    сохранению маски для обрезания фотографии (1е), началу обработки верхнего заголовка (2а)
    :param message: сообщение пользователя (предположительно, фотография) (1а)
    """
    global ids_to_delete
    chat_id = message.chat.id
    if message.content_type != 'document':
        logging.warning(f'{chat_id} Фото не принято, не тот тип сообщения: {message.content_type}')
        ids_to_delete[chat_id].append(message.message_id)
        msg = BOT.send_message(
            chat_id,
            text='Мне нужно отправить картинку в виде документа. Попробуй ещё раз'
            )
        ids_to_delete[chat_id].append(msg.message_id)
        BOT.register_next_step_handler(msg, check_photo)
        return

    file_extension = message.document.file_name.split('.')[-1]
    if file_extension not in ('png', 'jpg', 'jpeg'):
        logging.warning(f'{chat_id} Фото не принято, не то расширение: {file_extension}')
        ids_to_delete[chat_id].append(message.message_id)
        msg = BOT.send_message(
            chat_id,
            text='Я работаю только с файлами формата png, jpg, jpeg. Попробуй другой файл'
            )
        ids_to_delete[chat_id].append(msg.message_id)
        BOT.register_next_step_handler(msg, check_photo)
        return

    file_info = BOT.get_file(message.document.file_id)
    photo = BOT.download_file(file_info.file_path)
    photo_name = str(chat_id) + '_' + message.document.file_name
    photo_path = PATH_TO_SAVE + photo_name
    with open(photo_path, 'wb') as file:
        file.write(photo)
    covers_info[chat_id]['photo'] = photo_path
    logging.info(f'{chat_id} Фотография сохранена: {photo_path}')

    image = Image.open(photo_path)
    width, height = image.size
    markup = types.InlineKeyboardMarkup()
    button_choose_other_photo = types.InlineKeyboardButton('Выбрать другое фото',
                                                           callback_data=f'photo-other_{message.message_id}')
    if (width / height) < (PHOTO_WIDTH / PHOTO_HEIGHT):
        logging.warning(f'{chat_id} Соотношение сторон меньше 3:2 ({round(width / height, 2)})')
        button_photo_bg = types.InlineKeyboardButton('Продолжить', callback_data='photo-bg')
        markup.row(button_photo_bg)
        markup.row(button_choose_other_photo)
        msg = BOT.send_message(
            chat_id,
            text='Внимание! Соотношение сторон фотографии меньше 3:2. Для зоны фото будет добавлен фон по бокам',
            reply_markup=markup
            )
        ids_to_delete[chat_id].append(msg.message_id)
    elif (width / height) > (PHOTO_WIDTH / PHOTO_HEIGHT):
        logging.warning(f'{chat_id} Соотношение сторон больше 3:2 ({round(width / height), 2})')
        button_photo_crop = types.InlineKeyboardButton('Продолжить', callback_data='photo-crop')
        markup.row(button_photo_crop)
        markup.row(button_choose_other_photo)
        msg = BOT.send_message(
            chat_id,
            text='Внимание! Соотношение сторон фотографии больше 3:2. Фотография будет обрезана по бокам',
            reply_markup=markup
            )
        ids_to_delete[chat_id].append(msg.message_id)
    else:
        delete_messages(chat_id)
        process_upper_title(message)


def check_title(message: types.Message, title_type: Literal['upper', 'lower'], save_func: Callable) -> None:
    """
    Этап 2б / 3б: проверка заголовка.\n
    Переход к сохранению заголовка (2в / 3в)
    :param message: сообщение пользователя (предположительно, заголовок)
    :param title_type: тип заголовка: ``upper`` – верхний, ``lower`` – нижний
    :param save_func: функция, сохраняющая заголовок
    """
    global ids_to_delete
    chat_id = message.chat.id
    if message.content_type != 'text':
        logging.warning(f'{chat_id} Заголовок ({title_type}) не принят, не тот тип сообщения: {message.content_type}')
        ids_to_delete[chat_id].append(message.message_id)
        msg = BOT.send_message(
            chat_id,
            text='Сообщение должно содержать текст. Попробуй ещё раз'
        )
        ids_to_delete[chat_id].append(msg.message_id)
        BOT.register_next_step_handler(msg, check_title, title_type, save_func)
        return

    msg_text = message.text.strip().upper()
    max_n = 3 if title_type == 'upper' else 2
    title_params = pick_title_params(msg_text, title_type)
    covers_info[chat_id][f'{title_type}_title_params'] = title_params
    logging.info(f'{chat_id} Подобраны параметры для заголовка ({title_type}): {title_params}')
    font = covers_info[chat_id][f'{title_type}_title_params']['font']

    if istoowide(msg_text, font):
        logging.warning(f'{chat_id} Заголовок ({title_type}) не принят, слишком длинный: {msg_text}')
        ids_to_delete[chat_id].append(message.message_id)
        msg = BOT.send_message(
            chat_id,
            text='Текст слишком длинный. Попробуй ещё раз'
        )
        ids_to_delete[chat_id].append(msg.message_id)
        BOT.register_next_step_handler(msg, check_title, title_type, save_func)
    elif len(msg_text.split('\n')) > max_n:
        logging.warning(f'{chat_id} Заголовок ({title_type}) не принят, слишком много строк: {msg_text}')
        ids_to_delete[chat_id].append(message.message_id)
        msg = BOT.send_message(
            chat_id,
            text='В тексте слишком много строк. Попробуй ещё раз'
        )
        ids_to_delete[chat_id].append(msg.message_id)
        BOT.register_next_step_handler(msg, check_title, title_type, save_func)
    else:
        save_func(message)


def save_upper_title(message: types.Message) -> None:
    """
    Этап 2в: сохранение верхнего заголовка.\n
    Переход к обработке нижнего заголовка (3а)
    :param message: сообщение с проверенным верхним заголовком (2б)
    """
    chat_id = message.chat.id
    upper_title = message.text.strip().upper()
    covers_info[chat_id]['upper_title'] = upper_title
    logging.info(f'{chat_id} Сохранён верхний заголовок: {upper_title}')
    delete_messages(chat_id)
    process_lower_title(message)


def process_upper_title(message: types.Message) -> None:
    """
    Этап 2а: обработка верхнего заголовка.\n
    Переход к проверке заголовка (2б)
    :param message: сообщение из предыдущего этапа (1)
    """
    global ids_to_delete
    chat_id = message.chat.id
    ids_to_delete[chat_id] = list()
    msg = BOT.send_message(
        chat_id,
        text='Напиши название мероприятия (если больше одной строки, напиши с переносами)'
        )
    ids_to_delete[chat_id].append(msg.message_id)
    BOT.register_next_step_handler(msg, check_title, 'upper', save_upper_title)


def save_lower_title(message: types.Message) -> None:
    """
    Этап 3в: сохранение нижнего заголовка.\n
    Переход к обработке цвета (4а)
    :param message: сообщение с проверенным нижним заголовком (3б)
    """
    global covers_info
    chat_id = message.chat.id
    lower_title = message.text.strip().upper()
    covers_info[chat_id]['lower_title'] = lower_title
    logging.info(f'{chat_id} Сохранён нижний заголовок: {lower_title}')
    delete_messages(chat_id)
    process_color(chat_id, 'u')


def process_lower_title(message: types.Message) -> None:
    """
    Этап 3а: обработка нижнего заголовка.\n
    Переход к проверке заголовка (3б)
    :param message: сообщение из предыдущего этапа (2)
    """
    global ids_to_delete
    chat_id = message.chat.id
    ids_to_delete[chat_id] = list()
    msg = BOT.send_message(
        chat_id,
        text='Напиши фотографа. Если их двое, напиши имена через перенос'
        )
    ids_to_delete[chat_id].append(msg.message_id)
    BOT.register_next_step_handler(msg, check_title, 'lower', save_lower_title)


def process_color(chat_id: int, prefix: Literal['u', 'l', 'i', 'r']) -> None:
    """
    Этап 4а / 5а / 6а / 7а: обработка цвета плашки.\n
    Переход к сохранению цвета плашки (4б / 5б / 6б / 7б), обработке свободного цвета (4г / 5г / 6г / 7г)
    :param chat_id: айди чата из сообщения прошлого этапа (3, 4, 5, 6)
    :param prefix: префикс плашки, которая покрасится: ``u`` – верхняя, ``l`` – нижняя, ``i`` – левая, ``r`` – правая
    """
    global ids_to_delete
    ids_to_delete[chat_id] = list()
    markup = types.InlineKeyboardMarkup(row_width=2)
    color_btns = [types.InlineKeyboardButton(k, callback_data=prefix+'_'+v) for k, v in color2hex.items()]
    color_btns.append(types.InlineKeyboardButton('Другой', callback_data=prefix+'_other'))
    markup.add(*color_btns)

    BOT.send_message(
        chat_id,
        text=f'Выбери цвет {PREFIX2POS.get(prefix)} плашки',
        reply_markup=markup
        )


@BOT.callback_query_handler(func=lambda call: re.fullmatch(r'[ulir]_#[A-F0-9]{6}', call.data))
def save_color(call: types.CallbackQuery) -> None:
    """
    Этап 4в / 5в / 6в / 7в: сохранение цвета плашки.\n
    Переход к сохранению цвета другой плашки (5а / 6а / 7а), обработке расположения прямоугольников (8а)
    :param call: запрос от сообщения с выбором цвета (4а, 5а, 6а, 7а)
    """
    global covers_info
    chat_id = call.message.chat.id
    BOT.delete_message(chat_id, call.message.message_id)
    color = call.data[2:]
    title_fill = define_fill(color)
    cover_info = covers_info[chat_id]
    if call.data.startswith('u'):
        cover_info['upper_color'] = color
        logging.info(f'{chat_id} Сохранён верхний цвет: {color}')
        cover_info['upper_title_params']['fill'] = title_fill
        logging.info(f'{chat_id} Сохранён цвет верхнего заголовка: {title_fill}')
        process_color(chat_id, 'l')

    elif call.data.startswith('l'):
        cover_info['lower_color'] = color
        logging.info(f'{chat_id} Сохранён нижний цвет: {color}')
        cover_info['lower_title_params']['fill'] = title_fill
        logging.info(f'{chat_id} Сохранён цвет нижнего заголовка: {title_fill}')
        process_color(chat_id, 'i')

    elif call.data.startswith('i'):
        cover_info['left_color'] = color
        logging.info(f'{chat_id} Сохранён цвет левых прямоугольников: {color}')
        process_color(chat_id, 'r')

    elif call.data.startswith('r'):
        cover_info['right_color'] = color
        logging.info(f'{chat_id} Сохранён цвет правых прямоугольников: {color}')
        process_corner_forms(call)


def check_other_color(message: types.Message, prefix: Literal['u', 'l', 'i', 'r'], save_func: Callable) -> None:
    """
    Этап 4д / 5д / 6д / 7д:проверка свободного цвета.\n
    Переход к сохранению свободного цвета (4е / 5е / 6е / 7е)
    :param message: сообщение пользователя (предположительно, с HEX-кодом цвета)
    :param prefix: префикс плашки, которая покрасится: ``u`` – верхняя, ``l`` – нижняя, ``i`` – левая, ``r`` – правая
    :param save_func: функция, сохраняющая свободный цвет
    """
    msg_text = message.text
    if re.fullmatch(r'^#[0-9a-fA-F]{6}$', msg_text):
        save_func(message, prefix)
    else:
        logging.warning(f'{message.chat.id} HEX-код свободного цвета не принят: {msg_text}')
        chat_id = message.chat.id
        ids_to_delete[chat_id].append(message.message_id)
        msg = BOT.send_message(
            chat_id,
            text='HEX-код должен состоять из 7 символов (от 0 до 9, от A до F), первый из которых #'
            )
        ids_to_delete[chat_id].append(msg.message_id)
        BOT.register_next_step_handler(msg, check_other_color, prefix, save_func)


def save_other_color(message: types.Message, prefix: Literal['u', 'l', 'i', 'r']) -> None:
    """
    Этап 4е / 5е / 6е / 7е: сохранению свободного цвета.\n
    Переход к выбору цвета плашки (4а / 5а / 6а / 7а)
    :param message: сообщение с проверенным свободным цветом
    :param prefix: префикс плашки, которая покрасится: ``u`` – верхняя, ``l`` – нижняя, ``i`` – левая, ``r`` – правая
    """
    global color2hex
    chat_id = message.chat.id
    color = message.text.upper()
    color2hex[color] = color
    logging.info(f'{chat_id} Добавлен свободный цвет: {color}')
    delete_messages(chat_id)
    process_color(chat_id, prefix)


@BOT.callback_query_handler(func=lambda call: call.data.endswith('other'))
def process_other_color(call: types.CallbackQuery) -> None:
    """
    Этап 4г / 5г / 6г / 7г: обработка свободного цвета.\n
    Переход к проверке свободного цвета (4д / 5д / 6д / 7д)
    :param call: запрос от сообщения этапа 4а / 5а / 6а / 7а
    """
    chat_id = call.message.chat.id
    BOT.delete_message(chat_id, call.message.message_id)
    prefix = call.data[0]
    msg = BOT.send_message(
        chat_id,
        text='Напиши HEX-код цвета (через #)'
    )
    ids_to_delete[chat_id].append(msg.message_id)
    BOT.register_next_step_handler(msg, check_other_color, prefix, save_other_color)


def process_corner_forms(call: types.CallbackQuery) -> None:
    """
    Этап 8а: обработка расположения прямоугольников.\n
    Переход к самостоятельному составлению расположения прямоугольников (8б),
    сохранению расположения прямоугольников (8в)
    :param call: запрос от сообщения прошлого этапа (7)
    """
    chat_id = call.message.chat.id
    create_preview_pic(covers_info[chat_id], chat_id, False)
    preview_pic_path = PATH_TO_SAVE + str(call.message.chat.id) + '_' + PREVIEW_PIC_POSTFIX
    BOT.send_photo(chat_id,
                   photo=open(preview_pic_path, 'rb'),
                   caption='Выбери форму боковых плашек',
                   reply_markup=make_corner_type_markup())


previously_chosen_corner_type: Dict[int, int] = dict()
# для определения кнопки, которую нажали два раза подряд (это вызывает ошибки)


@BOT.callback_query_handler(func=lambda call: re.fullmatch(r'corner_\d{1,2}', call.data))
def change_corner_type(call: types.CallbackQuery) -> None:
    """
    Меняет тип расположения прямоугольников, редактирует сообщение с их выбором (8а)
    :param call: запрос от сообщения этапа 8а
    """
    global previously_chosen_corner_type
    chat_id = call.message.chat.id
    corner_type = int(call.data.split('_')[1])
    if corner_type == previously_chosen_corner_type.get(chat_id):
        pass
    else:
        previously_chosen_corner_type[chat_id] = corner_type
        cover_info = covers_info[chat_id]
        cover_info['corners'] = list(CORNER_COORDS[corner_type])
        logging.info(f'{chat_id} Выбран тип расположения прямоугольников {corner_type}: {cover_info["corners"]}')

        preview_pic_path = PATH_TO_SAVE + str(call.message.chat.id) + '_' + PREVIEW_PIC_POSTFIX
        my_image = Image.open(preview_pic_path)
        draw = ImageDraw.Draw(my_image)

        for coord, color_state in enumerate(cover_info['corners']):
            color_state = 1 - color_state  # инвертирование color_state (1 -> 0 или 0 -> 1) для правильного отображения
            redraw_rectangle(coord, color_state, draw, covers_info[chat_id], False)
        my_image.save(preview_pic_path)

        BOT.edit_message_media(media=types.InputMediaPhoto(open(preview_pic_path, 'rb'),
                                                           caption='Выбери форму боковых плашек'),
                               chat_id=chat_id,
                               message_id=call.message.message_id,
                               reply_markup=make_corner_type_markup())


@BOT.callback_query_handler(func=lambda call: call.data == 'custom_corner')
def process_custom_corners(call: types.CallbackQuery) -> None:
    """
    Этап 8б: самостоятельное составление расположения прямоугольников.\n
    Переход к сохранению расположения прямоугольников (8в)
    :param call: запрос от сообщения с выбором расположения прямоугольников (8а)
    """
    chat_id = call.message.chat.id
    BOT.delete_message(chat_id, call.message.message_id)

    cover_info = covers_info[chat_id]
    preview_pic_path = PATH_TO_SAVE + str(chat_id) + '_' + PREVIEW_PIC_POSTFIX
    my_image = Image.open(preview_pic_path)
    draw = ImageDraw.Draw(my_image)
    draw_preview_digits(list(range(RECTANGLE_NUM * 2)), draw, cover_info)
    my_image.save(preview_pic_path)

    BOT.send_photo(chat_id,
                   photo=open(preview_pic_path, 'rb'),
                   caption='Выбери прямоугольники, которые будут перекрашены',
                   reply_markup=make_interface_markup(CUSTOM_CORNER_PREFIX, cover_info['corners']))


@BOT.callback_query_handler(func=lambda call: call.data == f'{CUSTOM_CORNER_PREFIX}_random')
def draw_random_corners(call: types.CallbackQuery) -> None:
    """
    Рисует на изображении прямоугольники в случайном порядке,
    сохраняет данные о состоянии прямоугольников
    :param call: запрос от сообщения с самостоятельным расположением прямоугольников (8б)
    """
    chat_id = call.message.chat.id
    cover_info = covers_info[chat_id]
    random_corners = [randint(0, 1) for _ in range(RECTANGLE_NUM * 2)]
    logging.info(f'{chat_id} Сгенерированы случайное расположение прямоугольников: {random_corners}')

    preview_pic_path = PATH_TO_SAVE + str(chat_id) + '_' + PREVIEW_PIC_POSTFIX
    my_image = Image.open(preview_pic_path)
    draw = ImageDraw.Draw(my_image)

    for coord, color_state in enumerate(random_corners):
        redraw_rectangle(coord, color_state, draw, cover_info)
        logging.info(f'{chat_id} Перерисован прямоугольник {coord}: {color_state}, {cover_info["corners"]}')
    draw_preview_digits(list(range(RECTANGLE_NUM * 2)), draw, cover_info)

    my_image.save(preview_pic_path)
    edit_custom_message(call, cover_info['corners'])


@BOT.callback_query_handler(func=lambda call: re.fullmatch(CUSTOM_CORNER_PREFIX+r'_\d{1,2}_\d', call.data))
def change_custom_corner(call: types.CallbackQuery) -> None:
    """
    Обрабатывает запрос на перерисовывание прямоугольника,
    редактирует сообщение этапа 8б
    :param call: запрос от сообщения этапа 8б
    """
    chat_id = call.message.chat.id
    splitted_data = call.data.split('_')
    coord = int(splitted_data[1])
    color_state = int(splitted_data[2])

    preview_pic_path = PATH_TO_SAVE + str(chat_id) + '_' + PREVIEW_PIC_POSTFIX
    my_image = Image.open(preview_pic_path)
    draw = ImageDraw.Draw(my_image)

    cover_info = covers_info[chat_id]
    redraw_rectangle(coord, color_state, draw, cover_info)
    logging.info(f'{chat_id} Перерисован прямоугольник {coord}: {color_state}, {cover_info["corners"]}')

    my_image.save(preview_pic_path)
    edit_custom_message(call, cover_info['corners'])


@BOT.callback_query_handler(func=lambda call: call.data in ('corner_ready', f'{CUSTOM_CORNER_PREFIX}_ready'))
def save_corner_forms(call: types.CallbackQuery) -> None:
    """
    Этап 8в: сохранение расположения прямоугольников.\n
    Переход к выбору расположения копирайт-надписи (9а)
    :param call: запрос от сообщения этапа 8а / 8б
    """
    chat_id = call.message.chat.id
    logging.info(f'{chat_id} Итоговое расположение прямоугольников: {covers_info[chat_id]["corners"]}')
    BOT.delete_message(chat_id, call.message.message_id)
    process_copyright_sign(call)


def process_copyright_sign(call: types.CallbackQuery) -> None:
    """
    Этап 9а: обработка расположения копирайт-надписи.\n
    Переход к сохранению копирайт-надписи (9б)
    :param call: запрос от сообщения прошлого этапа (8а / 8б)
    """
    chat_id = call.message.chat.id
    cover_info = covers_info[chat_id]
    preview_pic_path = PATH_TO_SAVE + str(chat_id) + '_' + PREVIEW_PIC_POSTFIX
    my_image = Image.open(preview_pic_path)
    draw = ImageDraw.Draw(my_image)
    draw_preview_digits(list(range(RECTANGLE_NUM * 2)), draw, cover_info)
    my_image.save(preview_pic_path)

    BOT.send_photo(chat_id,
                   photo=open(preview_pic_path, 'rb'),
                   caption='Выбери место, куда поставить надпись «© ЛАЙВ РАБОТАЕТ»',
                   reply_markup=make_interface_markup(COPYRIGHT_SIGN_PREFIX, cover_info['corners'], False, False))


@BOT.callback_query_handler(func=lambda call: re.fullmatch(COPYRIGHT_SIGN_PREFIX+r'_\d{1,2}', call.data))
def save_copyright_coord(call: types.CallbackQuery) -> None:
    """
    Этап 9б: сохранение расположения копирайт-надписи.\n
    Переход к предварительному показу информации об обложке (10)
    :param call: запрос от сообщения этапа 9а
    """
    chat_id = call.message.chat.id
    BOT.delete_message(chat_id, call.message.message_id)
    coord = int(call.data.split('_')[1])
    covers_info[chat_id]['copyright_sign'] = coord
    logging.info(f'{chat_id} Выбрано расположение копирайт-надписи: {coord}')
    show_info(call)


def show_info(call: types.CallbackQuery) -> None:
    """
    Этап 10: предварительный показ информации об обложке.\n
    Переход к экспорту обложки (11)
    :param call: запрос от сообщения этапа 9б
    """
    chat_id = call.message.chat.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Приступить', callback_data='create-pic'))
    msg_list = []
    for k, v in covers_info[chat_id].items():
        msg_list.append(f'{k}: {v}')
        msg_list.append('\n\n')
    BOT.send_message(
        chat_id,
        text=f'Итоговая информация:\n\n{"".join(msg_list)}\n\nПриступить к сбору обложки?',
        reply_markup=markup
    )


@BOT.callback_query_handler(func=lambda call: call.data == 'create-pic')
def create_pic(call: types.CallbackQuery) -> None:
    """
    «Собирает» обложку, сохраняет её и отправляет сообщение экспортом (11)
    :param call: запрос от сообщения этапа 10
    """
    chat_id = call.message.chat.id
    cover_info = covers_info[chat_id]
    BOT.delete_message(chat_id, call.message.message_id)
    my_image = Image.new(mode='RGBA',
                         size=(PIC_WIDTH, PIC_HEIGHT),
                         color='#000000')
    draw = ImageDraw.Draw(my_image)
    draw_upper_lower_rectangles(draw, cover_info)
    draw_corners(draw, cover_info)
    draw_photo(draw, my_image, cover_info)
    draw_upper_title(draw, cover_info)
    draw_lower_title(draw, cover_info)
    draw_copyright(draw, cover_info)

    result_pic_path = PATH_TO_SAVE + str(chat_id) + '_' + RESULT_PIC_POSTFIX
    my_image.save(result_pic_path)
    logging.info(f'{chat_id} Сохранена итоговая картинка: {result_pic_path}')
    send_preview(chat_id)


def send_preview(chat_id: int) -> None:
    """
    Этап 11: экспорт обложки.\n
    Переход к экспорту в формате png (12)
    :param chat_id: айди чата
    """
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton('Экспорт .png', callback_data='export_png'))
    markup.row(types.InlineKeyboardButton('Собрать новую обложку', callback_data='restart'))

    result_pic_path = PATH_TO_SAVE + str(chat_id) + '_' + RESULT_PIC_POSTFIX
    BOT.send_photo(chat_id,
                   photo=open(result_pic_path, 'rb'),
                   caption='Готово! Выбери формат экспорта',
                   reply_markup=markup)


@BOT.callback_query_handler(func=lambda call: call.data.startswith('export'))
def export_png(call: types.CallbackQuery) -> None:
    """
    Этап 12: экспорт в формате png.\n
    Переход к подготовке перед перезапуском (13)
    :param call: запрос от сообщения этапа 11
    """
    if call.data == 'export_png':
        chat_id = call.message.chat.id
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton('Собрать новую обложку', callback_data='restart'))
        result_pic_path = PATH_TO_SAVE + str(chat_id) + '_' + RESULT_PIC_POSTFIX
        BOT.edit_message_media(media=types.InputMediaPhoto(
                               open(result_pic_path, 'rb'), caption='Готово! Выбери формат экспорта'),
                               chat_id=chat_id,
                               message_id=call.message.message_id,
                               reply_markup=markup)
        BOT.send_document(chat_id, document=open(result_pic_path, 'rb'))
        logging.info(f'{chat_id} Отправлен png-файл: {result_pic_path}')


@BOT.callback_query_handler(func=lambda call: call.data == 'restart')
def restart(call: types.CallbackQuery) -> None:
    """
    Этап 13: подготовка перед перезапуском.\n
    Переход к обработке фотографии (1а)
    :param call: запрос от сообщения этапа 11
    """
    chat_id = call.message.chat.id
    logging.info(f'{chat_id} Подготовка перед перезапуском')
    BOT.delete_message(call.message.chat.id, call.message.message_id)
    process_photo(call.message)


BOT.polling(none_stop=True)

import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACT_TOKEN')
TELEGRAM_TOKEN = os.getenv('TG_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка наличия токенов."""
    tokens = {
        'Token_pr': PRACTICUM_TOKEN,
        'Token_TG': TELEGRAM_TOKEN,
        'Chat_ID': TELEGRAM_CHAT_ID
    }
    for k, v in tokens.items():
        if not v:
            logging.critical(
                f'{k} отсутствует или пуст!'
            )
            return False
    logging.info('Tokens OK')
    return True


def send_message(bot, message):
    """Отправка ботом сообщения."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
    except telegram.TelegramError as err:
        logging.error(err)
    else:
        logging.debug('Ошибка при отправке сообщения!')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    try:
        homework = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        if homework.status_code != HTTPStatus.OK:
            logging.error('Эндпоинт недоступен!')
            homework.raise_for_status()
        else:
            logging.info('Status Code OK!')
        return homework.json()
    except requests.exceptions.RequestException:
        message = 'API не отвечает!'
        logging.error(message)
        raise message


def check_response(response):
    """Проверка запроса на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Запрос возвращает не словарь!')
    if 'homeworks' not in response:
        raise KeyError('Homeworks отсутствует')
    if not isinstance(response.get('homeworks'), list):
        raise TypeError('Status not a STR type!')
    return response.get('homeworks')


def parse_status(homework):
    """Запрос статуса домашней работы."""
    if not isinstance(homework, dict):
        raise TypeError('Отсутствует словарь!')
    if 'status' and 'homework_name' not in homework:
        raise KeyError('Homeworks or status отсутствует!')
    if not isinstance(homework.get('status'), str):
        raise ('Status not a STR type!')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError('Отсутствует homework_status!')
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    return (
        f'Изменился статус проверки работы "{homework_name}". {verdict}'
    )


def main():
    """Основная логика работы бота."""
    timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    if check_tokens():
        while True:
            try:
                response = get_api_answer(timestamp)
                homework = check_response(response)
                if len(homework) > 0:
                    send_message(bot, parse_status(homework[0]))
                    logging.debug('Сообщение отправлено в Телеграм')
                else:
                    logging.debug('Новых статусов не обнаружено!')
                time.sleep(RETRY_PERIOD)
            except Exception as error:
                send_message(bot, error)
                logging.error(
                    f'Program error: {error}!'
                )
            finally:
                time.sleep(RETRY_PERIOD)
    else:
        message = 'Ошибка! Не найден один' \
                  ' или несколько токенов! Остановка программы!'
        try:
            send_message(bot, message)
            logging.debug(
                f'Бот отправил сообщение "{message}"'
            )
        finally:
            logging.error(message)
            sys.exit


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s, %(levelname)s, %(message)s'
    )
    main()

import logging
import os
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(message)s'
)


def check_tokens():
    """Проверка наличия токенов."""
    tokens = {
        'token_pr': PRACTICUM_TOKEN,
        'token_TG': TELEGRAM_TOKEN,
        'chat_ID': TELEGRAM_CHAT_ID
    }
    for k, v in tokens.items():
        if v is not None:
            logging.info('Tokens OK')
            return True
        else:
            logging.critical(
                f'Отсутствует обязательная переменная окружения: {k}'
            )
            return False


def send_message(bot, message):
    """Отправка ботом сообщения."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logging.debug('Сообщение отправлено!')
    except Exception:
        logging.error('Ошибка при отправке сообщения!')


def get_api_answer(timestamp):
    """Запрос к эндпоинту API-сервиса."""
    try:
        homework = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        if homework.status_code != HTTPStatus.OK:
            logging.error('API response not OK!')
            raise ('ашипка!!!')
        else:
            logging.info('Status Code OK!')
        logging.info('API response OK!')
        return homework.json()
    except Exception:
        logging.error('Ошибка запроса к API!')
        raise(Exception)


def check_response(response):
    """Проверка запроса на соответствие документации."""
    if isinstance(response, dict):
        if 'homeworks' in response:
            if isinstance(response.get('homeworks'), list):
                return response.get('homeworks')
            raise TypeError('Запрос возвращает не список!')
        raise KeyError('Homeworks отсутствует')
    raise TypeError('Запрос возвращает не словарь!')


def parse_status(homework):
    """Запрос статуса домашней работы."""
    if isinstance(homework, dict):
        if 'status' and 'homework_name' in homework:
            if isinstance(homework.get('status'), str):
                homework_name = homework.get('homework_name')
                homework_status = homework.get('status')
                if homework_status in HOMEWORK_VERDICTS:
                    verdict = HOMEWORK_VERDICTS.get(homework_status)
                    return ('Изменился статус проверки работы '
                            f'"{homework_name}". {verdict}')
            raise ('Status not a STR type!')
        raise KeyError('Homeworks or status отсутствует!')
    raise TypeError('Отсутствует словарь!')


def main():
    """Основная логика работы бота."""
    timestamp = int(time.time())
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        while True:
            try:
                response = get_api_answer(timestamp)  # returns dict
                homework = check_response(response)
                if len(homework) > 0:
                    send_message(bot, parse_status(homework[0]))
                time.sleep(RETRY_PERIOD)
            except Exception as error:
                logging.error(
                    f'Program error: {error}!'
                )
                time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

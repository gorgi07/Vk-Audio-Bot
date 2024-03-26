# -----------------------------------------------------------
# Бот для получения последних сообщения из групповой беседы
# посредством токена приложения, имеющего доступ
# к VK API audio (к примеру VKAdmin). Аудио, найденные в
# сообщения, доваляются в плейлист текущего пользователя.
#
# Ссылка на получения токена c правами Messages, Audio, Offline:
# https://oauth.vk.com/authorize?client_id=6121396&scope=messages,audio,offline&redirect_uri=https://oauth.vk.com/blank.html&display=page&response_type=token&revoke=1
# -----------------------------------------------------------
from datetime import datetime
import requests
import time
from art import text2art
from colorama import init, Fore
import random
from cfg import api_version, ACCESS_TOKEN, CHAT_ID, TAG, PLAYLIST_ID, USER_ID, MY_ID, time_sleep

"""
Выводим приветствие в консоль, инициализация шрифтов
"""
print(text2art("Receiving  audio  -  VK group chat"))
init()
print(Fore.BLUE + "Бот запущен... работаем :)")


def send_message(message):
    """Метод для отправки сообщений."""
    random_id = random.getrandbits(31)
    try:
        response = requests.get(
            'https://api.vk.com/method/messages.send',
            params={
                'user_id': USER_ID,
                'message': message,
                'random_id': random_id,
                'access_token': ACCESS_TOKEN,
                'v': api_version
            }
        ).json()

        if 'response' in response:
            print(Fore.LIGHTGREEN_EX + f"Сообщение отправлено пользователю с id {USER_ID}")
        else:
            print("Ошибка при отправке сообщения:", response)

    except requests.RequestException as e:
        print("Ошибка сети:", e)


def add_audio_to_playlist(audio_id, owner_id, access_key, playlist):
    """Метод для добавления аудио в плейлист."""

    try:
        response = requests.get(
            'https://api.vk.com/method/audio.add',
            params={
                'audio_id': audio_id,
                'owner_id': owner_id,
                'access_token': ACCESS_TOKEN,
                'access_key': access_key,
                'playlist_id': playlist,
                'v': api_version,
            }
        ).json()

        if 'response' in response and response['response'] > 0:
            return True
        return False
    except requests.exceptions.RequestException as e:
        print("Произошла ошибка при отправке запроса:", e)
        return False


def get_message():
    """Метод для получения сообщений из групповой беседы."""

    try:
        response = requests.get(
            'https://api.vk.com/method/messages.getHistory',
            params={
                'access_token': ACCESS_TOKEN,
                'v': api_version,
                'peer_id': CHAT_ID,
                'count': 1,
                'offset': 0,
            }
        ).json()
        if 'response' in response:
            return response['response']['items'][0]
        return False

    except requests.exceptions.RequestException as e:
        print("Произошла ошибка при отправке запроса:", e)
        return False


def get_last_audio(album_id):
    try:
        response = requests.get(
            'https://api.vk.com/method/audio.get',
            params={
                'owner_id': album_id,  # Альбомы групп имеют отрицательный id
                'count': 1,
                'access_token': ACCESS_TOKEN,
                'v': api_version,
            }
        ).json()
        print(response)
    except Exception as e:
        print(e)


if __name__ == '__main__':

    # Лист для сохранения отработанных сообщений
    list_succ = []

    # Получаем текущее время в формате Unix time, для отрезки последнего поста (longpoll)
    current_unixtime = int(time.time())

    while True:
        try:
            message = get_message()

            if not message:
                time.sleep(time_sleep)
                continue

            # Обработка полученных записей со стены
            if message['date'] >= current_unixtime:
                if 'attachments' in message:
                    has_audio = any(attachment['type'] == 'audio' for attachment in message['attachments'])
                else:
                    has_audio = False

                # если сообщение обрабатывали - скипаем
                if message['id'] in list_succ:
                    time.sleep(time_sleep)
                    continue
                list_succ.append(message['id'])

                if message['text'].lower().find(TAG.lower()) == -1:
                    print(Fore.YELLOW + f"Сообщение {message['id']} не содержит ключевого слова.")
                    time.sleep(time_sleep)
                    continue

                if has_audio:
                    ids = ", ".join(str(playlist_id) for playlist_id in PLAYLIST_ID)
                    print(
                        Fore.LIGHTGREEN_EX + f"Сообщение {message['id']} обработано. Следующие аудио добавлены в плейлисты: {ids}")
                    str_for_message = ''
                    error = True
                    for item in message['attachments']:
                        if item['type'] == 'audio':
                            for playlist in PLAYLIST_ID:
                                if add_audio_to_playlist(item['audio']['id'], item['audio']['owner_id'],
                                                         item['audio']['access_key'], playlist):
                                    error = False

                            if not error:
                                print(
                                    Fore.GREEN + f"Аудио {item['audio']['id']}, наименование композиции - \"{item['audio']['title']}\", исполнитель {item['audio']['artist']}")
                    if not error:
                        for playlist in PLAYLIST_ID:
                            str_for_message += f'Плейлист: https://vk.com/audios{MY_ID}?section=all&z=audio_playlist{MY_ID}_{playlist}\n'
                        send_message(f"ТЕКСТ\n {str_for_message}")
                        time.sleep(2)

                        """_сон_"""
                        date = list(map(lambda x: int(x), (str(datetime.today()).split())[0].split("-")))
                        new_date = date
                        print(Fore.CYAN + f"Работа выполнена, жду следующего дня")
                        while date[0] == new_date[0] and date[1] == new_date[1] and date[2] == new_date[2]:
                            time.sleep(600)
                            new_date = list(map(lambda x: int(x), (str(datetime.today()).split())[0].split("-")))
                        print(Fore.CYAN + f"Наступил новый день {new_date[2]}-{new_date[1]}-{new_date[0]}, начинаю работу")

                else:
                    print(Fore.YELLOW + f"Сообщение {message['id']} не содержит аудио.")


        except KeyboardInterrupt:
            print(Fore.BLUE + 'Бот завершил работу... З.ы. обращайтесь еще ;) ')
            break
        except Exception as e:
            print(Fore.RED + f"Произошла ошибка: {repr(e)}")
            break
        finally:
            try:
                # пауза в try-except в целях отлавливания KeyboardInterrupt во время паузы (завершение во время паузы взывает исключение)
                time.sleep(time_sleep)
            except KeyboardInterrupt:
                print(Fore.BLUE + 'Бот завершил работу... З.ы. обращайтесь еще ;) ')

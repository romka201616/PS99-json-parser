import json
import requests
import os


def make_hashable(obj):
    """Recursively converts dicts and lists to tuples for hashability."""
    if isinstance(obj, dict):
        return tuple((k, make_hashable(v)) for k, v in sorted(obj.items()))
    if isinstance(obj, list):
        return tuple(make_hashable(elem) for elem in obj)
    return obj


def fetch_data_from_api(url):
    """Вспомогательная функция для получения JSON данных из API и обработки ошибок."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Вызывает исключение для кодов ошибок 4xx и 5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса к API: {e}")
        return None
    except json.JSONDecodeError:
        print("Ошибка декодирования JSON ответа от API")
        return None


def get_collections():
    """Получает список коллекций с API."""
    url = "https://biggamesapi.io/api/collections"
    data = fetch_data_from_api(url)
    if data and "data" in data:
        return data["data"]
    else:
        return []


def get_collection_items(collection):
    """Получает элементы коллекции с API."""
    url = f"https://biggamesapi.io/api/collection/{collection}"
    data = fetch_data_from_api(url)
    if data and "data" in data:
        return data["data"]
    else:
        return []


def update_collection_file(collection, new_items):
    """Обновляет локальный JSON-файл коллекции, добавляя новые элементы.
       Сохраняет новые элементы в отдельный файл."""
    filename = f"{collection}.json"
    new_items_folder = "new_items"
    os.makedirs(new_items_folder, exist_ok=True)
    new_items_filename = os.path.join(new_items_folder, f"{collection}_new.json")

    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f: # Добавлено encoding='utf-8' для чтения
                old_data = json.load(f)
                old_items = old_data.get("data", [])
        except json.JSONDecodeError:
            print(f"Ошибка чтения JSON из файла {filename}. Файл будет перезаписан.")
            old_items = []  # Считаем, что старых данных нет из-за ошибки чтения

        # Используем set для эффективного поиска новых элементов, предполагая уникальность элементов
        old_items_set = set(make_hashable(item) for item in old_items)
        actually_new_items = [item for item in new_items if make_hashable(item) not in old_items_set]

        if actually_new_items:
            updated_items = old_items + actually_new_items # Append new items to old items
            updated_data = {"data": updated_items}

            with open(filename, 'w', encoding='utf-8') as f: # Добавлено encoding='utf-8' для записи
                json.dump(updated_data, f, indent=2, ensure_ascii=False) # ensure_ascii=False для корректного отображения кириллицы, если есть
            print(f"Обновлен файл {filename}, добавлено {len(actually_new_items)} новых элементов.")

            with open(new_items_filename, 'w', encoding='utf-8') as f: # Добавлено encoding='utf-8' для записи
                json.dump({"data": actually_new_items}, f, indent=2, ensure_ascii=False) # Сохраняем только действительно новые элементы
            print(f"Новые элементы ({len(actually_new_items)}) сохранены в {new_items_filename}")
        else:
            print(f"Нет новых элементов для коллекции {collection}.")

    else:
        # Файл не существует, создаем его с новыми элементами
        data_to_write = {"data": new_items}
        with open(filename, 'w', encoding='utf-8') as f: # Добавлено encoding='utf-8' для записи
            json.dump(data_to_write, f, indent=2, ensure_ascii=False)
        print(f"Создан новый файл {filename} с {len(new_items)} элементами.")

        with open(new_items_filename, 'w', encoding='utf-8') as f: # Добавлено encoding='utf-8' для записи
            json.dump({"data": new_items}, f, indent=2, ensure_ascii=False)
        print(f"Все элементы ({len(new_items)}) сохранены как новые в {new_items_filename}")


def main():
    collections = get_collections()
    if collections: # Проверяем, что список коллекций не пуст
        for collection in collections:
            print(f"Обработка коллекции: {collection}")
            new_items = get_collection_items(collection)
            if new_items is not None: # Проверяем, что элементы коллекции были успешно получены
                update_collection_file(collection, new_items)
            else:
                print(f"Не удалось получить элементы для коллекции {collection}. Обновление пропущено.")
    else:
        print("Не удалось получить список коллекций. Обновление остановлено.")


if __name__ == "__main__":
    main()
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
import html # Для html.unescape

def fetch_wikitext_from_url(url):
    """
    Загружает HTML со страницы, находит textarea с id 'wpTextbox1'
    и возвращает ее содержимое, декодированное от HTML-сущностей.
    """
    print(f"Запрос данных с URL: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        print("Страница успешно загружена.")

        soup = BeautifulSoup(response.content, 'html.parser')
        textarea = soup.find('textarea', id='wpTextbox1')

        if textarea:
            raw_wikitext = textarea.get_text()
            decoded_wikitext = html.unescape(raw_wikitext)
            print("Вики-текст успешно извлечен и декодирован.")
            return decoded_wikitext
        else:
            print(f"Ошибка: Тег <textarea id='wpTextbox1'> не найден на странице {url}.")
            return None

    except requests.exceptions.Timeout:
        print(f"Ошибка: Таймаут при запросе к URL {url}.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к URL {url}: {e}")
        return None
    except Exception as e:
        print(f"Произошла непредвиденная ошибка при получении данных с URL: {e}")
        return None

def extract_pets_from_wikitext(wikitext):
    """
    Извлекает имена питомцев из вики-текста.
    Ищет блоки {{Pet-List ...}} и из них извлекает значения 'name:'.
    Все имена приводятся к нижнему регистру.
    """
    pets_in_text = set()
    pet_list_blocks = re.findall(r"\{\{Pet-List\s*\|(.*?)\}\}", wikitext, re.DOTALL)

    for block_content in pet_list_blocks:
        pet_entries = re.findall(r"name:([^;\n\}]+)", block_content)
        for pet_name in pet_entries:
            # Приводим имя к нижнему регистру перед добавлением в set
            pets_in_text.add(pet_name.strip().lower())
    return pets_in_text

def get_pets_from_excel(excel_filepath="pets.xlsx", sheet_name=0, name_column="Название товара"):
    """
    Читает имена питомцев из указанной колонки Excel файла.
    Все имена приводятся к нижнему регистру.
    """
    try:
        df = pd.read_excel(excel_filepath, sheet_name=sheet_name)
        if name_column not in df.columns:
            print(f"Ошибка: Колонка '{name_column}' не найдена в файле '{excel_filepath}'.")
            print(f"Доступные колонки: {list(df.columns)}")
            return None

        # Убедимся, что данные читаются как строки, удаляем NA, убираем пробелы И приводим к нижнему регистру
        pets_in_excel = set(df[name_column].dropna().astype(str).str.strip().str.lower())
        return pets_in_excel
    except FileNotFoundError:
        print(f"Ошибка: Файл '{excel_filepath}' не найден в корневой папке программы.")
        return None
    except Exception as e:
        print(f"Произошла ошибка при чтении Excel файла: {e}")
        return None

# --- Основная часть программы ---

wiki_url = "https://bgs-infinity.fandom.com/wiki/Bubble_Gum_Simulator_INFINITY_Wiki:Data/Pets?action=edit"
wiki_content = fetch_wikitext_from_url(wiki_url)

if wiki_content:
    pets_from_text = extract_pets_from_wikitext(wiki_content)
    if pets_from_text:
        print(f"Найдено {len(pets_from_text)} уникальных питомцев (без учета регистра) на вики-странице.")
    else:
        print("Не найдено питомцев на вики-странице.")

    excel_filepath = "pets.xlsx"
    column_name_in_excel = "Название товара"
    pets_from_excel = get_pets_from_excel(excel_filepath, name_column=column_name_in_excel)

    if pets_from_excel is not None and pets_from_text:
        print(f"Найдено {len(pets_from_excel)} уникальных питомцев (без учета регистра) в таблице Excel.")

        missing_in_excel = pets_from_text - pets_from_excel

        if missing_in_excel:
            print("\n--- Питомцы, которые есть на вики (без учета регистра), но отсутствуют в Excel (без учета регистра): ---")
            # Выводим имена в нижнем регистре, так как они хранились в set
            for i, pet_name in enumerate(sorted(list(missing_in_excel)), 1):
                print(f"{i}. {pet_name}")
        else:
            print("\nВсе питомцы с вики-страницы (без учета регистра) присутствуют в таблице Excel (без учета регистра).")
    elif not pets_from_text and pets_from_excel is not None:
         print("Не удалось извлечь питомцев с вики, но данные из Excel загружены. Сравнение невозможно.")
    elif pets_from_excel is None:
        print("Не удалось загрузить данные из Excel, сравнение невозможно.")
else:
    print("Не удалось получить вики-текст с URL, анализ невозможен.")
import os
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from collections import defaultdict
import logging


# Директорія для створення тестових файлів
FILE_DIR = "text_files"
# Кількість файлів для створення
NUM_FILES = 20
# Ключові слова для пошуку
KEYWORDS = ["Python", "multiprocessing", "threading", "file", "test", "benchmark"]

# Налаштування логування для виводу помилок
logging.basicConfig(
    level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s"
)


def setup_environment(directory, num_files, keywords):
    """Створює директорію та набір тестових файлів з вмістом."""
    print(f"--- 🚀 Початок налаштування середовища ---")
    path = Path(directory)
    path.mkdir(exist_ok=True)

    # Очищення старих файлів
    for f in path.glob("*.txt"):
        try:
            os.remove(f)
        except OSError as e:
            logging.error(f"Не вдалося видалити {f}: {e}")

    # Вміст для файлів (деякі з ключовими словами, деякі без)
    file_contents = [
        "Це простий test file.",
        "Тут ми говоримо про Python.",
        "Python і threading - це потужні інструменти.",
        "Багатопотоковість (threading) може бути складною.",
        "Цей file не містить ключових слів.",
        "multiprocessing в Python дозволяє обійти GIL.",
        "Це ще один test для benchmark.",
        "Python, threading, та multiprocessing - все в одному file.",
        "Просто текст, нічого цікавого.",
        "Обробка file є типовим завданням.",
    ]

    count = 0
    for i in range(num_files):
        try:
            file_path = path / f"file_{i+1}.txt"
            content = file_contents[i % len(file_contents)]

            # Додамо великий обсяг тексту, щоб зробити пошук більш CPU-залежним
            content += " ... (багато тексту) ..." * (
                500 * (i % 5 + 1)
            )  # Робимо файли різного розміру

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            count += 1
        except IOError as e:
            logging.error(f"Не вдалося створити {file_path}: {e}")

    print(f"Створено {count} файлів у директорії '{directory}'.")
    print(f"--- ✅ Налаштування завершено ---\n")
    return [path / f"file_{i+1}.txt" for i in range(num_files)]


def search_in_file(file_path, keywords):
    """
    Шукає ключові слова в одному файлі.
    Повертає словник {keyword: [file_path]} для знайдених слів.
    """
    found_keywords = defaultdict(list)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            for keyword in keywords:
                if keyword in content:
                    found_keywords[keyword].append(str(file_path))
    except FileNotFoundError:
        logging.error(f"Файл не знайдено: {file_path}")
    except IOError as e:
        logging.error(f"Помилка читання файлу {file_path}: {e}")
    except Exception as e:
        logging.error(f"Невідома помилка при обробці {file_path}: {e}")

    return found_keywords


def merge_results(results):
    """Об'єднує список результатів (зі словників) в один фінальний словник."""
    final_results = defaultdict(list)
    for res in results:
        for keyword, files in res.items():
            final_results[keyword].extend(files)
    return final_results


def run_search_threading(file_list, keywords):
    """Виконує пошук за допомогою ThreadPoolExecutor."""
    print("--- 🏁 Початок БАГАТОПОТОКОВОГО пошуку (threading) ---")
    start_time = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        # Передаємо кожному потоку функцію та аргументи
        futures = [
            executor.submit(search_in_file, file, keywords) for file in file_list
        ]

        for future in futures:
            results.append(future.result())

    final_results = merge_results(results)

    end_time = time.time()
    print(f"--- ⏱️  Час виконання (threading): {end_time - start_time:.4f} секунд ---")
    return final_results


def run_search_multiprocessing(file_list, keywords):
    """
    Виконує пошук за допомогою ProcessPoolExecutor.
    Це реалізує критерій "розподіл файлів між процесами"
    та "механізм обміну даними" (який Executor робить автоматично).
    """
    print("\n--- 🏁 Початок БАГАТОПРОЦЕСОРНОГО пошуку (multiprocessing) ---")
    start_time = time.time()
    results = []

    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        # Передаємо кожному процесу функцію та аргументи
        futures = [
            executor.submit(search_in_file, file, keywords) for file in file_list
        ]

        for future in futures:
            results.append(future.result())

    final_results = merge_results(results)

    end_time = time.time()
    print(
        f"--- ⏱️  Час виконання (multiprocessing): {end_time - start_time:.4f} секунд ---"
    )
    return final_results


def main():
    try:
        file_paths = setup_environment(FILE_DIR, NUM_FILES, KEYWORDS)
    except Exception as e:
        logging.error(f"Критична помилка при налаштуванні середовища: {e}")
        sys.exit(1)

    if not file_paths:
        print("Не вдалося створити тестові файли. Вихід.")
        sys.exit(1)

    print(f"Пошук ключових слів: {KEYWORDS}\n")

    thread_results = run_search_threading(file_paths, KEYWORDS)
    print("Результати (threading):")
    for key, files in thread_results.items():
        print(f"  '{key}': знайдено у {len(files)} файлах")

    multi_results = run_search_multiprocessing(file_paths, KEYWORDS)
    print("Результати (multiprocessing):")
    for key, files in multi_results.items():
        print(f"  '{key}': знайдено у {len(files)} файлах")

    print("\n--- 📊 Перевірка результатів ---")
    if thread_results == multi_results:
        print("✅ Успіх! Обидва методи дали однакові результати.")
    else:
        print("❌ Помилка! Результати відрізняються.")

    print("\nПримітка: Ця задача є змішаною (I/O-bound та CPU-bound).")
    print(
        "Threading ефективний для I/O (читання файлів), multiprocessing - для CPU (пошук у великому тексті)."
    )
    print(
        "Залежно від розміру файлів та швидкості диска, один з методів може бути швидшим."
    )


if __name__ == "__main__":
    main()

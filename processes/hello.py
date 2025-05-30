import time
import argparse
import os

if __name__ == "__main__":
    # Парсим аргументы командной строки
    parser = argparse.ArgumentParser()
    parser.add_argument("-dir", "--directory", type=str, default="./processes", help="Директория для сохранения файла")
    parser.add_argument("-m", "--message", type=str)
    parser.add_argument("-f", "--file", type=str, default="data.txt")
    parser.add_argument("-t", "--time", type=int, default=5)
    args = parser.parse_args()

    # Проверяем/создаём директорию
    os.makedirs(args.directory, exist_ok=True)

    file_path = os.path.join(args.directory, args.file)
    message = args.message
    try:
        with open(file_path, "a", encoding="utf-8") as file:
            while True:
                file.write(f'{message}\n')
                file.flush()
                time.sleep(args.time)
    except Exception as e:
        print(f"Ошибка: {e}")
    except KeyboardInterrupt:
        print("Программа остановлена пользователем")
import time

if __name__ == "__main__":
    try:
        with open("./processes/data.txt", "a", encoding="utf-8") as file:
            while True:
                file.write("Hello world!\n")
                file.flush()
                time.sleep(5)
    except Exception as e:
        print(f"Ошибка: {e}")
    except KeyboardInterrupt:
        print("Программа остановлена пользователем")
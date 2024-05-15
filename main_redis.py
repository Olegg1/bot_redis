import telebot
import redis

try:
    bot = telebot.TeleBot('Token')
    r = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

    def user_exists(user_id):
        return r.hexists(f"user:{user_id}", "name")

    @bot.message_handler(commands=['start'])
    def handle_start(message):
        bot.send_message(message.chat.id, "Привет! Я ваш телеграм-бот. Для создания профиля отправьте команду /create.")

    @bot.message_handler(commands=['create'])
    def create_profile(message):
        user_id = message.from_user.id
        if user_exists(user_id):
            bot.send_message(message.chat.id, "Профиль уже существует. Используйте команду /update для изменения профиля.")
        else:
            sent_msg = bot.send_message(message.chat.id, "Введите ваше имя:")
            bot.register_next_step_handler(sent_msg, process_name_step)

    def process_name_step(message):
        name = message.text
        user_id = message.from_user.id
        r.hset(f"user:{user_id}", "name", name)
        sent_msg = bot.send_message(message.chat.id, "Введите ваш возраст:")
        bot.register_next_step_handler(sent_msg, process_age_step)

    def process_age_step(message):
        age = message.text
        user_id = message.from_user.id
        r.hset(f"user:{user_id}", "age", age)
        bot.send_message(message.chat.id, f"Профиль создан. Ваше имя: {r.hget(f'user:{user_id}', 'name')}, возраст: {age}.")

    @bot.message_handler(commands=['delete'])
    def delete_profile(message):
        user_id = message.from_user.id
        if user_exists(user_id):
            r.delete(f"user:{user_id}")
            bot.send_message(message.chat.id, "Ваш профиль удален.")
        else:
            bot.send_message(message.chat.id, "Профиль не найден.")

    @bot.message_handler(commands=['update'])
    def update_profile(message):
        user_id = message.from_user.id
        if user_exists(user_id):
            sent_msg = bot.send_message(message.chat.id, "Введите новую информацию (формат: имя, возраст):")
            bot.register_next_step_handler(sent_msg, process_update_step)
        else:
            bot.send_message(message.chat.id, "Профиль не найден. Используйте команду /create для создания нового профиля.")

    def process_update_step(message):
        user_id = message.from_user.id
        try:
            name, age = message.text.split(", ")
            r.hset(f"user:{user_id}", "name", name)
            r.hset(f"user:{user_id}", "age", age)
            bot.send_message(message.chat.id, "Ваш профиль обновлен.")
        except ValueError:
            bot.send_message(message.chat.id, "Неверный формат. Попробуйте еще раз.")

    @bot.message_handler(commands=['admin'])
    def admin_actions(message):
        sent_msg = bot.send_message(message.chat.id, "Введите команду (view_all, delete_all):")
        bot.register_next_step_handler(sent_msg, process_admin_command)

    def process_admin_command(message):
        command = message.text
        print(command)
        if command == "view_all":
            keys = r.keys("user:*")
            users = {key: r.hgetall(key) for key in keys}
            bot.send_message(message.chat.id, f"Все пользователи:\n" + "\n".join([f"{key}: {value}" for key, value in users.items()]))
        elif command == "delete_all":
            keys = r.keys("user:*")
            for key in keys:
                r.delete(key)
            bot.send_message(message.chat.id, "Все профили удалены.")
        else:
            bot.send_message(message.chat.id, "Неизвестная команда. Попробуйте еще раз.")

    bot.polling()
except redis.exceptions.ConnectionError:
    print("Ошибка подключения к Redis.")
except redis.exceptions.TimeoutError:
    print("Превышено время ожидания при работе с Redis.")
except redis.exceptions.AuthenticationError:
    print("Ошибка аутентификации при подключении к Redis.")
except Exception as e:
    print(f"Произошла неизвестная ошибка: {e}")

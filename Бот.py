import asyncio
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from rcon.source import Client

BOT_TOKEN = "9287901758:AAERevqDX5Q5FTXVK-qUfjMc8ZHnd0pl7Lo"
ADMIN_ID = 7669007088
SERVER_IP = "LeafSmp.minerent.io"

RCON_HOST = "5.188.118.29"   
RCON_PORT = 21188            
RCON_PASS = "LeafSmp_Super_2026!" 

class UserStates(StatesGroup):
    waiting_for_nick = State()
    waiting_for_2fa_code = State()

class AdminStates(StatesGroup):
    waiting_for_admin_nick = State()
    waiting_for_admin_donate = State()
    waiting_for_unreg_nick = State()
    waiting_for_2fareset_nick = State()
    waiting_for_regacc_nick = State()
    waiting_for_regacc_pass = State()
    waiting_for_editpass_nick = State()
    waiting_for_editpass_pass = State()
    waiting_for_remove_donate_nick = State()
    waiting_for_remove_donate_group = State()
    waiting_for_admin_group_nick = State()
    waiting_for_admin_group_type = State()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def _sync_rcon(command: str):
    try:
        with Client(RCON_HOST, RCON_PORT, passwd=RCON_PASS, timeout=5) as client:
            resp = client.run(command)
            return True, resp
    except Exception as e:
        return False, str(e)

async def rcon_exec(command: str):
    return _sync_rcon(command)

async def get_online_players():
    ok, resp = await rcon_exec("list")
    if not ok or "There are" not in resp:
        return []
    match = re.search(r"online:\s*(.*)", resp)
    if match and match.group(1):
        return [name.strip() for name in match.group(1).split(",")]
    return []

def main_dashboard(user_id):
    kb = ReplyKeyboardBuilder()
    kb.button(text="🎮 IP Сервера")
    kb.button(text="💎 Купить донат")
    kb.button(text="🔐 Привязать 2FA")
    kb.button(text="📖 Гайд по 2FA")
    if user_id == ADMIN_ID:
        kb.button(text="⚙️ Админ-панель")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)

def donate_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🍃 Леший — 99₽", callback_data="donate_leshiy")
    kb.button(text="🐝 Шмель — 249₽", callback_data="donate_shmel")
    kb.button(text="🛡 Варден — 499₽", callback_data="donate_varden")
    kb.adjust(1)
    return kb.as_markup()

def admin_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🎁 Выдать донат", callback_data="admin_give")
    kb.button(text="🗑 Удалить донат", callback_data="admin_remove_donate")
    kb.button(text="👑 Выдать админку", callback_data="admin_give_admins")
    kb.button(text="🔓 Сбросить 2FA", callback_data="admin_2fareset")
    kb.button(text="🗑 Анрегнуть игрока", callback_data="admin_unreg")
    kb.button(text="✏️ Сменить пароль", callback_data="admin_editpass")
    kb.button(text="📝 Зарегистрировать", callback_data="admin_regacc")
    kb.button(text="🔍 Проверка RCON", callback_data="admin_test_rcon")
    kb.adjust(1)
    return kb.as_markup()

def admin_donate_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="Выдать Лешего", callback_data="give_leshiy")
    kb.button(text="Выдать Шмеля", callback_data="give_shmel")
    kb.button(text="Выдать Вардена", callback_data="give_varden")
    kb.adjust(1)
    return kb.as_markup()

def admin_remove_donate_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="Убрать Лешего", callback_data="remove_leshiy")
    kb.button(text="Убрать Шмеля", callback_data="remove_shmel")
    kb.button(text="Убрать Вардена", callback_data="remove_varden")
    kb.adjust(1)
    return kb.as_markup()

def admin_groups_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="Хелпер", callback_data="give_group_helper")
    kb.button(text="Модер", callback_data="give_group_moder")
    kb.button(text="Куратор", callback_data="give_group_curator")
    kb.button(text="Админ", callback_data="give_group_admin")
    kb.adjust(2)
    return kb.as_markup()

async def process_link_code(message: types.Message, raw_code: str):
    code = raw_code.strip()
    if not code.isdigit() or len(code) != 6:
        await message.answer("❌ Код должен состоять ровно из 6 цифр!\nПример: /2fa 123456")
        return

    cmd = f"leaflogin linktg {code} {message.from_user.id}"
    ok, resp = await rcon_exec(cmd)

    if ok and "SUCCESS" in resp:
        await message.answer("✅ **2FA успешно привязана!**", reply_markup=main_dashboard(message.from_user.id))
    elif ok and "CODE_NOT_FOUND" in resp:
        await message.answer("❌ Код не найден.\nВведите /2fa в игре заново.", reply_markup=main_dashboard(message.from_user.id))
    else:
        await message.answer(f"❌ Ошибка RCON:\n{resp}", reply_markup=main_dashboard(message.from_user.id))

@dp.message(Command("start"))
async def start(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) > 1 and parts[1].startswith("link_"):
        code = parts[1].replace("link_", "").strip()
        await process_link_code(message, code)
        return

    text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Добро пожаловать в бота сервера **LeafSMP**!\n"
        "Используйте кнопки внизу экрана."
    )
    await message.answer(text, reply_markup=main_dashboard(message.from_user.id), parse_mode="Markdown")

@dp.message(Command("2fa"))
async def cmd_2fa(message: types.Message, state: FSMContext):
    await state.clear()
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Укажите код:\n/2fa 123456")
        return
    await process_link_code(message, parts[1])

@dp.message(F.text == "🎮 IP Сервера")
async def show_ip(message: types.Message):
    await message.answer(f"🎮 **Подключение:**\n`{SERVER_IP}`\nВерсия: **1.21.11**", parse_mode="Markdown")

@dp.message(F.text == "📖 Гайд по 2FA")
async def guide_2fa(message: types.Message):
    text = (
        "📖 **Гайд по привязке Telegram 2FA:**\n\n"
        "1. Напишите в чат игры: /2fa\n"
        "2. Получите 6-значный код.\n"
        "3. Отправьте его сюда: /2fa 123456"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🔐 Привязать 2FA")
async def link_2fa_click(message: types.Message, state: FSMContext):
    await message.answer("🔐 **Введите 6-значный код из игры:**")
    await state.set_state(UserStates.waiting_for_2fa_code)

@dp.message(UserStates.waiting_for_2fa_code)
async def link_2fa_receive_code(message: types.Message, state: FSMContext):
    await state.clear()
    await process_link_code(message, message.text)

@dp.message(F.text == "💎 Купить донат")
async def show_donates(message: types.Message):
    text = (
        "Выбери привилегию:\n\n"
        "🍃 **Леший (99₽)**\n"
        "🐝 **Шмель (249₽)**\n"
        "🛡 **Варден (499₽)**"
    )
    await message.answer(text, reply_markup=donate_menu(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("donate_"))
async def process_donate(callback: types.CallbackQuery, state: FSMContext):
    item = callback.data.split("_")[1]
    names = {"leshiy": "Леший", "shmel": "Шмель", "varden": "Варден"}
    prices = {"leshiy": "99", "shmel": "249", "varden": "499"}

    await callback.message.answer(f"Вы выбрали **{names[item]}** за **{prices[item]}₽**.\n\nВведите свой ник в игре:", parse_mode="Markdown")
    await state.update_data(item=item)
    await state.set_state(UserStates.waiting_for_nick)
    await callback.answer()

@dp.message(UserStates.waiting_for_nick)
async def get_nick_for_payment(message: types.Message, state: FSMContext):
    nick = message.text.strip()
    data = await state.get_data()
    item = data.get('item', 'leshiy')
    names = {"leshiy": "Леший", "shmel": "Шмель", "varden": "Варден"}
    prices = {"leshiy": "99", "shmel": "249", "varden": "499"}

    await message.answer(f"Ник **{nick}** записан!\nЗаявка отправлена админу.", parse_mode="Markdown")

    admin_text = (
        f"💰 **Новая заявка на донат!**\n\n"
        f"Игрок: {message.from_user.first_name}\n"
        f"Юзернейм: @{message.from_user.username}\n"
        f"Ник в игре: **{nick}**\n"
        f"Привилегия: **{names[item]}** ({prices[item]}₽)\n"
        f"ID: `{message.from_user.id}`"
    )
    try:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    except Exception:
        pass
    await state.clear()

@dp.callback_query(F.data.startswith("2fa_allow:"))
async def handle_2fa_allow(callback: types.CallbackQuery):
    nick = callback.data.split(":", 1)[1]
    cmd = f"leaflogin 2faapprove {nick}"
    ok, resp = await rcon_exec(cmd)
    if ok and "SUCCESS" in resp:
        await callback.message.edit_text(f"✅ Вход для **{nick}** подтверждён!", parse_mode="Markdown")
    else:
        await callback.message.edit_text(f"❌ Ошибка авторизации:\n{resp}")

@dp.callback_query(F.data.startswith("2fa_deny:"))
async def handle_2fa_deny(callback: types.CallbackQuery):
    nick = callback.data.split(":", 1)[1]
    cmd = f"leaflogin 2fadeny {nick}"
    ok, resp = await rcon_exec(cmd)
    if ok and "SUCCESS" in resp:
        await callback.message.edit_text(f"⛔ Вход для **{nick}** отклонён!", parse_mode="Markdown")
    else:
        await callback.message.edit_text(f"❌ Ошибка:\n{resp}")

@dp.message(F.text == "⚙️ Админ-панель")
async def show_admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("⚙️ **Админ-панель LeafSMP:**", reply_markup=admin_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "admin_test_rcon")
async def admin_test_rcon(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.answer("⏳ Проверяю соединение с RCON...")
    ok, resp = await rcon_exec("list")
    if ok:
        await callback.message.answer(f"✅ Успех! Связь есть.\nОтвет сервера: {resp}")
    else:
        await callback.message.answer(f"❌ Ошибка!\nПричина: {resp}")
    await callback.answer()

@dp.callback_query(F.data == "admin_give")
async def admin_give_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    players = await get_online_players()
    
    if players:
        kb = InlineKeyboardBuilder()
        for p in players:
            kb.button(text=p, callback_data=f"select_give_{p}")
        kb.adjust(2)
        await callback.message.answer("Выберите игрока для выдачи доната (или введите ник вручную):", reply_markup=kb.as_markup())
    else:
        await callback.message.answer("На сервере нет игроков онлайн. Введите ник вручную:")
    
    await state.set_state(AdminStates.waiting_for_admin_nick)
    await callback.answer()

@dp.callback_query(F.data.startswith("select_give_"))
async def admin_give_select(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    nick = callback.data.replace("select_give_", "")
    await state.update_data(target_nick=nick)
    await callback.message.answer(f"Игрок: **{nick}**.\nВыберите донат:", reply_markup=admin_donate_menu(), parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_admin_donate)
    await callback.answer()

@dp.message(AdminStates.waiting_for_admin_nick)
async def admin_get_nick(message: types.Message, state: FSMContext):
    await state.update_data(target_nick=message.text.strip())
    await message.answer(f"Игрок: **{message.text.strip()}**.\nВыберите донат:", reply_markup=admin_donate_menu(), parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_admin_donate)

@dp.callback_query(AdminStates.waiting_for_admin_donate, F.data.startswith("give_"))
async def admin_give_final(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    target_nick = data.get('target_nick')
    item = callback.data.split("_")[1]
    group_name = {"leshiy": "леший", "shmel": "шмель", "varden": "варден"}[item]
    
    success, resp = await rcon_exec(f"lp user {target_nick} parent add {group_name}")
    if success:
        await callback.message.answer(f"✅ Донат **{group_name}** выдан **{target_nick}**!\nОтвет: `{resp}`", parse_mode="Markdown")
    else:
        await callback.message.answer(f"❌ Ошибка:\n{resp}")
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "admin_remove_donate")
async def admin_remove_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    players = await get_online_players()
    
    if players:
        kb = InlineKeyboardBuilder()
        for p in players:
            kb.button(text=p, callback_data=f"select_remove_{p}")
        kb.adjust(2)
        await callback.message.answer("Выберите игрока для снятия доната (или введите ник вручную):", reply_markup=kb.as_markup())
    else:
        await callback.message.answer("На сервере нет игроков. Введите ник вручную:")
        
    await state.set_state(AdminStates.waiting_for_remove_donate_nick)
    await callback.answer()

@dp.callback_query(F.data.startswith("select_remove_"))
async def admin_remove_select(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    nick = callback.data.replace("select_remove_", "")
    await state.update_data(target_nick=nick)
    await callback.message.answer(f"Игрок: **{nick}**.\nВыберите, какой донат снять:", reply_markup=admin_remove_donate_menu(), parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_remove_donate_group)
    await callback.answer()

@dp.message(AdminStates.waiting_for_remove_donate_nick)
async def admin_remove_get_nick(message: types.Message, state: FSMContext):
    await state.update_data(target_nick=message.text.strip())
    await message.answer(f"Игрок: **{message.text.strip()}**.\nВыберите, какой донат снять:", reply_markup=admin_remove_donate_menu(), parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_remove_donate_group)

@dp.callback_query(AdminStates.waiting_for_remove_donate_group, F.data.startswith("remove_"))
async def admin_remove_final(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    target_nick = data.get('target_nick')
    item = callback.data.split("_")[1]
    group_name = {"leshiy": "леший", "shmel": "шмель", "varden": "варден"}[item]
    
    success, resp = await rcon_exec(f"lp user {target_nick} parent remove {group_name}")
    if success:
        await callback.message.answer(f"✅ Группа **{group_name}** снята с **{target_nick}**!\nОтвет: `{resp}`", parse_mode="Markdown")
    else:
        await callback.message.answer(f"❌ Ошибка:\n{resp}")
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "admin_give_admins")
async def admin_admins_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    players = await get_online_players()
    
    if players:
        kb = InlineKeyboardBuilder()
        for p in players:
            kb.button(text=p, callback_data=f"select_admin_{p}")
        kb.adjust(2)
        await callback.message.answer("Выберите игрока для выдачи админ-прав (или введите ник вручную):", reply_markup=kb.as_markup())
    else:
        await callback.message.answer("На сервере нет игроков. Введите ник вручную:")
        
    await state.set_state(AdminStates.waiting_for_admin_group_nick)
    await callback.answer()

@dp.callback_query(F.data.startswith("select_admin_"))
async def admin_admins_select(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    nick = callback.data.replace("select_admin_", "")
    await state.update_data(target_nick=nick)
    await callback.message.answer(f"Игрок: **{nick}**.\nВыберите группу для выдачи:", reply_markup=admin_groups_menu(), parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_admin_group_type)
    await callback.answer()

@dp.message(AdminStates.waiting_for_admin_group_nick)
async def admin_admins_get_nick(message: types.Message, state: FSMContext):
    await state.update_data(target_nick=message.text.strip())
    await message.answer(f"Игрок: **{message.text.strip()}**.\nВыберите группу для выдачи:", reply_markup=admin_groups_menu(), parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_admin_group_type)

@dp.callback_query(AdminStates.waiting_for_admin_group_type, F.data.startswith("give_group_"))
async def admin_admins_final(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    target_nick = data.get('target_nick')
    item = callback.data.replace("give_group_", "")
    
    group_name = {
        "helper": "хелпер", 
        "moder": "модер", 
        "curator": "куратор", 
        "admin": "админ"
    }[item]
    
    success, resp = await rcon_exec(f"lp user {target_nick} parent add {group_name}")
    if success:
        await callback.message.answer(f"✅ Админ-права **{group_name}** выданы **{target_nick}**!\nОтвет: `{resp}`", parse_mode="Markdown")
    else:
        await callback.message.answer(f"❌ Ошибка:\n{resp}")
    await state.clear()
    await callback.answer()

@dp.callback_query(F.data == "admin_2fareset")
async def admin_2fareset_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.answer("Введите ник игрока, которому сбросить 2FA:")
    await state.set_state(AdminStates.waiting_for_2fareset_nick)
    await callback.answer()

@dp.message(AdminStates.waiting_for_2fareset_nick)
async def admin_2fareset_final(message: types.Message, state: FSMContext):
    nick = message.text.strip()
    ok, resp = await rcon_exec(f"leaflogin 2fareset {nick}")
    await message.answer(f"Результат сброса 2FA:\n{resp}")
    await state.clear()

@dp.callback_query(F.data == "admin_unreg")
async def admin_unreg_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.answer("Введите ник для анрега:")
    await state.set_state(AdminStates.waiting_for_unreg_nick)
    await callback.answer()

@dp.message(AdminStates.waiting_for_unreg_nick)
async def admin_unreg_final(message: types.Message, state: FSMContext):
    nick = message.text.strip()
    ok, resp = await rcon_exec(f"leaflogin unreg {nick}")
    await message.answer(f"Результат:\n{resp}")
    await state.clear()

@dp.callback_query(F.data == "admin_editpass")
async def admin_editpass_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.answer("Введите ник для смены пароля:")
    await state.set_state(AdminStates.waiting_for_editpass_nick)
    await callback.answer()

@dp.message(AdminStates.waiting_for_editpass_nick)
async def admin_editpass_get_pass(message: types.Message, state: FSMContext):
    await state.update_data(edit_nick=message.text.strip())
    await message.answer("Введите новый пароль:")
    await state.set_state(AdminStates.waiting_for_editpass_pass)

@dp.message(AdminStates.waiting_for_editpass_pass)
async def admin_editpass_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    nick = data['edit_nick']
    new_pass = message.text.strip()
    ok, resp = await rcon_exec(f"leaflogin editpass {nick} {new_pass}")
    await message.answer(f"Результат:\n{resp}")
    await state.clear()

@dp.callback_query(F.data == "admin_regacc")
async def admin_regacc_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await callback.message.answer("Введите ник для регистрации:")
    await state.set_state(AdminStates.waiting_for_regacc_nick)
    await callback.answer()

@dp.message(AdminStates.waiting_for_regacc_nick)
async def admin_regacc_get_pass(message: types.Message, state: FSMContext):
    await state.update_data(reg_nick=message.text.strip())
    await message.answer("Введите пароль:")
    await state.set_state(AdminStates.waiting_for_regacc_pass)

@dp.message(AdminStates.waiting_for_regacc_pass)
async def admin_regacc_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    nick = data['reg_nick']
    passw = message.text.strip()
    ok, resp = await rcon_exec(f"leaflogin regacc {nick} {passw}")
    await message.answer(f"Результат:\n{resp}")
    await state.clear()

@dp.message(F.text & ~F.text.startswith('/'))
async def any_message(message: types.Message):
    if message.from_user.id == ADMIN_ID: return
    user = message.from_user
    username = f"@{user.username}" if user.username else "Нет юзернейма"
    admin_text = f"📬 **Сообщение от игрока**\n\nИгрок: {user.first_name}\nЮзернейм: {username}\nID: `{user.id}`\n\nТекст:\n{message.text}"
    try:
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
        await message.answer("Сообщение отправлено админу!")
    except Exception:
        await message.answer("Не удалось отправить.")

@dp.message(F.reply_to_message)
async def admin_reply(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    if "ID: `" in message.reply_to_message.text:
        try:
            user_id = int(message.reply_to_message.text.split("ID: `")[1].split("`")[0])
            await bot.send_message(user_id, f"👨‍💻 **Ответ от админа:**\n\n{message.text}", parse_mode="Markdown")
            await message.answer("Ответ отправлен.")
        except Exception:
            await message.answer("Не удалось отправить.")
    else:
        await message.answer("Ответьте (Reply) на сообщение с ID.")

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
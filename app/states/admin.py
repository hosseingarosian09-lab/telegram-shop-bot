from aiogram.fsm.state import State, StatesGroup


class CategoryAdminStates(StatesGroup):
    waiting_new_name = State()
    waiting_edit_name = State()


class ProductAddStates(StatesGroup):
    waiting_category = State()
    waiting_name = State()
    waiting_author = State()
    waiting_price = State()
    waiting_stock = State()
    waiting_description = State()
    waiting_image = State()


class ProductEditStates(StatesGroup):
    waiting_value = State()
    waiting_image = State()

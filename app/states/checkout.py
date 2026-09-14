from aiogram.fsm.state import State, StatesGroup


class CheckoutStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()
    confirming = State()

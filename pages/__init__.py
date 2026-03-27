from nicegui import ui

STATUS_LABELS = {
    'w_magazynie': 'W magazynie',
    'aktywny': 'Aktywny',
    'sprzedany': 'Sprzedany',
    'zdjety': 'Zdjety z ogloszenia',
    'do_likwidacji': 'Do likwidacji',
}

STATUS_COLORS = {
    'w_magazynie': 'grey',
    'aktywny': 'blue',
    'sprzedany': 'green',
    'zdjety': 'orange',
    'do_likwidacji': 'red',
}

STATUS_OPTIONS = {
    'w_magazynie': 'W magazynie',
    'aktywny': 'Aktywny',
    'sprzedany': 'Sprzedany',
    'zdjety': 'Zdjety z ogloszenia',
}


def create_header():
    with ui.header().classes('items-center bg-blue-900'):
        with ui.row().classes('w-full items-center'):
            ui.button('SellTrack', on_click=lambda: ui.navigate.to('/'), icon='inventory_2') \
                .props('flat color=white').classes('text-lg')
            ui.space()
            ui.button('Dodaj', on_click=lambda: ui.navigate.to('/items/add'), icon='add') \
                .props('flat color=white')
            ui.button('Kategorie', on_click=lambda: ui.navigate.to('/categories'), icon='category') \
                .props('flat color=white')


def create_date_input(label: str, value: str = '') -> ui.input:
    """Date input with calendar picker popup."""
    with ui.input(label, value=value).props('clearable') as inp:
        with inp.add_slot('append'):
            ui.icon('edit_calendar').on('click', lambda: menu.open()).classes('cursor-pointer')
        with ui.menu() as menu:
            ui.date(value=value or None,
                    on_change=lambda e: (inp.set_value(e.value), menu.close()))
    return inp

from nicegui import ui

from db import get_db
from models import Category, Item
from pages import create_header


@ui.page('/categories')
def category_list():
    create_header()

    with ui.column().classes('w-full max-w-3xl mx-auto px-4 py-6'):
        with ui.row().classes('w-full items-center'):
            ui.label('Kategorie').classes('text-h5 font-bold')
            ui.space()
            ui.button('Dodaj kategorie', icon='add',
                      on_click=lambda: ui.navigate.to('/categories/add'))

        @ui.refreshable
        def cat_table():
            with get_db() as db:
                cats = db.query(Category).order_by(Category.display_name).all()

            if not cats:
                ui.label('Brak kategorii').classes('text-grey-5 q-mt-md')
                return

            columns = [
                {'name': 'name', 'label': 'Nazwa systemowa', 'field': 'name', 'align': 'left'},
                {'name': 'display', 'label': 'Nazwa wyswietlana', 'field': 'display', 'align': 'left'},
                {'name': 'count', 'label': 'Przedmioty', 'field': 'count', 'align': 'center'},
                {'name': 'actions', 'label': '', 'field': 'actions', 'align': 'right'},
            ]

            with get_db() as db:
                rows = []
                for cat in cats:
                    count = db.query(Item).filter(Item.category_id == cat.id).count()
                    rows.append({
                        'id': cat.id, 'name': cat.name,
                        'display': cat.display_name, 'count': count,
                    })

            table = ui.table(columns=columns, rows=rows, row_key='id').classes('w-full')
            table.add_slot('body-cell-actions', '''
                <q-td :props="props">
                    <q-btn flat dense icon="edit" @click="$parent.$emit('edit', props.row)" />
                    <q-btn flat dense icon="delete" color="red" @click="$parent.$emit('delete', props.row)" />
                </q-td>
            ''')
            table.on('edit', lambda e: ui.navigate.to(f'/categories/{e.args["id"]}/edit'))
            table.on('delete', lambda e: confirm_delete(e.args['id'], e.args['display'], e.args['count']))

        def confirm_delete(cat_id, name, count):
            if count > 0:
                ui.notify(f'Nie mozna usunac kategorii "{name}" - jest uzywana przez {count} przedmiotow',
                          type='negative')
                return

            with ui.dialog() as dlg, ui.card():
                ui.label(f'Usunac kategorie "{name}"?').classes('text-lg')
                with ui.row().classes('w-full justify-end gap-2 q-mt-md'):
                    ui.button('Anuluj', on_click=dlg.close).props('flat')
                    ui.button('Usun', on_click=lambda: do_delete(cat_id, dlg), icon='delete') \
                        .props('color=red')
            dlg.open()

        def do_delete(cat_id, dlg):
            with get_db() as db:
                cat = db.query(Category).get(cat_id)
                if cat:
                    db.delete(cat)
                    db.commit()
            dlg.close()
            ui.notify('Kategoria usunieta', type='positive')
            cat_table.refresh()

        cat_table()


@ui.page('/categories/add')
def category_add():
    create_header()

    with ui.column().classes('w-full max-w-xl mx-auto px-4 py-6'):
        ui.label('Dodaj kategorie').classes('text-h5 font-bold q-mb-md')

        name_in = ui.input('Nazwa systemowa',
                           validation={'Wymagane': lambda v: bool(v and v.strip())}).classes('w-full')
        display_in = ui.input('Nazwa wyswietlana',
                              validation={'Wymagane': lambda v: bool(v and v.strip())}).classes('w-full')

        def save():
            if not name_in.value or not name_in.value.strip():
                ui.notify('Nazwa systemowa jest wymagana', type='negative')
                return
            if not display_in.value or not display_in.value.strip():
                ui.notify('Nazwa wyswietlana jest wymagana', type='negative')
                return

            with get_db() as db:
                existing = db.query(Category).filter_by(name=name_in.value.strip()).first()
                if existing:
                    ui.notify('Kategoria o tej nazwie systemowej juz istnieje', type='negative')
                    return
                db.add(Category(name=name_in.value.strip(), display_name=display_in.value.strip()))
                db.commit()

            ui.notify('Kategoria dodana!', type='positive')
            ui.navigate.to('/categories')

        with ui.row().classes('w-full justify-end gap-2 q-mt-lg'):
            ui.button('Anuluj', on_click=lambda: ui.navigate.to('/categories')).props('flat')
            ui.button('Zapisz', icon='save', on_click=save).props('color=primary')


@ui.page('/categories/{cat_id}/edit')
def category_edit(cat_id: int):
    create_header()

    with get_db() as db:
        cat = db.query(Category).get(cat_id)

    if not cat:
        ui.label('Kategoria nie znaleziona').classes('text-xl text-red q-pa-lg')
        return

    with ui.column().classes('w-full max-w-xl mx-auto px-4 py-6'):
        ui.label(f'Edytuj: {cat.display_name}').classes('text-h5 font-bold q-mb-md')

        name_in = ui.input('Nazwa systemowa', value=cat.name).classes('w-full')
        display_in = ui.input('Nazwa wyswietlana', value=cat.display_name).classes('w-full')

        def save():
            if not name_in.value or not name_in.value.strip():
                ui.notify('Nazwa systemowa jest wymagana', type='negative')
                return
            if not display_in.value or not display_in.value.strip():
                ui.notify('Nazwa wyswietlana jest wymagana', type='negative')
                return

            with get_db() as db:
                existing = db.query(Category).filter(
                    Category.name == name_in.value.strip(), Category.id != cat_id,
                ).first()
                if existing:
                    ui.notify('Kategoria o tej nazwie systemowej juz istnieje', type='negative')
                    return
                c = db.query(Category).get(cat_id)
                c.name = name_in.value.strip()
                c.display_name = display_in.value.strip()
                db.commit()

            ui.notify('Kategoria zaktualizowana!', type='positive')
            ui.navigate.to('/categories')

        with ui.row().classes('w-full justify-end gap-2 q-mt-lg'):
            ui.button('Anuluj', on_click=lambda: ui.navigate.to('/categories')).props('flat')
            ui.button('Zapisz', icon='save', on_click=save).props('color=primary')

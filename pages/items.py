from datetime import date

from fastapi.responses import FileResponse
from nicegui import app, events, ui
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from db import get_db
from models import Category, Item, ItemImage, DEFAULT_EXPIRATION_DAYS
from pages import STATUS_COLORS, STATUS_LABELS, STATUS_OPTIONS, create_date_input, create_header
from services import (
    UPLOAD_DIR, delete_image_file, export_item_photos_zip, export_photos_zip,
    process_and_save_image,
)

# --- API endpoints for file downloads ---

@app.get('/api/export/all')
def api_export_all():
    with get_db() as db:
        items = db.query(Item).options(selectinload(Item.images)).all()
    path = export_photos_zip(items)
    return FileResponse(path, filename=path.split('/')[-1], media_type='application/zip')


@app.get('/api/export/{item_id}')
def api_export_item(item_id: int):
    with get_db() as db:
        item = db.query(Item).options(selectinload(Item.images)).get(item_id)
    if not item:
        return {'error': 'not found'}
    path = export_item_photos_zip(item)
    return FileResponse(path, filename=path.split('/')[-1], media_type='application/zip')


# --- Pages ---

@ui.page('/')
def item_list():
    create_header()

    state = {'search': '', 'category_id': None, 'status': 'w_magazynie', 'sort': 'date_desc', 'page': 1}
    PER_PAGE = 12

    with get_db() as db:
        cats = db.query(Category).order_by(Category.display_name).all()
        cat_options = {0: 'Wszystkie'}
        cat_options.update({c.id: c.display_name for c in cats})

    filter_status_options = {0: 'Wszystkie'}
    filter_status_options.update(STATUS_LABELS)

    with ui.column().classes('w-full max-w-7xl mx-auto px-4'):
        with ui.row().classes('w-full items-end gap-2 flex-wrap py-4'):
            search_in = ui.input('Szukaj', value='').props('clearable dense').classes('w-48')
            cat_sel = ui.select(cat_options, value=0, label='Kategoria').props('dense').classes('w-40')
            status_sel = ui.select(filter_status_options, value='w_magazynie', label='Status').props('dense').classes('w-44')
            sort_sel = ui.select(
                {'date_desc': 'Najnowsze', 'date_asc': 'Najstarsze',
                 'price_asc': 'Cena rosnąco', 'price_desc': 'Cena malejąco',
                 'title_asc': 'Tytuł A-Z', 'activation_desc': 'Aktywacja'},
                value='date_desc', label='Sortuj',
            ).props('dense').classes('w-40')
            ui.button(icon='search', on_click=lambda: apply_filters()).props('dense color=primary')
            ui.button(icon='clear_all', on_click=lambda: clear_filters()).props('dense flat')

        @ui.refreshable
        def items_grid():
            with get_db() as db:
                query = db.query(Item).options(
                    selectinload(Item.images), selectinload(Item.category_rel),
                )
                if state['search']:
                    s = f"%{state['search']}%"
                    query = query.filter(or_(Item.title.ilike(s), Item.description.ilike(s)))
                if state['category_id']:
                    query = query.filter(Item.category_id == state['category_id'])

                status_f = state['status']
                if status_f and status_f not in ('do_likwidacji',):
                    query = query.filter(Item.status == status_f)

                sort_map = {
                    'date_asc': Item.date_added.asc(),
                    'price_asc': Item.price.asc(),
                    'price_desc': Item.price.desc(),
                    'title_asc': Item.title.asc(),
                    'activation_desc': Item.activation_date.desc().nullslast(),
                }
                query = query.order_by(sort_map.get(state['sort'], Item.date_added.desc()))
                all_items = query.all()

            if status_f == 'do_likwidacji':
                all_items = [i for i in all_items if i.calculated_status == 'do_likwidacji']

            total = len(all_items)
            total_pages = max(1, -(-total // PER_PAGE))
            start = (state['page'] - 1) * PER_PAGE
            items = all_items[start:start + PER_PAGE]

            if not items:
                with ui.column().classes('w-full items-center py-12'):
                    ui.icon('inventory_2', size='64px').classes('text-grey-4')
                    ui.label('Brak przedmiotów do wyświetlenia').classes('text-lg text-grey-5')
                return

            with ui.element('div').classes(
                'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 w-full'
            ):
                for item in items:
                    with ui.card().classes('cursor-pointer hover:shadow-lg transition-shadow') \
                            .on('click', lambda _, i=item: ui.navigate.to(f'/items/{i.id}')):
                        if item.images:
                            ui.image(f'/uploads/{item.images[0].filename}') \
                                .classes('w-full').style('height: 200px; object-fit: cover')
                        else:
                            with ui.element('div').classes(
                                'w-full bg-grey-2 flex items-center justify-center'
                            ).style('height: 200px'):
                                ui.icon('image', size='48px').classes('text-grey-4')

                        with ui.card_section():
                            ui.label(item.title).classes('text-subtitle1 font-bold')
                            with ui.row().classes('items-center gap-2 no-wrap'):
                                ui.label(f'{float(item.price):.2f} zł').classes('text-bold text-primary')
                                ui.space()
                                cs = item.calculated_status
                                ui.badge(STATUS_LABELS.get(cs, cs),
                                         color=STATUS_COLORS.get(cs, 'grey'))
                            if item.category_rel:
                                ui.label(item.category_rel.display_name).classes('text-caption text-grey-7')

            if total_pages > 1:
                with ui.row().classes('w-full justify-center py-4'):
                    ui.pagination(1, total_pages, value=state['page'],
                                  on_change=lambda e: _set_page(e.value))

        def apply_filters():
            state['search'] = search_in.value or ''
            state['category_id'] = cat_sel.value if cat_sel.value != 0 else None
            state['status'] = status_sel.value if status_sel.value != 0 else None
            state['sort'] = sort_sel.value
            state['page'] = 1
            items_grid.refresh()

        def clear_filters():
            search_in.value = ''
            cat_sel.value = 0
            status_sel.value = 'w_magazynie'
            sort_sel.value = 'date_desc'
            state.update({'search': '', 'category_id': None, 'status': 'w_magazynie', 'sort': 'date_desc', 'page': 1})
            items_grid.refresh()

        def _set_page(p):
            state['page'] = p
            items_grid.refresh()

        items_grid()


# --- Add item ---

@ui.page('/items/add')
def item_add():
    create_header()

    with get_db() as db:
        cats = db.query(Category).order_by(Category.display_name).all()
        cat_options = {c.id: c.display_name for c in cats}

    uploaded_filenames: list[str] = []

    with ui.column().classes('w-full max-w-3xl mx-auto px-4 py-6'):
        ui.label('Dodaj przedmiot').classes('text-h5 font-bold q-mb-md')

        title_in = ui.input('Tytuł', validation={'Wymagane': lambda v: bool(v and v.strip())}) \
            .classes('w-full')
        desc_in = ui.textarea('Opis', validation={'Wymagane': lambda v: bool(v and v.strip())}) \
            .classes('w-full')
        price_in = ui.number('Cena (zł)', value=0, min=0, format='%.2f',
                             validation={'Wymagane': lambda v: v is not None and v > 0}) \
            .classes('w-full')
        link_in = ui.input('Link do aukcji (opcjonalnie)').classes('w-full')

        with ui.row().classes('w-full gap-4'):
            cat_sel = ui.select(cat_options, label='Kategoria',
                                validation={'Wymagane': lambda v: v is not None}).classes('flex-1')
            status_sel = ui.select(STATUS_OPTIONS, value='w_magazynie', label='Status').classes('flex-1')

        with ui.row().classes('w-full gap-4'):
            activation_in = create_date_input('Data aktywacji')
            exp_in = ui.number('Ważność (dni)', value=DEFAULT_EXPIRATION_DAYS, min=1).classes('flex-1')

        ui.label('Zdjęcia').classes('text-subtitle1 font-bold q-mt-md')

        @ui.refreshable
        def image_previews():
            if uploaded_filenames:
                with ui.row().classes('gap-2 flex-wrap'):
                    for fname in uploaded_filenames:
                        ui.image(f'/uploads/{fname}').classes('rounded') \
                            .style('height: 100px; width: 100px; object-fit: cover')

        def handle_upload(e: events.UploadEventArguments):
            try:
                content = e.content.read()
                fname = process_and_save_image(content, e.name)
                uploaded_filenames.append(fname)
                image_previews.refresh()
            except Exception as ex:
                ui.notify(f'Błąd uploadu: {ex}', type='negative')

        ui.upload(on_upload=handle_upload, multiple=True, auto_upload=True,
                  label='Przeciągnij zdjęcia lub kliknij') \
            .props('accept="image/*"').classes('w-full')
        image_previews()

        def save():
            if not title_in.value or not title_in.value.strip():
                ui.notify('Tytuł jest wymagany', type='negative')
                return
            if not desc_in.value or not desc_in.value.strip():
                ui.notify('Opis jest wymagany', type='negative')
                return
            if not price_in.value or price_in.value <= 0:
                ui.notify('Podaj cenę', type='negative')
                return
            if not cat_sel.value:
                ui.notify('Wybierz kategorię', type='negative')
                return
            if not uploaded_filenames:
                ui.notify('Dodaj przynajmniej jedno zdjęcie', type='negative')
                return

            act_date = None
            if activation_in.value:
                try:
                    act_date = date.fromisoformat(activation_in.value)
                except ValueError:
                    ui.notify('Niepoprawny format daty aktywacji', type='negative')
                    return

            with get_db() as db:
                item = Item(
                    title=title_in.value.strip(),
                    description=desc_in.value.strip(),
                    price=price_in.value,
                    auction_link=link_in.value.strip() or None,
                    activation_date=act_date,
                    expiration_days=int(exp_in.value) if exp_in.value else DEFAULT_EXPIRATION_DAYS,
                    category_id=cat_sel.value,
                    status=status_sel.value,
                )
                db.add(item)
                db.flush()
                for fname in uploaded_filenames:
                    db.add(ItemImage(filename=fname, item_id=item.id))
                db.commit()

            ui.notify('Przedmiot dodany!', type='positive')
            ui.navigate.to('/')

        with ui.row().classes('w-full justify-end gap-2 q-mt-lg'):
            ui.button('Anuluj', on_click=lambda: ui.navigate.to('/')).props('flat')
            ui.button('Zapisz', icon='save', on_click=save).props('color=primary')


# --- Edit item ---

@ui.page('/items/{item_id}/edit')
def item_edit(item_id: int):
    create_header()

    with get_db() as db:
        item = db.query(Item).options(
            selectinload(Item.images), selectinload(Item.category_rel),
        ).get(item_id)
        cats = db.query(Category).order_by(Category.display_name).all()
        cat_options = {c.id: c.display_name for c in cats}

    if not item:
        ui.label('Przedmiot nie znaleziony').classes('text-xl text-red q-pa-lg')
        return

    existing_image_ids: list[int] = [img.id for img in item.images]
    existing_images: list[dict] = [{'id': img.id, 'filename': img.filename} for img in item.images]
    new_filenames: list[str] = []

    with ui.column().classes('w-full max-w-3xl mx-auto px-4 py-6'):
        ui.label(f'Edytuj: {item.title}').classes('text-h5 font-bold q-mb-md')

        title_in = ui.input('Tytuł', value=item.title).classes('w-full')
        desc_in = ui.textarea('Opis', value=item.description).classes('w-full')
        price_in = ui.number('Cena (zł)', value=float(item.price), min=0, format='%.2f').classes('w-full')
        link_in = ui.input('Link do aukcji', value=item.auction_link or '').classes('w-full')

        with ui.row().classes('w-full gap-4'):
            cat_sel = ui.select(cat_options, value=item.category_id, label='Kategoria').classes('flex-1')
            status_sel = ui.select(STATUS_OPTIONS, value=item.status, label='Status').classes('flex-1')

        with ui.row().classes('w-full gap-4'):
            act_val = str(item.activation_date) if item.activation_date else ''
            activation_in = create_date_input('Data aktywacji', value=act_val)
            exp_in = ui.number('Ważność (dni)', value=item.expiration_days, min=1).classes('flex-1')

        with ui.row().classes('w-full gap-4'):
            rem_val = str(item.removal_date) if item.removal_date else ''
            removal_in = create_date_input('Data zdjęcia ogłoszenia', value=rem_val)

        # Existing images
        ui.label('Aktualne zdjęcia').classes('text-subtitle1 font-bold q-mt-md')

        @ui.refreshable
        def show_existing():
            if not existing_images:
                ui.label('Brak zdjęć').classes('text-grey-5')
                return
            with ui.row().classes('gap-2 flex-wrap'):
                for img_data in list(existing_images):
                    with ui.card().classes('relative').style('width: 120px'):
                        ui.image(f'/uploads/{img_data["filename"]}') \
                            .classes('w-full').style('height: 100px; object-fit: cover')
                        ui.button(icon='close', on_click=lambda _, d=img_data: remove_existing(d)) \
                            .props('flat dense round color=red size=sm') \
                            .classes('absolute top-0 right-0')

        def remove_existing(img_data):
            with get_db() as db:
                img_obj = db.query(ItemImage).get(img_data['id'])
                if img_obj:
                    delete_image_file(img_obj.filename)
                    db.delete(img_obj)
                    db.commit()
            existing_images.remove(img_data)
            if img_data['id'] in existing_image_ids:
                existing_image_ids.remove(img_data['id'])
            show_existing.refresh()
            ui.notify('Zdjęcie usunięte', type='info')

        show_existing()

        # New images
        ui.label('Dodaj nowe zdjęcia').classes('text-subtitle1 font-bold q-mt-md')

        @ui.refreshable
        def new_previews():
            if new_filenames:
                with ui.row().classes('gap-2 flex-wrap'):
                    for fname in new_filenames:
                        ui.image(f'/uploads/{fname}').classes('rounded') \
                            .style('height: 100px; width: 100px; object-fit: cover')

        def handle_upload(e: events.UploadEventArguments):
            try:
                content = e.content.read()
                fname = process_and_save_image(content, e.name)
                new_filenames.append(fname)
                new_previews.refresh()
            except Exception as ex:
                ui.notify(f'Błąd uploadu: {ex}', type='negative')

        ui.upload(on_upload=handle_upload, multiple=True, auto_upload=True,
                  label='Przeciągnij lub kliknij') \
            .props('accept="image/*"').classes('w-full')
        new_previews()

        def save():
            if not title_in.value or not title_in.value.strip():
                ui.notify('Tytuł jest wymagany', type='negative')
                return
            if not desc_in.value or not desc_in.value.strip():
                ui.notify('Opis jest wymagany', type='negative')
                return
            if not existing_images and not new_filenames:
                ui.notify('Przedmiot musi mieć przynajmniej jedno zdjęcie', type='negative')
                return

            act_date = None
            if activation_in.value:
                try:
                    act_date = date.fromisoformat(activation_in.value)
                except ValueError:
                    ui.notify('Niepoprawny format daty aktywacji', type='negative')
                    return

            rem_date = None
            if removal_in.value:
                try:
                    rem_date = date.fromisoformat(removal_in.value)
                except ValueError:
                    ui.notify('Niepoprawny format daty zdjęcia', type='negative')
                    return

            with get_db() as db:
                it = db.query(Item).get(item_id)
                it.title = title_in.value.strip()
                it.description = desc_in.value.strip()
                it.price = price_in.value
                it.auction_link = link_in.value.strip() or None
                it.activation_date = act_date
                it.expiration_days = int(exp_in.value) if exp_in.value else DEFAULT_EXPIRATION_DAYS
                it.removal_date = rem_date
                it.category_id = cat_sel.value
                it.status = status_sel.value
                for fname in new_filenames:
                    db.add(ItemImage(filename=fname, item_id=item_id))
                db.commit()

            ui.notify('Przedmiot zaktualizowany!', type='positive')
            ui.navigate.to(f'/items/{item_id}')

        with ui.row().classes('w-full justify-end gap-2 q-mt-lg'):
            ui.button('Anuluj', on_click=lambda: ui.navigate.to(f'/items/{item_id}')).props('flat')
            ui.button('Zapisz', icon='save', on_click=save).props('color=primary')


# --- Item detail (must be after /items/add and /items/{item_id}/edit) ---

@ui.page('/items/{item_id}')
def item_detail(item_id: int):
    create_header()

    with get_db() as db:
        item = db.query(Item).options(
            selectinload(Item.images), selectinload(Item.category_rel),
        ).get(item_id)

    if not item:
        ui.label('Przedmiot nie znaleziony').classes('text-xl text-red q-pa-lg')
        return

    with ui.column().classes('w-full max-w-5xl mx-auto px-4 py-6 gap-4'):
        # Title row
        with ui.row().classes('w-full items-center'):
            ui.label(item.title).classes('text-h4 font-bold')
            ui.space()
            cs = item.calculated_status
            ui.badge(STATUS_LABELS.get(cs, cs), color=STATUS_COLORS.get(cs, 'grey')).props('size=lg')

        # Images
        if item.images:
            with ui.row().classes('gap-3 flex-wrap'):
                for img in item.images:
                    ui.image(f'/uploads/{img.filename}') \
                        .classes('rounded shadow').style('height: 240px; object-fit: cover')

        ui.separator()

        # Details grid
        with ui.grid(columns=2).classes('gap-x-8 gap-y-2'):
            ui.label('Cena:').classes('font-bold')
            ui.label(f'{float(item.price):.2f} zł')

            ui.label('Kategoria:').classes('font-bold')
            ui.label(item.category_rel.display_name if item.category_rel else '-')

            ui.label('Dodano:').classes('font-bold')
            ui.label(item.date_added.strftime('%Y-%m-%d') if item.date_added else '-')

            if item.activation_date:
                ui.label('Data aktywacji:').classes('font-bold')
                ui.label(str(item.activation_date))

                ui.label('Wygasa:').classes('font-bold')
                days = item.days_until_expiration
                exp_str = str(item.expiration_date)
                if days is not None:
                    exp_str += f'  ({days} dni)'
                ui.label(exp_str)

            if item.removal_date:
                ui.label('Data zdjęcia:').classes('font-bold')
                ui.label(str(item.removal_date))

            if item.auction_link:
                ui.label('Link do aukcji:').classes('font-bold')
                ui.link(item.auction_link, item.auction_link, new_tab=True)

        ui.separator()
        ui.label('Opis').classes('text-subtitle1 font-bold')
        ui.label(item.description).classes('whitespace-pre-wrap')

        # Actions
        ui.separator()
        with ui.row().classes('gap-2'):
            ui.button('Edytuj', icon='edit',
                      on_click=lambda: ui.navigate.to(f'/items/{item_id}/edit'))
            ui.button('Eksportuj zdjęcia', icon='download',
                      on_click=lambda: ui.run_javascript(f'window.location.href="/api/export/{item_id}"')) \
                .props('outline')

            def confirm_delete():
                with ui.dialog() as dlg, ui.card():
                    ui.label('Czy na pewno chcesz usunąć ten przedmiot?').classes('text-lg')
                    with ui.row().classes('w-full justify-end gap-2 q-mt-md'):
                        ui.button('Anuluj', on_click=dlg.close).props('flat')
                        ui.button('Usuń', on_click=lambda: do_delete(dlg), icon='delete') \
                            .props('color=red')
                dlg.open()

            def do_delete(dlg):
                with get_db() as db:
                    it = db.query(Item).options(selectinload(Item.images)).get(item_id)
                    if it:
                        for img in it.images:
                            delete_image_file(img.filename)
                        db.delete(it)
                        db.commit()
                dlg.close()
                ui.notify('Przedmiot usunięty', type='positive')
                ui.navigate.to('/')

            ui.button('Usuń', icon='delete', on_click=confirm_delete).props('color=red outline')

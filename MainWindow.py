import PySimpleGUI as sg
from PySimpleGUI import Window

# global variables
URL = '-URL-'
URL_LIST = '-URL_LIST-'
BTN_ADD = '-BTN_ADD-'
BTN_CLEAN = '-BTN_CLEAN-'
BTN_DOWNLOAD = '-BTN_DOWNLOAD-'

def enable_disable_all(window: Window, state: str):
    window[URL].Widget.configure(state=state)
    window[URL_LIST].Widget.configure(state=state)
    window[BTN_ADD].Widget.configure(state=state)
    window[BTN_DOWNLOAD].Widget.configure(state=state)
    window[BTN_CLEAN].Widget.configure(state=state)

def main_window() -> Window:
    # opciones de menu copy/paste
    copy_paste_menu = ['', ['Copiar', 'Pegar', 'Limpiar']]
    command  = ['', ['Borrar', ]]

    # layout de nuestra ventana
    main_column = [
        [
            sg.Text('Url Video:'),
            sg.In(size=(63, 1), key=URL, right_click_menu=copy_paste_menu),
            sg.Button('Añadir', key=BTN_ADD)
        ],
        [
            sg.Listbox(
                values=[], enable_events=True, size=(80, 15), key=URL_LIST, right_click_menu=command
            )
        ],
        [
            sg.Button('Descargar', key=BTN_DOWNLOAD),
            sg.Button('Limpiar', key=BTN_CLEAN),
        ]
    ]

    layout = [
        [
            sg.Column(main_column, element_justification='center'),
        ]
    ]
    return Window('Super YT Downloader', layout)

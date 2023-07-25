import os
import PySimpleGUI as sg
from re import compile, IGNORECASE
from time import sleep
from threading import Thread
from queue import Queue, Empty
from LoadingGifs import LINE_BOXES
import MainWindow as wn
from MainWindow import URL, URL_LIST, BTN_ADD, BTN_CLEAN, BTN_DOWNLOAD

# regex para los videos las url de YouTube
regx_yt = compile(
    '^(https?\:\/\/)?(www\.youtube\.com|youtu\.be)\/.+$', IGNORECASE)

# funcion que ejecuta la descarga de los videos
def download_vid(list_url: list, work_id: int, gui_queue: Queue):

    for url in list_url:
        # ejecutamos los comandos de descarga del video
        command = 'yt-dlp -f "bv*+ba" "{}"'.format(url)
        os.system(command)
        sleep(0.2)

    # limpiamos el lista
    list_url.clear()
    # window[URL_LIST].update([])
    # enviamos mensaje de done a la pila
    gui_queue.put('{} ::: done'.format(work_id))

def main():
    # tema de la ventana
    sg.theme('DefaultNoMoreNagging')

    # instanciamos la pila
    gui_queue = Queue()

    window = wn.main_window()

    list_url = []
    work_id = 0

    # gestionamos los eventos de la ventana
    while True: 
        event, values = window.Read(timeout=100)

        # en caso de salir o cerrar la ventana rompemos el bucle
        if event == 'Exit' or event == sg.WIN_CLOSED:
            break

        # copy/paste/clean
        if event in ('Copiar', 'Pegar'):
            widget = window.find_element_with_focus().widget
        if event == 'Copiar' and widget.select_present():
            text = widget.selection_get()
            window.TKroot.clipboard_clear()
            window.TKroot.clipboard_append(text)
        elif event == 'Pegar':
            if widget.select_present():
                widget.delete(sg.tk.SEL_FIRST, sg.tk.SEL_LAST)
            widget.insert(sg.tk.INSERT, window.TKroot.clipboard_get())
            widget = None
        # limpiar input, limpiar lista
        if event == 'Limpiar':
            window[URL].update('')
        if event == 'Borrar':
            window[URL_LIST].update([])
        # anadimos elementos a nuestra lista en el evento del boton
        if event == BTN_ADD:
            # solo anadimos elementos en caso de que se trate de una url y no este repetido
            if values[URL] not in list_url and regx_yt.match(values[URL]):
                list_url.append(values[URL])
                window[URL_LIST].update(list_url)
                window[URL].update('')

        if event == BTN_DOWNLOAD:
            foldername = sg.PopupGetFolder(
                'Seleccionar Carpeta', no_window=True)
            if foldername:  # `None` when clicked `Cancel` - so I skip it
                currentPath = foldername
                os.chdir(currentPath)
                thread = Thread(target=download_vid, args=(
                    list_url, work_id, gui_queue, ), daemon=True)
                thread.start()
                work_id = work_id + 1 if work_id < 19 else 0

        if event == BTN_CLEAN:
            # limpiamos las lista y el list box del gui
            list_url.clear()
            window[URL_LIST].update([])

        # obtenemos la localizacion actual de la ventana
        windowLocation = window.CurrentLocation()
        popupLocation = (None, None)
        # realizamos el calculo para centrar los popups
        if windowLocation != (None, None):
            popupLocation = (windowLocation[0] + 220, windowLocation[1] + 160)
        
        # --------------- LECTURA DE MENSAJE DE LOS THREATS -------------------
        try:
            message = gui_queue.get_nowait()  # mira si hay mensajes en la pila
        except Empty:  # get_nowait() will se ejecuta cuando la pila esta vacia
            message = None  # nada en la pila, asi que no se hace nada

        # si se recibe algun mensaje de la pila entonces algun threat ha finalizado su trabajo
        if message is not None:
            # esta es la zona en la que executamos codigo al haber finalizado la ejecucion que esperabamos,
            # en este caso la descarga de los videos
            # con el work_id podemos saber exactamente que funcion en el hilo/s ha finalizado
            work_id -= 1
            # en caso de que no exista ya ninguna ejecucion, finalizamos el modal de carga y rehabilitamos la ventana principal
            if not work_id:
                # finalia el popup de carga y lanza el mensaje de finalizado
                sg.PopupAnimated(None)
                sg.popup_ok('Descarga finalizada', location=popupLocation)
                # habilitamos la ventamna principal
                wn.enable_disable_all(window, 'normal')
                window.enable()
                window.TKroot.focus_force()
                # limpiamos el list box del gui
                window[URL_LIST].update([])

        # si la descarga de videos se esta ejecutando, mostramos el modal de carga indeterminada y deshabilitamos la ventana principal
        if work_id:
            sg.PopupAnimated(
                LINE_BOXES, message='Cargando...', background_color=None, time_between_frames=100, no_titlebar=False, grab_anywhere=False, keep_on_top=False, location=popupLocation)
            wn.enable_disable_all(window, 'disable')
            window.disable()

    # finalizamos el programa
    window.close()



if __name__ == '__main__':
    main()

LinkedIn Apply Bot

Webscrapping? Posible pero aun asi requiere de interaccion.
Capturar pantalla y usar opencv para ubicar y leer lo que hay? Mover mouse e indicar segun aplique

EasyApply es necesario para el inicio, evitar ir a otras paginas
Si no es easy apply, agregar la url a un archivo externo para posteriormente hacerlo manualmente.

Tested on 1920x1080

profile dir created and open to locally use only that instance and have not other access

webbrowser
pyautogui
cv2
numpy
langdetect
pytesseract
bs4
json
time

Pasos
1. Abrir la pagina de linkedin empleos desde el navegador predeterminado, evitando tener que meter claves y demas
2. Escanear por simbolo de busqueda, entrar el titulo de trabajo 
2.a Escanear por simbolo de ubicacion, entrar la ubicacion | Tabulador para cambiar automaticamente cambiar
TODO
3. Ver lista de empleos
3.a Determinar si es solicitud sencilla, solicitud dentro de Linkedin, solicitud externa
3.b Solicitud sencilla ez check
3.c Solicitud dentro y externa agregar a archivo externo 
4. Click en empleo por empleo
5. Aplicacion al empleo
6. Manejo de archivo externo para ver el progreso del bot y lo que ha hecho
7...


TODO
Modularizar
Mejorar json output
waitDownload
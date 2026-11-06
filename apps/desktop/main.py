"""Este es el archivo que ejecutamos para abrir SMART UNI."""

import os
from pathlib import Path

from smart_uni.core import seed_demo
from smart_uni.storage_mode import open_service
from smart_uni.ui import SmartUniApp
from smart_uni.student_data import StudentSpaceService, seed_student_demo


def main():
    """Preparamos los datos y después abrimos la ventana de la aplicación."""
    # Podemos cambiar la ubicación del JSON sin modificar el código.
    # Si no indicamos otra ruta, se guarda dentro de nuestra carpeta personal.
    data_path = Path(
        os.environ.get(
            'SMART_UNI_DATA',
            str(Path.home() / '.smart_uni' / 'data.json'),
        )
    )

    # El modo secure requiere SQLCipher y un almacén del SO disponibles.
    # El modo habitual mantiene los datos del prototipo exactamente como antes.
    mode = os.environ.get('SMARTUNI_STORAGE', 'legacy')
    service = open_service(data_path, mode=mode)

    # Las credenciales públicas de demo jamás se crean en el modo secure.
    if mode == 'legacy':
        seed_demo(service)
        seed_student_demo(StudentSpaceService(service))

    app = SmartUniApp(service)
    app.mainloop()


if __name__ == '__main__':
    main()

"""Este es el archivo que ejecutamos para abrir SMART UNI."""

import os
from pathlib import Path

from smart_uni.core import SmartUniService, seed_demo
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

    service = SmartUniService(data_path)

    # Con esta cuenta podemos probar las pantallas durante la exposición.
    seed_demo(service)
    seed_student_demo(StudentSpaceService(service))

    app = SmartUniApp(service)
    app.mainloop()


if __name__ == '__main__':
    main()

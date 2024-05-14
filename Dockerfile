# Usa una imagen base de Python
FROM python:3.9

# Establece el directorio de trabajo en /app
WORKDIR /orlas

# Copia el archivo de requerimientos e instala las dependencias
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copia el código de la aplicación a la imagen
COPY . .

# Expone el puerto en el que se ejecuta la aplicación Flask
EXPOSE 5000

# Define el comando para ejecutar la aplicación
CMD ["python", "app.py"]

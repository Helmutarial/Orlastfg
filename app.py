from flask import Flask, render_template, redirect, url_for, flash, g, send_file, session, request, jsonify,json
from models import db, Estudiante, Reserva, Foto, Profesor, Voto
from forms import EstudianteForm
from flask_migrate import Migrate # para actualizar la base de datos
from datetime import datetime #para la gestion de reservas
import os #para trabajar con archivos y carpetas en python
from werkzeug.utils import secure_filename
from functools import wraps
import logging
from flask_oidc import OpenIDConnect
from zipfile import ZipFile  #para que los usuarios puedan descargar sus fotos
import urllib
import html
from sqlalchemy import desc, func

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mi_base_de_datos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'clave_secreta'  # Necesaria para trabajar con formularios en Flask-WTF
app.config.update({
    'SECRET_KEY': 'SomethingNotEntirelySecret',
    'TESTING': True,
    'DEBUG': True,
    'OIDC_CLIENT_SECRETS': os.path.join(os.path.dirname(__file__), 'static', 'data', 'client_secrets.json'),
    'OIDC_ID_TOKEN_COOKIE_SECURE': False,
    #'OIDC_REQUIRE_VERIFIED_EMAIL': False,
    'OIDC_USER_INFO_ENABLED': True,
    'OIDC_OPENID_REALM': 'tfg-orlas',
    'OIDC_SCOPES': ['openid', 'email'],
    'OIDC_INTROSPECTION_AUTH_METHOD': 'client_secret_post'
})




oidc = OpenIDConnect(app)
db.init_app(app)  # Inicializar SQLAlchemy con la aplicación Flask
migrate = Migrate(app, db)  # Configurar migraciones


def datos_completos_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        profile = session.get('oidc_auth_profile')
        if oidc.user_loggedin:
            # Si el usuario está autenticado y tiene los datos completos, continúa con la función
            g.user = Estudiante.query.filter_by(username=profile.get('preferred_username')).first()
            return f(*args, **kwargs)
        else:
            # Si el usuario no está autenticado, redirígelo a la pasarela de autenticación (/private)
            return redirect(url_for('private', next=request.endpoint))
    return decorated_function

def perfil_completado_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Obtener el usuario actualmente autenticado
        user = Estudiante.query.filter_by(username=oidc.user_getfield('preferred_username')).first()
        
        # Verificar si el campo nombre está lleno para el usuario en sesión
        if user and user.nombre:
            # Si el campo nombre está lleno, redireccionar al usuario a la página principal u otra página deseada
            flash('Ya has completado tu perfil', 'info')
            return redirect(url_for('index'))  # Puedes cambiar 'index' por la ruta deseada
        # Si el perfil no está completo, permitir que la función original se ejecute normalmente
        return f(*args, **kwargs)
    return decorated_function




@app.route('/inicio')
def inicio():
    return render_template('inicio.html')

@app.route('/') 
@oidc.require_login
def index():
    profile = session.get('oidc_auth_profile')
    # Obtener el usuario de la base de datos
    usuario = Estudiante.query.filter_by(username=oidc.user_getfield('preferred_username')).first()
    reserva = usuario.reservas # Obtener las reservas asociadas al usuario
    # Obtener los 5 profesores más votados por usuarios del mismo grado y especialidad
    profesespecialidad = (
        db.session.query(Profesor, func.count(Voto.id).label('total_votos'))
        .join(Voto, Profesor.id == Voto.profesor_id)
        .join(Estudiante, Estudiante.id == Voto.estudiante_id)
        .filter(Estudiante.especialidad == usuario.especialidad)
        .group_by(Profesor.id)
        .order_by(desc('total_votos'))
        .limit(5)
        .all()
    )
    profesgrado = (
        db.session.query(Profesor, func.count(Voto.id).label('total_votos'))
        .join(Voto, Profesor.id == Voto.profesor_id)
        .join(Estudiante, Estudiante.id == Voto.estudiante_id)
        .filter(Estudiante.grado == usuario.grado)
        .group_by(Profesor.id)
        .order_by(desc('total_votos'))
        .limit(5)
        .all()
    )
    g.user = Estudiante.query.filter_by(username=profile.get('preferred_username')).first()
    return render_template('index.html', usuario=g.user,  username=oidc.user_getfield('preferred_username'),reserva=reserva,profesespecialidad=profesespecialidad,profesgrado=profesgrado) # metemos lo de la variable global para el layout sepa si es admin o no




@app.route('/signout')
def logout():
    id_token = session.get('oidc_auth_token').get('id_token')
    session.clear()
    return redirect("https://sso.dat.etsit.upm.es/realms/tfg-orlas/protocol/openid-connect/logout?id_token_hint=%s&post_logout_redirect_uri=%s" % (id_token, urllib.parse.quote("http://127.0.0.1:5000/inicio", safe='')))

@app.route('/private') #la ruta se tiene que llamar asi, si no no funciona
@oidc.require_login
def private():

    profile = session.get('oidc_auth_profile')
    username = profile.get('preferred_username')
    email = profile.get('email')
    
    # Buscar el usuario en la base de datos por su nombre de usuario preferido
    usuario = Estudiante.query.filter_by(username=username).first()

    # Si el usuario existe en la base de datos, actualizar su información
    if usuario:
        app.logger.debug(f"Usuario '{username}' ya existe en la base de datos. Actualizando información.")
        usuario.correo = email
        # Guardar los cambios en la base de datos
        db.session.commit()
        # Redireccionar al usuario a la página de inicio
        return redirect(url_for('index'))

    else:
        # Si el usuario no existe en la base de datos, crear un nuevo registro
        app.logger.debug(f"Creando un nuevo usuario con nombre de usuario '{username}'.")
        nuevo_usuario = Estudiante(username=username, correo=email)
        db.session.add(nuevo_usuario)
        # Guardar los cambios en la base de datos
        db.session.commit()
        # Redireccionar al usuario a la página de inicio
        return redirect(url_for('perfil'))




# Configuración para la carga de archivos
UPLOAD_FOLDER = 'static/fotos'  # ruta de la carpeta donde se almacenarán las fotos cargadas
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # Extensiones de archivo permitidas
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER




with app.app_context():
    db.create_all()  # Crear las tablas en la base de datos si no existen


@app.route('/perfil', methods=['GET', 'POST'])
@oidc.require_login
@perfil_completado_required
def perfil():
    g.user = Estudiante.query.filter_by(username=oidc.user_getfield('preferred_username')).first()
    form = EstudianteForm()
    if form.validate_on_submit():
        # Obtener el usuario actual desde la base de datos
        usuario = Estudiante.query.filter_by(username=oidc.user_getfield('preferred_username')).first()
        if usuario:
            # Actualizar los datos del usuario con los valores del formulario
            usuario.nombre = form.nombre.data
            usuario.apellido1 = form.apellido1.data
            usuario.apellido2 = form.apellido2.data
            usuario.grado = form.grado.data
            usuario.especialidad = form.especialidad.data
            # Guardar los cambios en la base de datos
            db.session.commit()
            flash('Datos actualizados exitosamente', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario no encontrado', 'danger')
    return render_template('perfil.html', form=form, username=oidc.user_getfield('preferred_username'), usuario= g.user)




@app.route('/guardar_reserva', methods=['POST'])
def guardar_reserva():
    start_str = request.form['start']
    end_str = request.form['end']
    # Obtener el usuario actual desde la base de datos
    usuario = Estudiante.query.filter_by(username=oidc.user_getfield('preferred_username')).first()
    reserva = Reserva.query.filter_by(estudiante_id=usuario.id).first()
    # Convertir las cadenas de fecha y hora a objetos datetime
    start = datetime.fromisoformat(start_str)
    end = datetime.fromisoformat(end_str)
    if reserva  :
        reserva.start = start
        reserva.end = end
    else: 
        # Crear una nueva instancia de Reserva con los datos recibidos
        reserva = Reserva(start=start, end=end, estudiante_id=usuario.id)
        
        # Agregar la reserva a la sesión y guardarla en la base de datos
        db.session.add(reserva)
        
    db.session.commit()
    
    # Puedes devolver una respuesta al cliente si lo deseas
    return jsonify({'message': 'Reserva guardada exitosamente'})

@app.route('/reservas', methods=['GET', 'POST'])

@datos_completos_required   
@oidc.require_login
def reservas():
    g.user = Estudiante.query.filter_by(username=oidc.user_getfield('preferred_username')).first()
    # Obtener las reservas existentes desde la base de datos
    reservas_db = Reserva.query.all()

    # Convertir las reservas existentes a un formato compatible con JSON
    reservas_existente = []
    for reserva in reservas_db:
        reserva_dict = {
            "title": "Reservado",  # Puedes personalizar esto si tienes un título específico para cada reserva
            "start": reserva.start.strftime('%Y-%m-%dT%H:%M:%S'),
            "end": reserva.end.strftime('%Y-%m-%dT%H:%M:%S')
        }
        reservas_existente.append(reserva_dict)

    # Renderizar el template y pasar las reservas al template
    return render_template('reservas.html', reservas=json.dumps(reservas_existente),usuario=g.user)




@app.route('/actualizar_pagado/<int:id>', methods=['POST'])
def actualizar_pagado(id):
    estudiante = Estudiante.query.get_or_404(id)
    if request.method == 'POST':
        pagado = request.form['pagado']
        estudiante.pagado = pagado
        db.session.commit()
        return 'Campo pagado actualizado correctamente', 200


@app.route('/actualizar_pack/<int:id>', methods=['POST'])
def actualizar_pack(id):
    # Obtener el estudiante por su ID
    estudiante = Estudiante.query.get_or_404(id)
    
    # Obtener el nuevo valor de pack enviado desde el cliente
    nuevo_valor = request.form['pack']
    
    # Actualizar el valor de pack en el objeto del estudiante
    estudiante.pack = nuevo_valor
    
    # Guardar los cambios en la base de datos
    db.session.commit()
    
    return 'Pack actualizado correctamente', 200

@app.route('/actualizar_dato/<int:id>', methods=['POST'])
def actualizar_dato(id):
    estudiante = Estudiante.query.get_or_404(id)
    campo = request.form['campo']
    valor = request.form['valor']
    if campo == 'pagado':
        estudiante.pagado = valor
    elif campo == 'pack':
        estudiante.pack = valor
    db.session.commit()
    return 'Datos actualizados correctamente', 200




@app.route('/admin')
@oidc.require_login
def admin():
    # Aquí obtienes el usuario actual, por ejemplo desde la sesión
    usuario = Estudiante.query.filter_by(username=oidc.user_getfield('preferred_username')).first()

    estudiantes = Estudiante.query.all()

    order = request.args.get('order', 'asc')  # Obtener el parámetro de orden, predeterminado a 'asc'
    if order == 'desc':
        estudiantes = sorted(estudiantes, key=lambda x: x.reservas[0].start if x.reservas else datetime.min, reverse=True)
    else:
        estudiantes = sorted(estudiantes, key=lambda x: x.reservas[0].start if x.reservas else datetime.max)

    if usuario and usuario.tipo == 'admin':
        return render_template('admin.html', usuario=usuario, estudiantes=estudiantes)
    else:
        # Si no es administrador, puedes redirigirlo a otra página o mostrar un mensaje de error
        return render_template('error.html', message='No tienes permisos para acceder a esta página')


# Función para verificar si la extensión del archivo es permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/subirfotos', methods=['GET', 'POST'])
@oidc.require_login
def subir_fotos():

    g.user = Estudiante.query.filter_by(username=oidc.user_getfield('preferred_username')).first()
    estudiantes = Estudiante.query.all()
    # Obtén todas las especialidades disponibles en la base de datos
    especialidades = Estudiante.query.with_entities(Estudiante.especialidad).distinct().all()
    # Convierte la lista de tuplas en una lista plana de especialidades
    especialidades = [esp[0] for esp in especialidades]

    # Obtén todas los grados disponibles en la base de datos
    grados = Estudiante.query.with_entities(Estudiante.grado).distinct().all()
    grados = [esp[0] for esp in grados]
    especialidadygrado = list(set(especialidades + grados))
    if g.user and g.user.tipo == 'admin':
        if request.method == 'POST':
            # Verificar si se han enviado archivos
            if 'file' not in request.files:
                flash('No se han seleccionado archivos', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            
            # Verificar si el nombre del archivo está vacío
            if file.filename == '':
                flash('No se ha seleccionado ningún archivo', 'error')
                return redirect(request.url)
            
            # Verificar si el archivo tiene una extensión permitida
            if file and allowed_file(file.filename):
                # Obtener el ID del estudiante seleccionado del formulario
                estudiante_id = request.form.get('estudiante')
                print("ID del estudiante seleccionado:", estudiante_id)  # Imprimir el ID del estudiante
                
                # Buscar el estudiante en la base de datos
                estudiante = Estudiante.query.get(estudiante_id)
                print("Estudiante asociado:", estudiante)  # Imprimir información sobre el estudiante
                
                # Obtener la especialidad seleccionada del formulario
                especialidad = request.form['especialidad']

                # Guardar el archivo en el servidor
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
                # Crear una nueva instancia de Foto y asociarla con el estudiante seleccionado
                nueva_foto = Foto(filename=filename, estudiante=estudiante,especialidad=especialidad)
                
                # Agregar la nueva foto a la sesión y guardarla en la base de datos
                db.session.add(nueva_foto)
                db.session.commit()
                
                flash('Archivo subido correctamente', 'success')
                return redirect(request.url)
            else:
                flash('Formato de archivo no válido. Se permiten archivos con extensiones: png, jpg, jpeg, gif', 'error')
                return redirect(request.url)
        return render_template('subirfotos.html', usuario=g.user, estudiantes=estudiantes,especialidades=especialidadygrado) #lo llamo especialidades porque lo tenia para especialidades y si cambio el nombre es un lio
    else: 
        # Si no es administrador, puedes redirigirlo a otra página o mostrar un mensaje de error
        return render_template('error.html', message='No tienes permisos para acceder a esta página')

@app.route('/tusfotos')
@datos_completos_required 
@oidc.require_login
def tus_fotos():
    # Obtener el usuario actualmente autenticado
    user = Estudiante.query.filter_by(username=oidc.user_getfield('preferred_username')).first()
    
        
    if user:
        # Obtén todas las fotos asociadas a estudiantes con la especialidad seleccionada
        fotosespecialidad = Foto.query.filter_by(especialidad=user.especialidad).all()
        # Obtén todas las fotos asociadas a estudiantes con la especialidad seleccionada
        fotosgrado = Foto.query.filter_by(especialidad=user.grado).all()
        # Obtener las fotos asociadas al usuario
        fotosusuario = user.fotos
        fotos = fotosusuario + fotosespecialidad + fotosgrado
        return render_template('tusfotos.html', usuario=user, fotos=fotos)
    else:
        flash('Usuario no encontrado', 'error')
        return redirect(url_for('index'))

@app.route('/download_all_photos', methods=['GET'])
def download_all_photos():
    # Obtener la lista de todas las fotos
    fotos = Foto.query.all()
    
    # Crear un archivo ZIP temporal
    zip_path = 'temp_photos.zip'
    with ZipFile(zip_path, 'w') as zip_file:
        for foto in fotos:
            # Agregar cada foto al archivo ZIP
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], foto.filename)
            zip_file.write(photo_path, foto.filename)
    
    # Enviar el archivo ZIP al cliente para su descarga
    return send_file(zip_path, as_attachment=True)

@app.route('/votarprofesores', methods=['GET', 'POST'])
@datos_completos_required 
@oidc.require_login
def votar_profesores():
    # Obtener el usuario actualmente autenticado
    username = oidc.user_getfield('preferred_username')
    user = Estudiante.query.filter_by(username=oidc.user_getfield('preferred_username')).first()
    estudiante = Estudiante.query.filter_by(username=username).first()
    


    ruta_json = os.path.join("static", "data", "profes.json")
    with open(ruta_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Extraer los nombres de los profesores y decodificar caracteres especiales
    nombres_profesores = [html.unescape(nombre) for nombre in data]

    if request.method == 'POST':
        # Borrar los profesores que había votado anteriormente
        Voto.query.filter_by(estudiante_id=estudiante.id).delete()
        
        # Obtener los nombres de los profesores votados desde el formulario
        profesor_nombres = request.form.getlist('profesor_nombre')
        
        # Verificar si el estudiante ya ha votado a alguno de los profesores seleccionados
        profesores_votados = [v.profesor_id for v in Voto.query.filter_by(estudiante_id=estudiante.id).all()]
        
        for profesor_nombre in profesor_nombres:
            # Verificar si el profesor ya existe en la base de datos
            profesor_existente = Profesor.query.filter_by(nombre=profesor_nombre).first()
            
            if not profesor_existente:
                # Crear un nuevo profesor si no existe
                nuevo_profesor = Profesor(nombre=profesor_nombre)
                db.session.add(nuevo_profesor)
                db.session.commit()
                # Actualizar la variable profesor_existente
                profesor_existente = nuevo_profesor
            
            # Verificar si el estudiante ya ha votado a este profesor
            if profesor_existente.id in profesores_votados:
                flash(f'Ya has votado al profesor {profesor_nombre}. No puedes votar dos veces al mismo profesor.', 'error')
                return redirect(url_for('votarprofesores'))
            
            # Crear un nuevo voto
            nuevo_voto = Voto(estudiante_id=estudiante.id, profesor_id=profesor_existente.id)
            db.session.add(nuevo_voto)
        db.session.commit()

    return render_template('votarprofesores.html', profesores=nombres_profesores,usuario=user)

@app.route('/getProfessorsNames')
def get_professors_names():
    try:
        # Leer el contenido del archivo de texto
        with open('profes.txt', 'r') as file:
            data = json.load(file)
        
        # Extraer los nombres de los profesores
        names = [professor['name'] for professor in data]
        
        # Devolver los nombres de los profesores como JSON
        return jsonify(names)

    except Exception as e:
        # Manejar cualquier error que ocurra durante la lectura del archivo
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
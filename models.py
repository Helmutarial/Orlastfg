from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

# Tabla intermedia para la relación muchos a muchos entre Estudiante y Foto
estudiantes_fotos = db.Table('estudiantes_fotos',
    db.Column('estudiante_id', db.Integer, db.ForeignKey('estudiante.id'), primary_key=True),
    db.Column('foto_id', db.Integer, db.ForeignKey('foto.id'), primary_key=True)
)

class Estudiante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=True)
    apellido1 = db.Column(db.String(100), nullable=True)
    apellido2 = db.Column(db.String(100), nullable=True)
    grado = db.Column(db.String(100), nullable=True)
    especialidad = db.Column(db.String(100), nullable=True)
    tipo = db.Column(db.String(20), nullable=False, default='normal')
    pagado = db.Column(db.String(3), nullable=True, default='no')
    pack = db.Column(db.String(10), nullable=True,)
    correo = db.Column(db.String(100), nullable=True)
    fotos = db.relationship('Foto', back_populates='estudiante')
    reservas = db.relationship('Reserva', backref='estudiante', lazy=True)  # Relación uno a muchos con Reserva
    votos = db.relationship('Voto', backref='estudiante', lazy=True)  # Relación uno a muchos con Voto


class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiante.id'), nullable=False)  # Clave foránea que hace referencia al ID del estudiante

class Foto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    especialidad = db.Column(db.String(100))  # Campo para almacenar la especialidad
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiante.id'))
    estudiante = db.relationship('Estudiante', back_populates='fotos')


class Profesor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    votos = db.relationship('Voto', backref='profesor', lazy=True)  # Relación uno a muchos con Voto

class Voto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estudiante_id = db.Column(db.Integer, db.ForeignKey('estudiante.id'), nullable=False)
    profesor_id = db.Column(db.Integer, db.ForeignKey('profesor.id'), nullable=False)

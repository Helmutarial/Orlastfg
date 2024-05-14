from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired


class EstudianteForm(FlaskForm): 
    nombre = StringField('Nombre', validators=[DataRequired()])
    apellido1 = StringField('Apellidos', validators=[DataRequired()])
    apellido2 = StringField('Apellidos', validators=[DataRequired()])
    grado = StringField('Grado', validators=[DataRequired()])
    especialidad = StringField('Especialidad', validators=[DataRequired()]) 
    guardar = SubmitField('Guardar')  
   


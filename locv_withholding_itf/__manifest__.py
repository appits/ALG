# encoding: UTF-8
# Create:  jeduardo** 26/08/2017 **  **
# type of the change:  Creacion
# Comments: Creacion del modulo de locv_withholding_itf
#Contiene un diccionario en Python para agregar las descripciones del módulo, como autor, versión, etc.
{
    'name': 'locv_withholding_itf',
    'version':'1.0',
    'category': 'Account',
    'summary':'Automatic ITF Withhold',
    'description': '''\
Calculate automatic itf withholding
===========================
Colaborador: Maria Carreno

V1.0
Calculate automatic itf withholding
''',
    'author': 'Localizacion Venezolana',
    'website': '',
    #data, es una lista donde se agregan todas las vistas del módulo, es decir los archivos.xml y archivos.csv.
    'data': [

             'view/res_company_view.xml',

            ],
    #depends,  es una lista donde se agregan los módulos que deberían estar instalados (Módulos dependencia) para que el modulo pueda ser instalado en Odoo.
    'depends': ['base','account'],
    'js': [],
    'css': [],
    'qweb' : [],
    #'installable': True,
    #'auto_install': False,
    'application': True,
}
from models import *
from microsip_web.apps.main.filtros.models import *
from microsip_web.apps.config.models import Empresa
import autocomplete_light

autocomplete_light.register(ClavesArticulos, search_fields=('clave',),
    autocomplete_js_attributes={'placeholder': 'Clave ..'})

autocomplete_light.register(Articulos, autocomplete_js_attributes = {'placeholder':'Articulo'},
        search_fields = ('nombre',), choices= Articulos.objects.all())

autocomplete_light.register(Cliente, autocomplete_js_attributes={'placeholder': 'Busca un cliente ..'}, 
        search_fields=('nombre',), choices= Cliente.objects.all(), name='ClienteAutocomplete')

autocomplete_light.register(Ciudad, search_fields=('nombre',),
    autocomplete_js_attributes={'placeholder': 'Ciudad ..'})

autocomplete_light.register(CuentaCo, search_fields=('cuenta','nombre',),
    autocomplete_js_attributes={'placeholder': 'Cuenta ..'})

autocomplete_light.register(Carpeta, search_fields=('nombre',))
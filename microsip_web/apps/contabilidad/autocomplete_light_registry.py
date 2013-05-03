import autocomplete_light

from microsip_web.apps.inventarios.models import CuentaCo

autocomplete_light.register(CuentaCo, search_fields=('cuenta','nombre',),
    autocomplete_js_attributes={'placeholder': 'Cuenta ..'})
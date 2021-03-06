from django import template
from django.conf import settings

register = template.Library()

def microsip_module_btn(ms_module):
   result = ''
   if ms_module == 'admin':
      result = '<li><a href="/"> <i class="msicon-admin"></i></a></li>'

   if ms_module in settings.MICROSIP_MODULES:
      if ms_module == 'microsip_web.apps.ventas':
         result = '<li><a href="/ventas/articulos/"> <i class="msicon-ventas"></i><label class="small_screen"> Ventas </label></a></li>'
      elif ms_module == 'microsip_web.apps.inventarios':
         result ='<li><a href="/inventarios/almacenes/"> <i class="msicon-inventarios"></i> <label class="small_screen"> Inventarios</label></a></li>'
      elif ms_module == 'microsip_web.apps.cuentas_por_pagar':
         result ='<li><a  href="/cuentas_por_pagar/GenerarPolizas/"> <i class="msicon-cuentas_por_pagar"></i><label class="small_screen"> Cuentas por pagar</label></a></li>'
      elif ms_module == 'microsip_web.apps.cuentas_por_cobrar':
         result = '<li><a href="/cuentas_por_cobrar/GenerarPolizas/"> <i class="msicon-cuentas_por_cobrar"></i><label class="small_screen"> Cuentas por cobrar </label></a></li>'
      elif ms_module == 'microsip_web.apps.contabilidad':
         result = '<li><a href="/contabilidad/polizas_pendientes/"> <i class="msicon-contabilidad"></i><label class="small_screen"> Contabilidad </label></a></li>'
      elif ms_module == 'microsip_web.apps.punto_de_venta':
         result ='<li><a href="/punto_de_venta/facturas/"> <i class="msicon-punto_de_venta"></i><label class="small_screen"> Punto de venta</label></a></li>'
      elif ms_module == 'microsip_web.apps.compras':
         result = '<li><a href="/compras/ordenes"> <i class="msicon-compras"></i><label class="small_screen"> Compras</label></a></li>'
   
   return result

register.simple_tag(microsip_module_btn)

def ventas_tools_menu(tool_name):
   result = ''
   installed_modules = settings.MICROSIP_MODULES
   if tool_name == 'documentos' and 'microsip_web.apps.ventas.documentos' in installed_modules :
      result = '''<li class="dropdown">
         <a id="drop1" href="#"role="button" class="dropdown-toggle" data-toggle="dropdown"> <i class="icon-folder-close"></i>  
           Documentos <b class="caret"></b></a>
            <ul class="dropdown-menu" role="menu" aria-labelledby="drop1">
              <li><a tabindex="-1" href="/ventas/facturas/"> <i class="icon-file"></i> Facturas</a></li>
              <li><a tabindex="-1" href="/ventas/remisiones/"> <i class="icon-file"></i> Remisiones</a></li>
            </ul>
         </li>'''
   
   if tool_name == 'herramientas':
      if 'microsip_web.apps.ventas.herramientas' in installed_modules:
         result = '''
            <li class="dropdown">
               <a id="drop1" href="#" role="button" class="dropdown-toggle" data-toggle="dropdown"> <i class="icon-cog"></i> Herramientas <b class="caret"></b></a>
               <ul class="dropdown-menu" role="menu" aria-labelledby="drop1" style='text-align:left;'>
                 <li><a tabindex="-1" href="/ventas/generar_polizas/"><i class="icon-share"></i> Generar Polizas Contables</a></li>
                 <li role="presentation" class="divider"></li>
                 <li><a tabindex="-1" href="/ventas/PreferenciasEmpresa/"><i class="icon-cog"></i> Preferencias de la empresa</a></li>
               </ul>
             </li>
            '''

      elif 'microsip_web.apps.ventas.herramientas.generar_polizas' in installed_modules:
         result = '''
            <li class="dropdown">
               <a id="drop1" href="#" role="button" class="dropdown-toggle" data-toggle="dropdown"> <i class="icon-cog"></i> Herramientas <b class="caret"></b></a>
               <ul class="dropdown-menu" role="menu" aria-labelledby="drop1" style='text-align:left;'>
                 <li><a tabindex="-1" href="/ventas/Facturas/"><i class="icon-share"></i> Generar Polizas Contables</a></li>
                 <li role="presentation" class="divider"></li>
                 <li><a tabindex="-1" href="/ventas/PreferenciasEmpresa/"><i class="icon-cog"></i> Preferencias de la empresa</a></li>
               </ul>
             </li>
            '''

   return result

register.simple_tag(microsip_module_btn)

def pv_utilerias_btn():
   result = ''
   if 'microsip_web.apps.punto_de_venta.utilerias' in settings.MICROSIP_MODULES:
      result = '<li><a tabindex="-1" href="/punto_de_venta/utilerias/factura_global"><i class="icon-share"></i> Generar factura global</a></li>'
   return result

register.simple_tag(pv_utilerias_btn)
register.simple_tag(ventas_tools_menu)
register.simple_tag(microsip_module_btn)
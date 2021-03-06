#encoding:utf-8
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect
from django.template import RequestContext

from .models import *
from .forms import *

# user autentication
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

from microsip_web.libs import contabilidad
from microsip_web.libs.custom_db.main import get_conecctionname

##########################################
##                                      ##
##        Generacion de polizas         ##
##                                      ##
##########################################

def generar_polizas(fecha_ini=None, fecha_fin=None, ignorar_documentos_cont=True, crear_polizas_por='Documento', crear_polizas_de='', plantilla='', descripcion= '', connection_name= None, usuario_micorsip=''):
    depto_co = ContabilidadDepartamento.objects.get(clave='GRAL')
    error   = 0
    msg     = ''
    documentosCCData = []
    
    try:
        informacion_contable = InformacionContable_CC.objects.all()[:1]
        informacion_contable = informacion_contable[0]
    except ObjectDoesNotExist:
        error = 1

    #Si estadefinida la informacion contable no hay error!!!
    if error == 0:

        if ignorar_documentos_cont:
            documentosCC  = CuentasXCobrarDocumento.objects.filter(contabilizado ='N', concepto= crear_polizas_de , fecha__gte=fecha_ini, fecha__lte=fecha_fin).order_by('fecha')[:99]
        else:
            documentosCC  = CuentasXCobrarDocumento.objects.filter(concepto= crear_polizas_de , fecha__gte=fecha_ini, fecha__lte=fecha_fin).order_by('fecha')[:99]

        msg, documentosCCData = contabilidad.crear_polizas(
            origen_documentos   = 'cuentas_por_cobrar',
            documentos          = documentosCC, 
            depto_co            = depto_co,
            informacion_contable= informacion_contable,
            plantilla           = plantilla,
            crear_polizas_por   = crear_polizas_por,
            crear_polizas_de    = crear_polizas_de,
            msg = msg,
            descripcion = descripcion, 
            connection_name= connection_name,
            usuario_micorsip = usuario_micorsip,
        )

    elif error == 1 and msg=='':
        msg = 'No se han derfinido las preferencias de la empresa para generar polizas [Por favor definelas primero en Configuracion > Preferencias de la empresa]'

    return documentosCCData, msg

@login_required(login_url='/login/')
def generar_polizas_View(request, template_name='cuentas_por_cobrar/herramientas/generar_polizas/generar_polizas.html'):
    connection_name = get_conecctionname(request.session)
    if connection_name == '':
        return HttpResponseRedirect('/select_db/')
    
    documentosData  = []
    msg             = msg_resultados = msg_informacion =''

    if request.method == 'POST':
        
        form = GenerarPolizasManageForm(request.POST)
        if form.is_valid():
            fecha_ini               = form.cleaned_data['fecha_ini']
            fecha_fin               = form.cleaned_data['fecha_fin']
            ignorar_documentos_cont = form.cleaned_data['ignorar_documentos_cont']
            crear_polizas_por       = form.cleaned_data['crear_polizas_por']
            crear_polizas_de        = form.cleaned_data['crear_polizas_de']
            plantilla               = form.cleaned_data['plantilla']
            descripcion             = form.cleaned_data['descripcion']

            msg = 'es valido'

            documentosData, msg = generar_polizas(fecha_ini, fecha_fin, ignorar_documentos_cont, crear_polizas_por, crear_polizas_de, plantilla, descripcion, connection_name, request.user.username)
            if documentosData == []:
                msg_resultados = 'Lo siento, no se encontraron resultados para este filtro'
            else:
                form = GenerarPolizasManageForm( )       
                msg_informacion = 'Polizas generadas satisfactoriamente, *Ahora revisa las polizas pendientes generadas en el modulo de contabilidad'
    else:
        form = GenerarPolizasManageForm( )

    c = {'documentos':documentosData,'msg':msg,'form':form, 'msg_resultados':msg_resultados,'msg_informacion':msg_informacion,}
    return render_to_response(template_name, c, context_instance=RequestContext(request))

##########################################
##                                      ##
##        Preferencias de empresa       ##
##                                      ##
##########################################

@login_required(login_url='/login/')
def preferenciasEmpresa_View(request, template_name='cuentas_por_cobrar/herramientas/generar_polizas/preferencias_empresa.html'):
    try:
        informacion_contable = InformacionContable_CC.objects.all()[:1]
        informacion_contable = informacion_contable[0]
    except:
        informacion_contable = InformacionContable_CC()

    msg = ''
    if request.method == 'POST':
        form = InformacionContableManageForm(request.POST, instance=informacion_contable)
        if form.is_valid():
            form.save()
            msg = 'Datos Guardados Exitosamente'
    else:
        form = InformacionContableManageForm(instance=informacion_contable)

    plantillas = PlantillaPolizas_CC.objects.all()
    c= {'form':form,'msg':msg,'plantillas':plantillas,}
    return render_to_response(template_name, c, context_instance=RequestContext(request))

##########################################
##                                      ##
##              Plantillas              ##
##                                      ##
##########################################

@login_required(login_url='/login/')
def plantilla_poliza_manageView(request, id = None, template_name='cuentas_por_cobrar/herramientas/generar_polizas/plantilla_poliza.html'):
    message = ''

    if id:
        plantilla = get_object_or_404(PlantillaPolizas_CC, pk=id)
    else:
        plantilla =PlantillaPolizas_CC()

    plantilla_form = PlantillaPolizaManageForm(request.POST or None, instance=plantilla)
    plantilla_items = PlantillaPoliza_items_formset(ConceptoPlantillaPolizaManageForm, extra=1, can_delete=True)
    plantilla_items_formset = plantilla_items(request.POST or None, instance=plantilla)

    if plantilla_form.is_valid() and plantilla_items_formset.is_valid():
        plantilla = plantilla_form.save(commit = False)
        plantilla.save()

        #GUARDA CONCEPTOS DE PLANTILLA
        for concepto_form in plantilla_items_formset:
            Detalleplantilla = concepto_form.save(commit = False)
            #PARA CREAR UNO NUEVO
            if not Detalleplantilla.id:
                Detalleplantilla.plantilla_poliza_CC = plantilla
        
        plantilla_items_formset.save()
        return HttpResponseRedirect('/cuentas_por_cobrar/PreferenciasEmpresa/')
    
    c = {'plantilla_form': plantilla_form, 'formset': plantilla_items_formset , 'message':message,}
    return render_to_response(template_name, c, context_instance=RequestContext(request))

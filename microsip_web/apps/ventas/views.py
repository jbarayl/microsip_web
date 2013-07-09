#encoding:utf-8
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
from django.db.models import Q
from datetime import timedelta
from decimal import *
from django.core import serializers
#Paginacion
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# user autentication
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Max

import datetime, time

from models import *
from forms import *
from microsip_web.apps.inventarios.views import c_get_next_key
from microsip_web.apps.main.views import crear_polizas_contables

##########################################
##                                      ##
##        Generacion de polizas         ##
##                                      ##
##########################################

@login_required(login_url='/login/')
def pedido_ManageView(request, id = None, template_name='ventas/documentos/pedidos/pedido.html'):
    if id:
        documento = get_object_or_404(DoctoVe, pk=id)
    else:
        documento = DoctoVe()
    
    gruposgrupo_formset = formset_factory(form= GruposGrupo_ManageForm, can_delete=True,)

    if request.method == 'POST':
        doctove_items = DoctoVeDet_inlineformset(DoctoVeDet_ManageForm, extra=1, can_delete=True)
        formset = doctove_items(request.POST, request.FILES, instance=documento)
    else:
        doctove_items = DoctoVeDet_inlineformset(DoctoVeDet_ManageForm, extra=1, can_delete=True)
        formset = doctove_items(instance=documento)
        gruposgrupomain_form  = GruposGrupoMain_ManageForm()
        grupos_formset = gruposgrupo_formset()
        pedidoForm= DoctoVe_ManageForm(instance=documento)
        

    c = {'pedidoForm': pedidoForm,'formset':formset,'gruposgrupomain_form':gruposgrupomain_form,'grupos_formset':grupos_formset,}

    return render_to_response(template_name, c, context_instance=RequestContext(request))

def pedidos_view(request, template_name='ventas/documentos/pedidos/pedidos.html'):
    pedidos = DoctoVe.objects.filter(tipo='P')
    c = {'pedidos':pedidos, }
    return render_to_response(template_name, c, context_instance=RequestContext(request))   

def generar_polizas(fecha_ini=None, fecha_fin=None, ignorar_documentos_cont=True, crear_polizas_por='Documento', crear_polizas_de='', plantilla_facturas='', plantilla_devoluciones='', descripcion= ''):
    error   = 0
    msg     = ''
    documentosData = []
    documentosGenerados = []
    documentosDataDevoluciones = []
    depto_co = get_object_or_404(DeptoCo,clave='GRAL')
    try:
        informacion_contable = InformacionContable_V.objects.all()[:1]
        informacion_contable = informacion_contable[0]
    except ObjectDoesNotExist:
        error = 1
    
    #Si estadefinida la informacion contable no hay error!!!
    if error == 0:

        facturas    = []
        devoluciones= []
        if ignorar_documentos_cont:
            if crear_polizas_de     == 'F' or crear_polizas_de  == 'FD':
                facturas            = DoctoVe.objects.filter(Q(estado='N')|Q(estado='D'), tipo ='F', contabilizado ='N',  fecha__gte=fecha_ini, fecha__lte=fecha_fin).order_by('fecha')[:99]
            elif crear_polizas_de   == 'D' or crear_polizas_de  == 'FD':
                devoluciones        = DoctoVe.objects.filter(estado = 'N').filter(tipo  ='D', contabilizado ='N',  fecha__gte=fecha_ini, fecha__lte=fecha_fin).order_by('fecha')[:99]
        else:
            if crear_polizas_de     == 'F' or crear_polizas_de  == 'FD':
                facturas            = DoctoVe.objects.filter(Q(estado='N')|Q(estado='D'), tipo ='F', fecha__gte=fecha_ini, fecha__lte=fecha_fin).order_by('fecha')[:99]
            elif crear_polizas_de   == 'D' or crear_polizas_de  == 'FD':
                devoluciones        = DoctoVe.objects.filter(estado = 'N').filter(tipo  = 'D', fecha__gte=fecha_ini, fecha__lte=fecha_fin).order_by('fecha')[:99]

        #PREFIJO
        prefijo = informacion_contable.tipo_poliza_ve.prefijo
        if not informacion_contable.tipo_poliza_ve.prefijo:
            prefijo = ''

        if crear_polizas_de     == 'F' or crear_polizas_de  == 'FD':
            msg, documentosData = crear_polizas_contables(
                origen_documentos   = 'ventas',
                documentos          = facturas, 
                depto_co            = depto_co,
                informacion_contable= informacion_contable,
                plantilla           = plantilla_facturas,
                crear_polizas_por   = crear_polizas_por,
                crear_polizas_de    = crear_polizas_de,
                msg = msg,
                descripcion = descripcion, 
                tipo_documento = 'F',
            )
            documentosGenerados = documentosData
        if crear_polizas_de     == 'D' or crear_polizas_de  == 'FD':
            msg, documentosDataDevoluciones = crear_polizas_contables(
                origen_documentos   = 'ventas',
                documentos          = devoluciones, 
                depto_co            = depto_co,
                informacion_contable= informacion_contable,
                plantilla           = plantilla_devoluciones,
                crear_polizas_por   = crear_polizas_por,
                crear_polizas_de    = crear_polizas_de,
                msg = msg,
                descripcion = descripcion, 
                tipo_documento = 'D',
            )

    elif error == 1 and msg=='':
        msg = 'No se han derfinido las preferencias de la empresa para generar polizas [Por favor definelas primero en Configuracion > Preferencias de la empresa]'
    
    return documentosGenerados, documentosDataDevoluciones, msg

@login_required(login_url='/login/')
def facturas_View(request, template_name='ventas/herramientas/generar_polizas.html'):
    documentosData = []
    polizas_de_devoluciones = []
    msg             = msg_informacion =''
    error = 0

    if request.method == 'POST':
        form = GenerarPolizasManageForm(request.POST)
        if form.is_valid():

            fecha_ini               = form.cleaned_data['fecha_ini']
            fecha_fin               = form.cleaned_data['fecha_fin']
            ignorar_documentos_cont = form.cleaned_data['ignorar_documentos_cont']
            crear_polizas_por       = form.cleaned_data['crear_polizas_por']
            crear_polizas_de        = form.cleaned_data['crear_polizas_de']
            plantilla_facturas      = form.cleaned_data['plantilla']
            plantilla_devoluciones  = form.cleaned_data['plantilla_2']
            descripcion             = form.cleaned_data['descripcion']
            if (crear_polizas_de == 'F' and not plantilla_facturas== None) or (crear_polizas_de == 'D' and not plantilla_devoluciones== None) or (crear_polizas_de == 'FD' and not plantilla_facturas== None and not plantilla_devoluciones== None):
                documentosData, polizas_de_devoluciones, msg = generar_polizas(fecha_ini, fecha_fin, ignorar_documentos_cont, crear_polizas_por, crear_polizas_de, plantilla_facturas, plantilla_devoluciones, descripcion)
            else:
                error =1
                msg = 'Seleciona una plantilla'

            if (crear_polizas_de == 'F' or crear_polizas_de=='FD') and documentosData == [] and msg=='':
                msg = 'Lo siento, no se encontraron facturas para este filtro'
            elif (crear_polizas_de == 'D' or crear_polizas_de=='FD') and polizas_de_devoluciones == [] and msg=='':
                msg = 'Lo siento, no se encontraron devoluciones para este filtro'
            
            if crear_polizas_de == 'FD' and documentosData == [] and polizas_de_devoluciones == []:
                msg = 'Lo siento, no se encontraron facturas ni devoluciones para este filtro'
            
            if (not documentosData == [] or not polizas_de_devoluciones == []) and error == 0:
                form = GenerarPolizasManageForm()       
                msg_informacion = 'Polizas generadas satisfactoriamente, *Ahora revisa las polizas pendientes generadas en el modulo de contabilidad'
    else:
        form = GenerarPolizasManageForm()
    
    c = {'documentos':documentosData, 'polizas_de_devoluciones':polizas_de_devoluciones,'msg':msg,'form':form,'msg_informacion':msg_informacion,}
    return render_to_response(template_name, c, context_instance=RequestContext(request))

##########################################
##                                      ##
##        Preferencias de empresa       ##
##                                      ##
##########################################

@login_required(login_url='/login/')
def preferenciasEmpresa_View(request, template_name='ventas/herramientas/preferencias_empresa.html'):
    try:
        informacion_contable = InformacionContable_V.objects.all()[:1]
        informacion_contable = informacion_contable[0]
    except:
        informacion_contable = InformacionContable_V()

    cuenta_cliente_formset = modelformset_factory(clientes_config_cuenta, form= clientes_config_cuentaManageForm, can_delete=True,)
    
    msg = ''
    if request.method == 'POST':
        formset = cuenta_cliente_formset(request.POST, request.FILES)

        form = InformacionContableManageForm(request.POST, instance=informacion_contable)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            formset = cuenta_cliente_formset()
            msg = 'Datos Guardados Exitosamente'
    else:
        form = InformacionContableManageForm(instance=informacion_contable)
        formset = cuenta_cliente_formset()
        
    plantillas = PlantillaPolizas_V.objects.all()
    c= {'form':form,'msg':msg,'plantillas':plantillas,'formset':formset,}
    return render_to_response(template_name, c, context_instance=RequestContext(request))

##########################################
##                                      ##
##              Plantillas              ##
##                                      ##
##########################################

@login_required(login_url='/login/')
def plantilla_poliza_manageView(request, id = None, template_name='ventas/herramientas/plantilla_poliza.html'):
    message = ''

    if id:
        plantilla = get_object_or_404(PlantillaPolizas_V, pk=id)
    else:
        plantilla =PlantillaPolizas_V()

    if request.method == 'POST':
        plantilla_form = PlantillaPolizaManageForm(request.POST, request.FILES, instance=plantilla)

        plantilla_items         = PlantillaPoliza_items_formset(ConceptoPlantillaPolizaManageForm, extra=1, can_delete=True)
        plantilla_items_formset = plantilla_items(request.POST, request.FILES, instance=plantilla)
        
        if plantilla_form.is_valid() and plantilla_items_formset.is_valid():
            plantilla = plantilla_form.save(commit = False)
            plantilla.save()

            #GUARDA CONCEPTOS DE PLANTILLA
            for concepto_form in plantilla_items_formset :
                Detalleplantilla = concepto_form.save(commit = False)
                #PARA CREAR UNO NUEVO
                if not Detalleplantilla.id:
                    Detalleplantilla.plantilla_poliza_v = plantilla
            
            plantilla_items_formset .save()
            return HttpResponseRedirect('/ventas/PreferenciasEmpresa/')
    else:
        plantilla_items = PlantillaPoliza_items_formset(ConceptoPlantillaPolizaManageForm, extra=1, can_delete=True)
        plantilla_form= PlantillaPolizaManageForm(instance=plantilla)
        plantilla_items_formset  = plantilla_items(instance=plantilla)
    
    c = {'plantilla_form': plantilla_form, 'formset': plantilla_items_formset , 'message':message,}

    return render_to_response(template_name, c, context_instance=RequestContext(request))

@login_required(login_url='/login/')
def plantilla_poliza_delete(request, id = None):
    plantilla = get_object_or_404(PlantillaPolizas_V, pk=id)
    plantilla.delete()

    return HttpResponseRedirect('/ventas/PreferenciasEmpresa/')


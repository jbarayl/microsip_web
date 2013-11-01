 #encoding:utf-8
from django.utils import simplejson
from dajaxice.decorators import dajaxice_register
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.core import serializers
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.core import management
import json
import datetime, time
from django.db.models import Q
from mobi.decorators import detect_mobile
from decimal import *
from models import *
from microsip_web.libs.custom_db.main import next_id, get_existencias_articulo, first_or_none
from microsip_web.libs.tools import split_seq
from django.db import connections, transaction
from microsip_web.libs.custom_db.main import get_conecctionname
from microsip_web.apps.config.models import DerechoUsuario

def allow_microsipuser( username = None, clave_objeto=  None ):
    return DerechoUsuario.objects.filter(usuario__nombre = username, clave_objeto = clave_objeto).exists() or username == 'SYSDBA'

@dajaxice_register( method = 'GET' )
def remove_seriesinventario_byarticulo( request, **kwargs ):
    connection_name = get_conecctionname( request.session )
    articulo_id = kwargs.get( 'articulo_id', None )
    articulo = Articulos.objects.get( pk = articulo_id )
    articulo_clave = first_or_none( ClavesArticulos.objects.filter( articulo = articulo ) )
    almacen_id = kwargs.get( 'almacen_id', None )
    salida_id = kwargs.get( 'salida_id', None )
    salida = DoctosIn.objects.get( pk = salida_id )
    series = kwargs.get( 'series', None )
    series= series.split(',')
    msg = ''
    for serie in series:
        if not DesgloseEnDiscretos.objects.filter( art_discreto__articulo_id = articulo_id, art_discreto__clave = serie ).exists() and serie != '':
            msg = '%s El numero de serie %s no esta registrado.'% (msg, serie)
        if serie == '':
            series.remove(serie)

    series_count = len(series)
    if msg == '':
        detalle_salidas = first_or_none( DoctosInDet.objects.filter( articulo = articulo, doctosIn__id = salida_id ) )
        if not detalle_salidas:
            detalle_salidas = DoctosInDet.objects.create( 
                id = next_id( 'ID_DOCTOS', connection_name ),
                doctosIn = salida,
                almacen = salida.almacen,
                concepto = salida.concepto,
                tipo_movto = 'S',
                claveArticulo = articulo_clave,
                articulo = articulo,
                unidades = series_count,
                costo_unitario = articulo.costo_ultima_compra,
                costo_total = series_count * articulo.costo_ultima_compra,
                fechahora_ult_modif = datetime.now(),
                usuario_ult_modif = request.user.username,
                detalle_modificacionestime = '%s %s/%s=%s,'%( datetime.now().strftime("%d-%b-%Y %I:%M %p"), request.user.username, 'ubicacion', series_count)
                 )
        else:
            detalle_salidas.unidades = detalle_salidas.unidades + series_count
            detalle_salidas.fechahora_ult_modif =  datetime.now()
            detalle_salidas.usuario_ult_modif = request.user.username

            if detalle_salidas.detalle_modificacionestime == None:
                detalle_salidas.detalle_modificacionestime = ''

            detalle_salidas.detalle_modificacionestime += '%s %s/%s=-%s,'%( datetime.now().strftime("%d-%b-%Y %I:%M %p"), request.user.username, 'ubicacion', series_count)
            detalle_salidas.save( update_fields = [ 'unidades', 'fechahora_ult_modif','detalle_modificacionestime', ] );
        
        for serie in series:
            articulo_discreto = ArticulosDiscretos.objects.get( clave = serie, articulo = articulo, tipo = 'S' )
            DesgloseEnDiscretos.objects.filter( id = -1, docto_in_det = detalle_salidas, art_discreto = articulo_discreto, unidades = 1 ).delete()
            exist_discretos = ExistDiscreto.objects.get(articulo_discreto= articulo_discreto, almacen = salida.almacen)
            exist_discretos.existencia = 0
            exist_discretos.save()

        c = connections[ connection_name ].cursor()
        c.execute( "DELETE FROM SALDOS_IN where saldos_in.articulo_id = %s;"% articulo.id )
        c.execute( "EXECUTE PROCEDURE RECALC_SALDOS_ART_IN %s;"% articulo.id )
        transaction.commit_unless_managed()
        c.close()

        management.call_command( 'syncdb', database = connection_name )

        msg = 'articulos agregados'

    return simplejson.dumps( { 'msg' : msg, } ) 

@dajaxice_register( method = 'GET' )
def add_seriesinventario_byarticulo( request, **kwargs ):
    connection_name = get_conecctionname( request.session )
    articulo_id = kwargs.get( 'articulo_id', None )
    articulo = Articulos.objects.get( pk = articulo_id )
    articulo_clave = first_or_none( ClavesArticulos.objects.filter( articulo = articulo ) )
    almacen_id = kwargs.get( 'almacen_id', None )
    entrada_id = kwargs.get( 'entrada_id', None )
    entrada = DoctosIn.objects.get( pk = entrada_id )
    series = kwargs.get( 'series', None )
    series= series.split(',')
    msg = ''
    for serie in series:
        if DesgloseEnDiscretos.objects.filter( art_discreto__articulo_id = articulo_id, art_discreto__clave = serie ).exists() and serie != '':
            msg = '%s El numero de serie %s ya esta registrado.'% (msg, serie)
        if serie == '':
            series.remove(serie)

    series_count = len(series)
    if msg == '':
        detalle_entradas = first_or_none( DoctosInDet.objects.filter( articulo = articulo, doctosIn__id = entrada_id ) )
        if not detalle_entradas:
            detalle_entradas = DoctosInDet.objects.create( 
                id = next_id( 'ID_DOCTOS', connection_name ),
                doctosIn = entrada,
                almacen = entrada.almacen,
                concepto = entrada.concepto,
                tipo_movto = 'E',
                claveArticulo = articulo_clave,
                articulo = articulo,
                unidades = series_count,
                costo_unitario = articulo.costo_ultima_compra,
                costo_total = series_count * articulo.costo_ultima_compra,
                fechahora_ult_modif = datetime.now(),
                usuario_ult_modif = request.user.username,
                detalle_modificacionestime = '%s %s/%s=%s,'%( datetime.now().strftime("%d-%b-%Y %I:%M %p"), request.user.username, 'ubicacion', series_count)
                 )
        else:
            detalle_entradas.unidades = detalle_entradas.unidades + series_count
            detalle_entradas.fechahora_ult_modif =  datetime.now()
            detalle_entradas.usuario_ult_modif = request.user.username

            if detalle_entradas.detalle_modificacionestime == None:
                detalle_entradas.detalle_modificacionestime = ''

            detalle_entradas.detalle_modificacionestime += '%s %s/%s=%s,'%( datetime.now().strftime("%d-%b-%Y %I:%M %p"), request.user.username, 'ubicacion', series_count)
            detalle_entradas.save( update_fields = [ 'unidades', 'fechahora_ult_modif','detalle_modificacionestime', ] );
        
        for serie in series:
            try:
                articulo_discreto = ArticulosDiscretos.objects.get( clave = serie, articulo = articulo, tipo = 'S' )
            except ObjectDoesNotExist:
                articulo_discreto = ArticulosDiscretos.objects.create( id = next_id( 'ID_CATALOGOS', connection_name ) , clave= serie, articulo= articulo, tipo='S')

            DesgloseEnDiscretos.objects.create( id = -1, docto_in_det = detalle_entradas, art_discreto = articulo_discreto, unidades = 1 )
            
            try:
                exist_discretos = ExistDiscreto.objects.get(articulo_discreto= articulo_discreto, almacen = entrada.almacen)
            except ObjectDoesNotExist:
                ExistDiscreto.objects.create( id = -1, articulo_discreto = articulo_discreto, almacen = entrada.almacen, existencia = 1)
            else:
                exist_discretos.existencia = 1
                exist_discretos.save()

        c = connections[ connection_name ].cursor()
        c.execute( "DELETE FROM SALDOS_IN where saldos_in.articulo_id = %s;"% articulo.id )
        c.execute( "EXECUTE PROCEDURE RECALC_SALDOS_ART_IN %s;"% articulo.id )
        transaction.commit_unless_managed()
        c.close()

        management.call_command( 'syncdb', database = connection_name )

        msg = 'articulos agregados'

    return simplejson.dumps( { 'msg' : msg, } ) 

@dajaxice_register( method = 'GET' )
def get_seriesinventario_byarticulo( request, **kwargs ):
    ''' Para ajustar un articulo a las unidades indicadas sin importar su existencia actual '''
    #Paramentros
    articulo_id = kwargs.get( 'articulo_id', None )
    almacen_id = kwargs.get( 'almacen_id', None )
    series = ''
    ariculos_discretos = DesgloseEnDiscretos.objects.filter( 
        Q(docto_in_det__doctosIn__concepto = 27) | Q(docto_in_det__doctosIn__concepto = 38),
        docto_in_det__doctosIn__almacen_id = almacen_id,
        docto_in_det__doctosIn__descripcion = 'ES INVENTARIO',
        art_discreto__articulo_id = articulo_id,
        )
    for articulo_discreto in ariculos_discretos:
        series = "%s%s, "% (series, articulo_discreto.art_discreto.clave)
    
    return simplejson.dumps( { 'series' : series, } ) 

def ajustar_existencias( **kwargs ):
    ''' Para ajustar un articulo a las unidades indicadas sin importar su existencia actual '''
    #Paramentros
    articulo_id = kwargs.get( 'articulo_id', None )
    ajustar_a = kwargs.get( 'ajustar_a', None )
    almacen = kwargs.get( 'almacen', None )
    connection_name = kwargs.get( 'connection_name', None )

    entradas, salidas, existencias, inv_fin = get_existencias_articulo(
        articulo_id = articulo_id, 
        connection_name = connection_name, 
        fecha_inicio = datetime.now().strftime( "01/01/%Y" ),
        almacen = almacen, 
        )

    unidades_a_insertar = -inv_fin + ajustar_a
    return unidades_a_insertar

def add_existenciasarticulo_byajustes( **kwargs ):
    """ Para agregar existencia a un articulo por ajuste 
        En caso de que el articulo no tenga costo indicado [se le aplica el de la ultima compra]
    """

    #Paramentros
    ajustar_primerconteo = kwargs.get( 'ajustar_primerconteo', None )
    ubicacion = kwargs.get( 'ubicacion', None )
    articulo_id = kwargs.get( 'articulo_id', None )
    articulo = Articulos.objects.get( pk = articulo_id )

    entrada_id = kwargs.get( 'entrada_id', None )
    entrada = DoctosIn.objects.get( pk = entrada_id )
    salida_id = kwargs.get( 'salida_id', None )
    salida = DoctosIn.objects.get( pk = salida_id )
    
    almacen_id = kwargs.get( 'almacen_id', None )
    almacen = Almacenes.objects.get( pk = almacen_id)

    request_session = kwargs.get( 'request_session', 0 )
    request_user = kwargs.get( 'request_user', 0 )
    connection_name = get_conecctionname( request_session )
    
    detalle_unidades = kwargs.get( 'detalle_unidades', 0 )
    detalle_costo_unitario = kwargs.get( 'detalle_costo_unitario', articulo.costo_ultima_compra )
    
    puede_modificar_costos = allow_microsipuser( username = request_user.username, clave_objeto = 469)

    detalles_entradas_ultimocosto = first_or_none( DoctosInDet.objects.filter(
            Q( doctosIn__concepto = 27 ),
            articulo = articulo,
            almacen = almacen,
            doctosIn__descripcion = 'ES INVENTARIO'
            ).order_by('-fechahora_ult_modif').values_list( 'costo_unitario', flat = True ) )

    if not detalles_entradas_ultimocosto:
         detalles_entradas_ultimocosto = articulo.costo_ultima_compra

    existe_en_detalles = DoctosInDet.objects.filter( 
        Q( doctosIn__concepto = 27 ) | Q( doctosIn__concepto = 38 ),
        articulo = articulo,
        almacen = almacen,
        doctosIn__descripcion = 'ES INVENTARIO',
        ).count() > 0

    detalle_entradas = first_or_none( DoctosInDet.objects.filter( articulo = articulo, doctosIn = entrada ) )
    detalle_salidas = first_or_none( DoctosInDet.objects.filter( articulo = articulo, doctosIn = salida ) )
    articulo_clave = first_or_none( ClavesArticulos.objects.filter( articulo = articulo ) )

    detalle = DoctosInDet(
        articulo = articulo,
        claveArticulo = articulo_clave,
        almacen = almacen,
        unidades = detalle_unidades,
        )
    
    #Logica

    #Si no se existe arituclo en documentos se ajustan unidades
    if not existe_en_detalles and ajustar_primerconteo:
        detalle.unidades = ajustar_existencias( articulo_id = articulo.id, ajustar_a = detalle.unidades ,almacen = almacen , connection_name = connection_name )

    es_nuevo = False

    #SALIDA
    if detalle.unidades <= 0:
        #si no existe detalle salidas
        if not detalle_salidas:
            es_nuevo = True
            detalle_salidas = detalle
            detalle_salidas.id = next_id( 'ID_DOCTOS', connection_name )
            detalle_salidas.doctosIn = salida
            detalle_salidas.concepto = salida.concepto
            detalle_salidas.tipo_movto ='S'
            detalle_salidas.unidades = -detalle_salidas.unidades
        #Si exitse detalle salidas
        elif detalle_salidas:
            detalle_salidas.unidades = detalle_salidas.unidades + ( -detalle.unidades ) 

        #Desde salida no se permite cambiar costo unitario
        detalle_salidas.costo_unitario = detalles_entradas_ultimocosto
        detalle = detalle_salidas
    
    #ENTRADA
    elif detalle.unidades > 0:
        if not detalle_entradas:
            es_nuevo = True
            detalle_entradas = detalle
            detalle_entradas.id = next_id( 'ID_DOCTOS', connection_name )
            detalle_entradas.doctosIn = entrada
            detalle_entradas.concepto = entrada.concepto
            detalle_entradas.tipo_movto ='E'

        elif detalle_entradas:
            detalle_entradas.unidades = detalle_entradas.unidades + detalle.unidades
            
        detalle = detalle_entradas
    
    #MODIFICA COSTOS
    #Si es entrada y tiene pribilegios modifica el costo unitario
    # if puede_modificar_costos and detalle.tipo_movto == 'E':
    #    detalle.costo_unitario = detalle_costo_unitario 
    # else:
    # detalle_costo_unitario = first_or_none( DoctosInDet.objects.filter(
    #     Q( doctosIn__concepto = 27 ),
    #     articulo = articulo,
    #     almacen = almacen,
    #     doctosIn__descripcion = 'ES INVENTARIO'
    #     ).order_by('-fechahora_ult_modif').values_list( 'costo_unitario', flat = True ) )      
    
    # if not detalle_costo_unitario:
    detalle_costo_unitario = articulo.costo_ultima_compra
    detalle.costo_unitario = detalle_costo_unitario
    detalle.costo_total = detalle.unidades * detalle.costo_unitario
    detalle.fechahora_ult_modif = datetime.now()

    # HISTORIAL DE MODIFICACIONES
    if detalle.detalle_modificacionestime == None:
        detalle.detalle_modificacionestime = ''
    detalle_ajuste = '' 
    if not existe_en_detalles:   
        detalle_ajuste = '(AJ.=%s)'%detalle.unidades
    detalle.detalle_modificacionestime += '%s %s/%s=%s%s,'%( datetime.now().strftime("%d-%b-%Y %I:%M %p"), request_user.username, ubicacion, detalle_unidades, detalle_ajuste)

    if es_nuevo:
        detalle.save()
    else:    
        detalle.save( update_fields = [ 'unidades', 'costo_unitario', 'costo_total', 'fechahora_ult_modif','detalle_modificacionestime', ] );

    c = connections[ connection_name ].cursor()
    c.execute( "DELETE FROM SALDOS_IN where saldos_in.articulo_id = %s;"% articulo.id )
    c.execute( "EXECUTE PROCEDURE RECALC_SALDOS_ART_IN %s;"% articulo.id )
    transaction.commit_unless_managed()
    c.close()

    management.call_command( 'syncdb', database = connection_name )

    entradasx, salidasx, existenciasx, exitencia = get_existencias_articulo(
        articulo_id = articulo.id, 
        connection_name = connection_name, 
        fecha_inicio = datetime.now().strftime( "01/01/%Y" ),
        almacen = almacen, 
        )

    datos = {'error_message': '', 'alamcen_id': almacen.ALMACEN_ID, 'articulo_nombre': articulo.nombre, 'existencia_actual': str(exitencia) }
    
    return datos

@dajaxice_register( method = 'GET' )
def close_inventario_byalmacen_view( request, **kwargs ):
    """ Para agregar existencia a un articulo por ajuste"""
    #Paramentros
    almacen_id = kwargs.get( 'almacen_id', None )
    DoctosIn.objects.filter(almacen__ALMACEN_ID = almacen_id, descripcion='ES INVENTARIO').update(descripcion= 'INVENTARIO CERRADO')
    return simplejson.dumps( { 'mensaje' : 'Inventario cerrado', } ) 

@detect_mobile
@dajaxice_register( method = 'GET' )
def add_existenciasarticulo_byajustes_view( request, **kwargs ):
    """ Para agregar existencia a un articulo por ajuste"""
    #Paramentros
    ajustar_primerconteo = kwargs.get( 'ajustar_primerconteo', False )

    ubicacion = kwargs.get( 'ubicacion', None )
    articulo_id = kwargs.get( 'articulo_id', None )
    entrada_id = kwargs.get( 'entrada_id', None )
    salida_id = kwargs.get( 'salida_id', None )
    is_mobile =  kwargs.get( 'is_mobile', False )
    detalle_unidades = Decimal( kwargs.get( 'detalle_unidades', None ) )
    detalle_costo_unitario = Decimal( kwargs.get( 'detalle_costo_unitario', None ) )
    entrada = DoctosIn.objects.get( pk = entrada_id )
    almacen_id = entrada.almacen.ALMACEN_ID

    #Para dos almacenes
    entrada2_id = kwargs.get( 'entrada2_id', None )
    salida2_id = kwargs.get( 'salida2_id', None )
    almacen_sinventas = first_or_none( Almacenes.objects.filter( nombre = 'Almacen sin ventas' ))
    if almacen_sinventas and entrada2_id and salida2_id:

        add_existenciasarticulo_byajustes(
        articulo_id = articulo_id,
        entrada_id = entrada2_id,
        salida_id = salida2_id,
        detalle_unidades = detalle_unidades,
        request_session = request.session,
        request_user = request.user,
        ubicacion = ubicacion,
        almacen_id = almacen_sinventas.ALMACEN_ID,
        ajustar_primerconteo = ajustar_primerconteo,
        )

    datos = add_existenciasarticulo_byajustes(
        articulo_id = articulo_id,
        entrada_id = entrada_id,
        salida_id = salida_id,
        detalle_unidades = detalle_unidades,
        detalle_costo_unitario = detalle_costo_unitario,
        request_session = request.session,
        request_user = request.user,
        ubicacion = ubicacion,
        almacen_id = almacen_id,
        ajustar_primerconteo = ajustar_primerconteo,
        )


    datos['is_mobile'] = is_mobile
    
    return HttpResponse( json.dumps( datos ), mimetype = "application/javascript" )

@dajaxice_register( method = 'GET' )
def add_articulossinexistencia( request, **kwargs ):
    """ Agrega articulos almacenables de la linea indicada faltantes en los documentos de ajustes indicados.  """
    #Paramentros
    ubicacion = kwargs.get( 'ubicacion', None )
    entrada_id = kwargs.get( 'entrada_id', None )
    entrada = DoctosIn.objects.get( pk = entrada_id )
    almacen = entrada.almacen

    salida_id = kwargs.get( 'salida_id', None )

    salida = DoctosIn.objects.get( pk = salida_id )
    entrada = DoctosIn.objects.get( pk = entrada_id )

    articulos_endocumentos = list( set( DoctosInDet.objects.filter(
        Q( doctosIn__concepto = 27 ) | Q( doctosIn__concepto = 38 ),
        almacen = almacen,
        doctosIn__descripcion = 'ES INVENTARIO'
        ).order_by( '-articulo' ).values_list( 'articulo__id', flat = True ) ) )
    articulos_sinexistencia = Articulos.objects.exclude( estatus = 'B').filter( es_almacenable = 'S', seguimiento='N').exclude(pk__in = articulos_endocumentos ).order_by( '-id' ).values_list( 'id', flat = True )
    
    total_articulos_sinexistencia = articulos_sinexistencia.count()
    articulos_sinexistencia = articulos_sinexistencia[0:9000]

    articulos_sinexistencia_list = split_seq( articulos_sinexistencia, 2000 )
    articulos_agregados = 0

    for articulos_sinexistencia_sublist in articulos_sinexistencia_list:
        detalles_en_ceros = 0
        for articulo_id in articulos_sinexistencia_sublist:
            
            add_existenciasarticulo_byajustes(
                    articulo_id = articulo_id ,
                    entrada_id = entrada_id,
                    salida_id = salida_id,
                    detalle_unidades = 0,
                    request_session = request.session,
                    request_user = request.user,
                    ubicacion = ubicacion,
                    almacen_id = almacen.ALMACEN_ID,
                    )
            detalles_en_ceros = detalles_en_ceros + 1
            
        articulos_agregados = articulos_agregados + detalles_en_ceros

    articulos_pendientes = total_articulos_sinexistencia -  articulos_agregados
    return simplejson.dumps( { 'articulos_agregados' : articulos_agregados, 'articulo_pendientes' : articulos_pendientes, } )

@dajaxice_register( method = 'GET' )
def add_articulossinexistencia_bylinea( request, **kwargs ):
    """ Agrega articulos almacenables de la linea indicada faltantes en los documentos de ajustes indicados.  """
    #Paramentros
    ubicacion = kwargs.get( 'ubicacion', None )
    linea_id = kwargs.get( 'linea_id', None )
    entrada_id = kwargs.get( 'entrada_id', None )
    salida_id = kwargs.get( 'salida_id', None )

    entrada = DoctosIn.objects.get( pk = entrada_id )
    linea = LineaArticulos.objects.get( pk = linea_id )
    almacen = entrada.almacen

    articulos_endocumentos = list( set( DoctosInDet.objects.filter(
        Q( doctosIn__concepto = 27 ) | Q( doctosIn__concepto = 38 ),
        almacen = almacen,
        doctosIn__descripcion = 'ES INVENTARIO'
        ).order_by( '-articulo' ).values_list( 'articulo__id', flat = True ) ) )

    articulos_sinexistencia = Articulos.objects.exclude(estatus = 'B').filter( es_almacenable = 'S', seguimiento='N', linea = linea ).exclude(pk__in = articulos_endocumentos ).order_by( '-id' ).values_list( 'id', flat = True )
    
    total_articulos_sinexistencia = articulos_sinexistencia.count()
    articulos_sinexistencia = articulos_sinexistencia[0:9000]

    articulos_sinexistencia_list = split_seq( articulos_sinexistencia, 2000 )
    articulos_agregados = 0

    for articulos_sinexistencia_sublist in articulos_sinexistencia_list:
        detalles_en_ceros = 0
        for articulo_id in articulos_sinexistencia_sublist:
            
            add_existenciasarticulo_byajustes(
                    articulo_id = articulo_id ,
                    entrada_id = entrada_id,
                    salida_id = salida_id,
                    detalle_unidades = 0,
                    request_session = request.session,
                    request_user = request.user,
                    ubicacion = ubicacion,
                    almacen_id = almacen.ALMACEN_ID
                    )
            detalles_en_ceros = detalles_en_ceros + 1
            
        articulos_agregados = articulos_agregados + detalles_en_ceros

    articulos_pendientes = total_articulos_sinexistencia -  articulos_agregados
    return simplejson.dumps( { 'articulos_agregados' : articulos_agregados, 'articulo_pendientes' : articulos_pendientes, } )

@dajaxice_register( method = 'GET' )
def get_existenciasarticulo_byclave( request, **kwargs ):
    """ Para obterner existencia de un articulo segun clave del articulo """
    #Paramentros
    almacen_nombre = kwargs.get( 'almacen', None)
    almacen = Almacenes.objects.get(nombre = almacen_nombre)
    entrada_id = kwargs.get( 'entrada_id', None )
    articulo_clave = kwargs.get( 'articulo_clave', None)
    connection_name = get_conecctionname( request.session )
    
    #variables de salida
    error = ""
    inv_fin = 0
    articulo_linea = ''
    costo_ultima_compra = 0
    articulo_id = ''
    articulo_nombre = ''
    articulo_seguimiento = ''
    clave_articulo = first_or_none( ClavesArticulos.objects.exclude( articulo__estatus = 'B').filter( clave = articulo_clave, articulo__seguimiento = 'N' ) )
    opciones_clave = {}
    
    detalle_modificacionestime = ''
    detalle_modificacionestime_salidas = ''
    ya_ajustado = False
    if clave_articulo:
        articulo = Articulos.objects.get( pk = clave_articulo.articulo.id )

        detalles_all = DoctosInDet.objects.filter(
            Q( doctosIn__concepto = 27 ) | Q( doctosIn__concepto = 38 ),
            articulo = articulo,
            almacen = almacen,
            doctosIn__descripcion = 'ES INVENTARIO').order_by('fechahora_ult_modif')
        
        if detalles_all:
            ya_ajustado = True
        else:
            c = connections[ connection_name ].cursor()
            c.execute( "DELETE FROM SALDOS_IN where saldos_in.articulo_id = %s;"% articulo.id )
            c.execute( "EXECUTE PROCEDURE RECALC_SALDOS_ART_IN %s;"% articulo.id )
            transaction.commit_unless_managed()
            c.close()

            management.call_command( 'syncdb', database = connection_name )

        entradas, salidas, existencias, inv_fin = get_existencias_articulo(
            articulo_id = articulo.id,
            connection_name = connection_name, 
            fecha_inicio = datetime.now().strftime( "01/01/%Y" ),
            almacen = almacen_nombre, )
        
        articulo_id = articulo.id
        articulo_nombre = articulo.nombre
        try:
            articulo_linea = articulo.linea.nombre
        except ObjectDoesNotExist:
            articulo_linea = 'No indicada aun'

        articulo_seguimiento = articulo.seguimiento
        costo_ultima_compra = None

        detalles_entradas = DoctosInDet.objects.filter(
            Q( doctosIn__concepto = 27 ),
            articulo = articulo,
            almacen = almacen,
            doctosIn__descripcion = 'ES INVENTARIO'
            ).order_by('fechahora_ult_modif')

        detalles_salidas = DoctosInDet.objects.filter(
            Q( doctosIn__concepto = 38 ),
            articulo = articulo,
            almacen = almacen,
            doctosIn__descripcion = 'ES INVENTARIO').order_by('fechahora_ult_modif')

        for detalle_entradas in detalles_entradas:
            detalle_modificacionestime = detalle_modificacionestime + detalle_entradas.detalle_modificacionestime
            costo_ultima_compra = detalle_entradas.costo_unitario
        
        for detalle_salidas in detalles_salidas:
            if not detalle_salidas.detalle_modificacionestime:
                detalle_salidas.detalle_modificacionestime = ''

            detalle_modificacionestime_salidas = detalle_modificacionestime_salidas + detalle_salidas.detalle_modificacionestime
            #costo_ultima_compra = detalle_salidas.costo_unitario
        


        #Si no existe un costo ya asignado se asigna el del articulo    
        if not costo_ultima_compra:
            costo_ultima_compra = str(articulo.costo_ultima_compra)
    else:
        error = "no_existe_clave"
        claves = ClavesArticulos.objects.exclude(articulo__estatus='B').filter( clave__contains = articulo_clave, articulo__seguimiento = 'N' )
        for c in claves:
            opciones_clave[ str( c.clave ) ] = c.articulo.nombre
    
    if not detalle_modificacionestime:
        detalle_modificacionestime = ''

    datos = { 
        'error_msg' : error,
        'ya_ajustado': ya_ajustado,
        'articulo_id' : articulo_id,
        'articulo_seguimiento': articulo_seguimiento,
        'articulo_nombre' : articulo_nombre,
        'existencias' : str(inv_fin), 
        'costo_ultima_compra' : str(costo_ultima_compra),
        'opciones_clave': opciones_clave,
        'detalle_modificacionestime': detalle_modificacionestime,
        'detalle_modificacionestime_salidas': detalle_modificacionestime_salidas,
        'articulo_linea' : articulo_linea,
        }
    return HttpResponse( json.dumps( datos ), mimetype = "application/javascript" )

@dajaxice_register( method = 'GET' )
def get_existenciasarticulo_byid( request, **kwargs ):
    """ Para obterner existencia de un articulo segun id del articulo """
    #Paramentros
    almacen_nombre = kwargs.get( 'almacen', None)
    almacen = Almacenes.objects.get(nombre = almacen_nombre)
    articulo_id = kwargs.get( 'articulo_id', None)
    entrada_id = kwargs.get( 'entrada_id', None )
    connection_name = get_conecctionname( request.session )
    detalle_modificacionestime = ''
    detalle_modificacionestime_salidas = ''
    ya_ajustado = False
    costo_ultima_compra = None
    
    articulo = Articulos.objects.get( pk = articulo_id )

    detalles_all = DoctosInDet.objects.filter(
        Q( doctosIn__concepto = 27 ) | Q( doctosIn__concepto = 38 ),
        articulo = articulo,
        almacen = almacen,
        doctosIn__descripcion = 'ES INVENTARIO').order_by('fechahora_ult_modif')

    if detalles_all:
        ya_ajustado = True
    else:
        c = connections[ connection_name ].cursor()
        c.execute( "DELETE FROM SALDOS_IN where saldos_in.articulo_id = %s;"% articulo.id )
        c.execute( "EXECUTE PROCEDURE RECALC_SALDOS_ART_IN %s;"% articulo.id )
        transaction.commit_unless_managed()
        c.close()

        management.call_command( 'syncdb', database = connection_name )

    entradas, salidas, existencias, inv_fin = get_existencias_articulo(
        articulo_id = articulo_id , 
        connection_name = connection_name, 
        fecha_inicio = datetime.now().strftime( "01/01/%Y" ),
        almacen = almacen_nombre, )
 
    detalles_entradas = DoctosInDet.objects.filter(
        Q( doctosIn__concepto = 27 ),
        articulo = articulo,
        almacen = almacen,
        doctosIn__descripcion = 'ES INVENTARIO').order_by('fechahora_ult_modif')

    detalles_salidas = DoctosInDet.objects.filter(
        Q( doctosIn__concepto = 38 ),
        articulo = articulo,
        almacen = almacen,
        doctosIn__descripcion = 'ES INVENTARIO').order_by('fechahora_ult_modif')

    for detalle_entradas in detalles_entradas:
        if not detalle_entradas.detalle_modificacionestime:
            detalle_entradas.detalle_modificacionestime = ''

        detalle_modificacionestime = detalle_modificacionestime + detalle_entradas.detalle_modificacionestime
        costo_ultima_compra = detalle_entradas.costo_unitario

    for detalle_salidas in detalles_salidas:
        if not detalle_salidas.detalle_modificacionestime:
            detalle_salidas.detalle_modificacionestime = ''

        detalle_modificacionestime_salidas = detalle_modificacionestime_salidas + detalle_salidas.detalle_modificacionestime
        #costo_ultima_compra = detalle_salidas.costo_unitario

    #Si no existe un costo ya asignado se asigna el del articulo    
    if not costo_ultima_compra:
        costo_ultima_compra = str(articulo.costo_ultima_compra)
    
    if not detalle_modificacionestime:
        detalle_modificacionestime = ''

    try:
        articulo_linea = articulo.linea.nombre
    except ObjectDoesNotExist:
        articulo_linea = 'No indicada aun'

    return simplejson.dumps( { 
        'existencias' : int( inv_fin ), 
        'ya_ajustado': ya_ajustado,
        'articulo_seguimiento' : articulo.seguimiento,
        'costo_ultima_compra' : str(costo_ultima_compra),
        'detalle_modificacionestime': detalle_modificacionestime,
        'detalle_modificacionestime_salidas': detalle_modificacionestime_salidas,
        'articulo_linea' : articulo_linea
        })
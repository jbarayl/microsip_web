from django.conf.urls import patterns, url
from django.views import generic
from microsip_web.apps.inventarios import views
from microsip_web.apps.punto_de_venta import views as pv_views

urlpatterns = patterns('',
    #INVENTARIOS FISICOS
    (r'^InventariosFisicos/$', views.invetariosFisicos_View),
    # (r'^InventarioFisico/$', views.invetarioFisico_manageView),
    # (r'^InventarioFisico/(?P<id>\d+)/', views.invetarioFisico_manageView),
    
    
    (r'^articulo/(?P<id>\d+)/', views.ArticuloManageView),
    (r'^InventarioFisico_pa/$', views.create_invetarioFisico_pa_createView),
    (r'^InventarioFisico_pa/(?P<id>\d+)/', views.invetarioFisico_pa_manageView),
    (r'^inventarioFisico_mobile/(?P<id>\d+)/', views.invetarioFisico_mobile_pa_manageView),
    (r'^articulos/$', pv_views.articulos_view),
    #(r'^InventarioFisico/Delete/(?P<id>\d+)/', views.invetarioFisico_delete),
    #ENTRADAS
    # (r'^Entradas/$', views.entradas_View),
    # (r'^Entrada/$', views.entrada_manageView),
    # (r'^Entrada/(?P<id>\d+)/', views.entrada_manageView),
    # (r'^Entrada/Delete/(?P<id>\d+)/', views.entrada_delete),
    #SALIDAS
    # (r'^Salidas/$', views.salidas_View),
    # (r'^Salida/$', views.salida_manageView),
    # (r'^Salida/(?P<id>\d+)/', views.salida_manageView),
    # (r'^Salida/Delete/(?P<id>\d+)/', views.salida_delete),
    
)
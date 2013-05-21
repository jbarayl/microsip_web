from django.conf.urls import patterns, url
from django.views import generic
from microsip_web.apps.main import views

urlpatterns = patterns('',
    #Puntos
    (r'^inicializar_puntos_clientes/$', views.inicializar_puntos_clientes),
    

    #Articulos
    (r'^articulos/$', views.articulos_view),
    (r'^articulo/(?P<id>\d+)/', views.articulo_manageView),
    (r'^inicializar_tablas/$', views.inicializar_tablas),

	#Clientes
	(r'^clientes/$', views.clientes_view),
	(r'^cliente/(?P<id>\d+)/', views.cliente_manageView),

    (r'^lineas_articulos/$', views.lineas_articulos_view),
	# (r'^linea_articulos/$', views.linea_articulos_manageView),
    (r'^linea_articulos/(?P<id>\d+)/', views.linea_articulos_manageView),
    
    (r'^grupos_lineas/$', views.grupos_lineas_view),
    # (r'^grupo_lineas/$', views.grupo_lineas_manageView),
    (r'^grupo_lineas/(?P<id>\d+)/', views.grupo_lineas_manageView),
    # (r'^InventarioFisico/$', views.invetarioFisico_manageView),
    # (r'^InventarioFisico/(?P<id>\d+)/', views.invetarioFisico_manageView),
    # (r'^InventarioFisico/Delete/(?P<id>\d+)/', views.invetarioFisico_delete),
)
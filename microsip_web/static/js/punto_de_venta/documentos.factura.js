function cargar_factura_global(data){
	// alert(data.detalles);
	// var detallesj = JSON.stringify(eval("(" + data.detalles + ")"));
  if (data.message != '') 
  {
    alert(data.message);
  }
  else
    window.location = "/punto_de_venta/facturas/";
	// for (var i = 0; i <= data.length ; i++) 

}

$(function() {
  
  $("input[name*='precio_total_neto']:last").live('keydown', function(e) {
    var keyCode = e.keyCode || e.which; 
      if (keyCode == 9 || keyCode == 13) 
      {
        $(this).parent().parent().parent().find('a:last').click();
      // $("input[name*='claveArticulo']:last")[0].focus(); 
      }
  });

  $("#check_almacen").on("click", function(){
    if ($("#check_almacen").attr("checked"))
      $("#id_almacen").attr("disabled",false);
    else
      $("#id_almacen").attr("disabled",true);
  });
  $("input[id*='fecha']").datepicker({dateFormat:'dd/mm/yy',});
  $('#id_doctosIn_table tbody tr').formset({
    prefix: '{{ formset.prefix }}',
    addCssClass:'hide',
    addText:'Nuevo Articulo',
    deleteText:'',
  });
  $("input[name*='clave_articulo']:last")[0].focus();  

  $("#btn_facturaglobal").on("click", function(){
    var almacen_id = null;
    if ($("#check_almacen").attr("checked"))
      almacen_id = $("#id_almacen").val();
      if (almacen_id == '')
      {
        alert('Seleciona un almacen');
        return false
      }
      if ($("#id_cliente").val() == null)
      {
        alert('Seleciona el cliente');
        return false 
      }


    Dajaxice.microsip_web.apps.punto_de_venta.generar_factura_global( cargar_factura_global, { 
  		'fecha_inicio': $("#id_fecha_inicio").val(),
  	 	'fecha_fin': $("#id_fecha_fin").val(),
      'almacen_id': almacen_id,
      'cliente_id':$("#id_cliente").val()[0],
      'modalidad_facturacion': $("#id_modalidad_facturacion").val(),
	  });
  });
});


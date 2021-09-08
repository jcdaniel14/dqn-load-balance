$(document).ready(function () {
  $(".slider").on("input", valueUpdated);

  function valueUpdated(e) {
    let id_interface =  $(e.target).attr('id');
    let bw = $(e.target).val();
    let max_percentage = $(e.target).attr('congestion_porcentaje');
    let max = $(e.target).attr('max');
    let congestion_percentage = Math.round((bw/max)*100);

    // texto
    $("#"+id_interface+"_si" ).hide();
    $("#"+id_interface+"_no" ).hide();

    if(congestion_percentage>=max_percentage){
        $("#"+id_interface+"_si" ).show();
    }else{
        $("#"+id_interface+"_no" ).show();
    }
    //valores
    $("#"+id_interface+"_congestion_porcentaje").html(congestion_percentage+"/"+max_percentage);
    $("#"+id_interface+"_congestion_bits").html(bw+"/"+max);
  }
});

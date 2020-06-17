$(function () {
  'use strict'

  $('[data-toggle="offcanvas"]').on('click', function () {
    $('.offcanvas-collapse').toggleClass('open')
  })
  var textChart;

  var ajax = {
    call :function({url, type='GET', dataType='json', fnsuccess}={}){
      $.ajax({
        url : url,
        type : type,
        dataType: dataType,
        success : function(data) {
          fnsuccess(data);
        },
        error : function(request,error)
        {
          bootbox.alert("Request Error: " + request.responseText);
        },
        beforeSend: function( xhr ) {
          $(".loader").show();          
        }
      }).always(function() {
        $(".loader").hide();
      });
    }
  }

  function getArchivos(){
    $("#archivos tbody").html("");
    ajax.call({
      url:'/archivos',
      fnsuccess: (data) => {        
        $.each(data, function( key, value ) {
          $("#archivos tbody").append('<tr><th scope="row">'+(key+1)+'</th><td>'+value.archivo+'</td><td>'+value.tamano+'</td>'+
          '<td><a href="/archivo/'+value.archivo+'" class="btn btn-link" role="button" aria-pressed="true"><i class="fas fa-download"></i></a></td></tr>');
        });          
    }});
  }

  function getConsignas(transformador,id_consignacion){
    $("#consignas tbody").html('');
    $("#jsonCons").html('');
    ajax.call({
      url : '/consignaciones?id_consignacion=' + id_consignacion.trim()+'&transformador=' + transformador,      
      fnsuccess : function(data) {
        if (data.hasOwnProperty('error') ) {
          bootbox.alert('Error evalundo Consignacion: '+ data.error);
        }else{
          $("#jsonCons").html(JSON.stringify(data.data[0], undefined, 2));
          $.each(data.model, function( key, value ) {
            $("#consignas tbody").append('<tr><th scope="row">Clase '+value.clase+'</th><td>'+(parseFloat(value.valor)*100).toFixed(2)+'</td></tr>');
          });   
        }       
      }
    });
  }

  function color(opacity=0.3){
    var r = Math.floor(Math.random()*255);
    var g = Math.floor(Math.random()*255);
    var b = Math.floor(Math.random()*255);

    return [ "rgba("+r+","+g+","+b+","+ opacity +")",
             "rgba("+r+","+g+","+b+","+ (opacity + 0.5) +")"];
 }

  function getWords(tipo, count, num){    
    $("#jsonText").html("");
    ajax.call({
      url : '/texting?tipo=' + tipo.trim() + '&count=' + count + "&numero=" + num,
      fnsuccess : function(data) {
        if (data.hasOwnProperty('error') ) {
          bootbox.alert('Error en Bitacoras: '+ data.error);
        }else{       
          $("#jsonText").html(JSON.stringify(data, undefined, 2));   
          if (textChart) {
            textChart.destroy();
          }
          var colors = [];
          var hoverColors=[];
          for (let index = 0; index < data.x.length; index++) {
            var c = color();
            colors.push(c[0]);
            hoverColors.push(c[1]);
          }
          var ctx = $('#textChart');
          textChart = new Chart(ctx, {
            type: 'horizontalBar',
            data: {
                labels: data.x,
                datasets: [{
                    label: 'Frecuencia',
                    data: data.y,
                    borderWidth: 1,
                    backgroundColor: colors,
                    hoverBackgroundColor: hoverColors           
                }]
            },
            options: {
                scales: {
                    yAxes: [{
                        ticks: {
                            beginAtZero: true
                        }
                    }]
                }
            }
          });
        }       
      }
    });
  }  

  $(document).ready(function(){    
    $('#nav-tab a[href="#nav-arch"]').on('click', function (e) {
      getArchivos();
    })
    $("#frmCons").submit(function( event ) {
      var tra = $("#txtTrans").val() || '';
      var con = $("input#txtCons").val();
      if( tra == '' && con == ''){
          bootbox.alert("Error: Ingrese al menos 1 parametro");
      }else if( tra != '' && con != ''){
        bootbox.alert("Error: Ingrese solo 1 parametro de busuqeda");
      }else{
        getConsignas(tra, con);
      }
      event.preventDefault();
    });

    $( "#frmText" ).submit(function( event ) {      
      getWords($('input[name=txtTipoWords]:checked', '#frmText').val(), parseInt($("input#txtResWords").val()), parseInt($("input#txtNumWords").val()))
      event.preventDefault();      
    });

    // Api Transformador
    $('#txtTrans').select2({
      language: "es",
      placeholder: "Transformador",
      allowClear: true,
      minimumInputLength: 2,
      ajax: {
        delay: 250,
        url: function (params) {
          return '/transformador?search=' + (params.term ? params.term.toUpperCase() : params.term);
        },
        dataType: 'json',
        processResults: function (data) {
          var resp = []
          $.each(data, function(i, val){
            resp.push({'id': val, 'text': val})
          })
          return {
            results: resp
          };
        }
      }
    });
  });
})

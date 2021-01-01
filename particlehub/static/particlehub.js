$(document).ready(function(){
    update_device_table();
    $("#start-all-logs").on("click", function(){
        $.get("/start-all-logs", function(data, status){

          });
    });
    $("#stop-all-logs").on("click", function(){
        $.get("/stop-all-logs", function(data, status){

          });
    });

});

function update_device_table() {
  $.get("/get-devices", function(data, status){
    $('#device-list').html(data);
  });
}

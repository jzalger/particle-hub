$(document).ready(function(){
    update_device_table();
});

function update_device_table() {
  $.get("/get-devices", function(data, status){
    $('#device-list').html(data);
  });
}
$(document).ready(function($){
    update_device_table();

    $("#add-unmanaged-devices").on("click", function(){
        $.get("/add-unmanaged-devices", function(data, status){
            update_device_table();
        });
    });

    $("#start-logging-all").on("click", function(){
        $.get("/start-logging-all", function(data, status){
            update_device_table();
          });
    });
    $("#stop-logging-all").on("click", function(){
        $.get("/stop-logging-all", function(data, status){
             update_device_table();
          });
    });
});

function update_device_table() {
  $.get("/get-devices", function(data, status){
    $('#device-list').html(data);
    // Attach callbacks to the new rows.
    $("tbody tr").click(function () {
        let device_id = $(this).attr('data-id');
        $.get("/get-device-info", {"device_id": device_id}, function(data, status){
            $("#device-details").html(data);
        });
    });
  });
}


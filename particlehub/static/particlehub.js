$(document).ready(function(){
    update_device_table();

    // TODO: Manage use device checkmark
    // TODO: Manage device detail selection and display

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
  });
}


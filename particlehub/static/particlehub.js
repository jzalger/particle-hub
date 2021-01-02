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

    // FIXME: This code needs to be abstracted
    // Attach detail info callbacks to the new rows.
    $(".device-row").click(function () {
        let device_id = $(this).attr('data-id');
        $.get("/get-device-info", {"id": device_id}, function(data, status){
            $("#device-details").html(data);

            // Attach tagging callbacks to the variable rows
            $(".tag-row").click(function (){
                let device_id = $(this).attr('data-id');
                let tag = $(this).attr('data-tag');
                $.get("/add-tag", {"id": device_id, "tag": tag}, function(data, status){
                    let row = $("button[data-tag='" + data.tag +"']");
                    $(row).append('<i class="fas fa-tag text-info"></i>');
                });
            });
        });
    });
    // Attach callbacks for add/remove
    $(".remove-device-btn").click(function(){
        let device_id = $(this).attr('data-id');
        $.get("/remove-device", {"id": device_id}, function(data, status){
            update_device_table();
        });
    });
    $(".add-device-btn").click(function(){
        let device_id = $(this).attr('data-id');
        let log_source = $(this).attr('data-log-source');
        $.get("/add-device", {"id": device_id, "log_source": log_source}, function(data, status){
            update_device_table();
        });
    });
  });
}


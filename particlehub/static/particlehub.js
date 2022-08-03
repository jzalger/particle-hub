$(document).ready(function($){
    $.ajaxSetup({
            headers:
            { 'X-CSRF-TOKEN': $('meta[name="csrf-token"]').attr('content') }
        });
    update_device_table();
});
function update_device_table() {
  $.get("/get-devices", function(data, status){
    $('#device-list').html(data);

    // Attach detail info callbacks to the new rows.
    $(".device-row").click(function () {
        let device_id = $(this).attr('data-id');
        $.get("/get-device-info", {"id": device_id}, function(_data, _status){
            $("#device-details").html(_data);
            attach_tagging_callbacks();
        });
    });
    // Attach callbacks for add/remove
    $(".remove-device-btn").click(function(){
        let device_id = $(this).attr('data-id');
        $.post("/remove-device", {"id": device_id}, function(_data, _status){
            update_device_table();
        });
    });
    $(".add-device-btn").click(function(){
        let device_id = $(this).attr('data-id');
        let log_source = $(this).attr('data-log-source');
        $.post("/add-device", {"id": device_id}, function(_data, _status){
            update_device_table();
        });
    });
  });
}
function attach_tagging_callbacks(){
    // Attach tagging callbacks to the variable rows
    $(".tag-row").click(function (){
        let device_id = $(this).attr('data-id');
        let tag = $(this).attr('data-tag');
        let row = $("button[data-tag='" + tag +"']");
        if ($(row).attr('data-tagged') == "false") {
            $.post("/add-tag", {"id": device_id, "tag": tag}, function(data, status){
                if (data.status == "success") {
                    $(row).attr('data-tagged','true');
                    $(row).append('<em class="fa fa-tag text-secondary"></em>');
                } else {
                    $(row).append('<em class="fa fa-circle-exclamation text-danger"></em>');
                }
            });
        } else {
            $.post("/remove-tag", {"id": device_id, "tag": tag}, function(data, status){
                if (data.status == "success") {
                    $(row).attr('data-tagged', 'false');
                    $(row).find('em').remove();
                } else {
                    $(row).append('<em class="fa fa-circle-exclamation text-danger"></em>');
                }
            });
        }
    });
}

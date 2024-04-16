
function triggerAttendanceProcessedEvent() {
    $(document).trigger('attendanceProcessed');
}

function loadUpdatedAttendanceList() {
    console.log("test updated attendance list...");
    $.get('/path/to/render_attendance_list/', function(updatedList) {
        console.log("Test Received updated attendance list:", updatedList);
        $('#AttendanceListContainer').html(updatedList);
    });
}

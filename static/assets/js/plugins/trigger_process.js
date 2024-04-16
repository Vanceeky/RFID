
    $(document).ready(function() {
        // Simulate a button click event
        $('#testButton').on('click', function() {
            // Trigger a custom event when the button is clicked
            console.log('test')
            $(document).trigger('attendanceProcessed');
        });
    });

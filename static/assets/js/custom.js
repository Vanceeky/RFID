$(document).ready(function() {
    $('#rfid_input').on('change', function() {
        var rfid_number = $(this).val();

        // Check if the input is long enough to be a valid RFID card number
        if (rfid_number.length >= 10) {
            // Get the CSRF token
            var csrf_token = $("input[name=csrfmiddlewaretoken]").val();

            // Send the RFID number and CSRF token to your view for processing
            $.ajax({
                type: 'POST',
                url: '/process_attendance/',  // Update the URL to match your Django URL configuration
                data: {
                    csrfmiddlewaretoken: csrf_token,
                    rfid_number: rfid_number
                },
                success: function(response) {
                    // Clear the input field
                    $('#rfid_input').val('');
                
                    // Use SweetAlert to display the response message without an OK button
                    Swal.fire({
                        icon: response.icon,
                        text: response.message,
                        showConfirmButton: false,
                        timer: 2000,
                        timerProgressBar: true
                    });
                
                    // Load the updated attendance list on the 'attendance' page
                    //loadUpdatedAttendanceList();
                                        // Trigger a custom event after successful processing
                    $(document).trigger('attendanceProcessed');
                },
                error: function(xhr, status, error) {
                    // Clear the input field
                    $('#rfid_input').val('');

                    // Log the error details to the console
                    console.error(xhr.responseText);

                    // Use SweetAlert to display an error message without an OK button
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'An error occurred while processing attendance',
                        showConfirmButton: false, // Remove the OK button
                        timer: 2000, // Automatically close the alert after 2 seconds
                        timerProgressBar: true // Display a progress bar during the timer
                    });
                }
            });
        }
    });

});

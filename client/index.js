
const client_io = io({});

$(document).on("ready", function () {

    $("#send-btn").on("click", function () {

        let message = $("#message").val();
        if (message == "") return;
        
        // read message content
        data = {
            message: message
        };

        // send data to server
        client_io.emit("message", data);
        console.log(data)

        // clear message box
        $("#message").val("")
        
    });

});

client_io.on("update", (data) => {
    console.log(data)
    $("#messages").empty()
    data.forEach(message => {
        $("#messages").append(`<div>${message}</div>`);
    });
});

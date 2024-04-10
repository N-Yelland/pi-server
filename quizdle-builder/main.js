
// This is JS for quizdle-builder

console.log("Test message")

const client_io = io({});

var grid_width = 15
var grid_height = 15

function build_grid() {

    for (let i = 0; i < grid_height; i++) {
        var row = $("<div></div>").appendTo(".grid");
        row.addClass("row");
        
        for (let j = 0; j < grid_width; j++) {
            var cell = $("<div></div>").appendTo(row);
            cell.addClass("cell");
        }
    }
}

$(document).on("ready", function () {
    build_grid();
});

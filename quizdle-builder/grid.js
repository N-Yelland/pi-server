
$(".build-btn").on("click", async function () {
    console.log("Starting grid-building process...");
    
    // Tidy up possible interruptions...
    $(this).removeClass("spin");
    $(".error-msg").fadeOut();

    let words = [];
    $(".answer").each(function () {
        let answer = $(this).val();
        if (answer) {
            words.push(answer);
        } else {
            // flash empty answers
            $(this).addClass("flash");
            let element = $(this);
            setTimeout(function() {element.removeClass("flash")}, 1000);
        }
    });

    if (words.length < 5) {
        console.log("You must provide all the answers!");
        return;
    }

    $(this).addClass("spin");

    const data = await get_crossword_grids(words);

    console.log("Recieved data: ", data);

    // An error has returned instead of grid data; we should report it.
    var error;
    if (typeof data == "string") {
        error = data;
    } else if (data.errors) {
        error = data.errors.join(", ");
    }

    if (error) {
        console.log("there was an error...");
        $(this).removeClass("spin");

        $(".error-msg .text").html(error);
        $(".error-msg").fadeIn(500);
        setTimeout(function () {
            $(".error-msg").fadeOut();
        }, 5000);
        
        return;
    }

    // TODO: handle the presence of warnings

    // display grids; just the first one for now

    localStorage["grids"] = JSON.stringify(data.grids);
    localStorage["grid_index"] = 0;

    const grid = data.grids[0];

    display_grid(grid);

    // Activate the other buttons
    $("#rebuild-btn").removeClass("inactive");
    $("#next-btn").toggleClass("inactive", data.grids.length == 1)

});


function display_grid (grid) {
    const n = grid.grid_size;

    // Build an n x n grid
    create_grid(n);

    $(".build-btn").removeClass("spin");
    $(".build-btn").hide();

    // ... and fill it with the right words.

    write_words_to_grid(grid.clues);
    /*
    for (clue of grid.clues) {
        $(".clue-info").append(`${clue.word}\t${clue.row},${clue.col},${clue.direction}<br>`);
    }
    */
}


function rebuild_grid (increment=null) {
    // Removes grid...
    $(".grid .row").remove();
    $(".clue-info").empty();

    if (!increment) {
        // Case 1: Full rebuild
        // Displays big button again...
        $(".big-btn").show();

        // ...and click it!
        $(".big-btn").click();
    } else {
        // Case 2: build another pre-computed grid...
        const grids = JSON.parse(localStorage["grids"]);
        const x = parseInt(localStorage["grid_index"]) + (increment == "next" ? 1 : -1);
        const grid = grids[x];
        const num_grids = grids.length;

        display_grid(grid);
        
        // Update index
        localStorage["grid_index"] = x;

        return {
            "new_index": x,
            "num_grids": num_grids
        };
    }
}

$("#prev-btn").on("click", function () {
    const grid_info = rebuild_grid("prev");
    $("#prev-btn").toggleClass("inactive", grid_info.new_index == 0);
    $("#next-btn").toggleClass("inactive", grid_info.new_index == grid_info.num_grids - 1);
});

$("#next-btn").on("click", function () {
    const grid_info = rebuild_grid("next");
    $("#prev-btn").toggleClass("inactive", grid_info.new_index == 0);
    $("#next-btn").toggleClass("inactive", grid_info.new_index == grid_info.num_grids - 1);
});

$("#rebuild-btn").on("click", function () {
    $(".buttons .button").addClass("inactive");
    rebuild_grid();
})


function create_grid(n) {

    for (let i = 0; i < n; i++) {
        var row = $("<div></div>").appendTo(".grid");
        row.addClass("row");
        
        for (let j = 0; j < n; j++) {
            var cell = $("<div></div>").appendTo(row);
            cell.addClass("cell");
        }
    }
}


function write_char_to_grid(char, row, col) {
    let cell = $(".grid").children(".row").eq(row).children(".cell").eq(col);
    if (cell.html() && cell.html() != char) {
        console.log(`Conflict (overwritten) in cell (${row}, ${col})`);
    }
    cell.html(char);
}


function write_words_to_grid(words) {
    // 'words' is a JSON object with schema [{word: str, row: int, col: int, direction: str}, ...]
    for (const word of words) {
        for (let i = 0; i < word.word.length; i++) {
            write_char_to_grid(
                word.word[i],
                word.row + i * (word.direction == "D"),
                word.col + i * (word.direction == "A")
            );
        }
    }
}

$(document).on("ready", function () {
    const grids = JSON.parse(localStorage.getItem("grids"));
    const x = parseInt(localStorage.getItem("grid_index"))

    // we assume grids being set implies x is set.
    if (grids) {
        display_grid(grids[x])
        $("#prev-btn").toggleClass("inactive", x == 0);
        $("#next-btn").toggleClass("inactive", x == grids.length);
        $("#rebuild-btn").removeClass("inactive");
    }
})


// Calendar things

const months = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
const days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

const today = new Date();
const week = [];

for (let i = 0; i < 7; i++) {
    let day = new Date();
    day.setDate(day.getDate() + i);
    week.push(day);
}

for (let day of week) {
    let day_blob = $("<div></div>").appendTo("#calendar");
    day_blob.addClass("day-blob button");

    day_blob.html(`
        <div class="date-text small">${days[day.getDay()]}</div>
        <div class="date-text big">${day.getDate().toString()}</div>
        <div class="date-text small">${months[day.getMonth()]}</div>`);
    
    day_blob.attr("id", day.toISOString().substring(0,10))
}

$(document).on("ready", async function () {

    $(".day-blob").on("click", function () {
        $("#upload-btn").removeClass("inactive");
        $(".day-blob").removeClass("selected");
        $(this).addClass("selected");
    })

    const next_weeks_quizdles_status = await get_next_weeks_quizdles_status();
    
    for (let date of next_weeks_quizdles_status) {
        $(`#${date}`).addClass("done");
    }

})

$("#upload-btn").on("click", function () {
    $(".pop-up-box").hide();
    $("#upload-confirmation").show();
    
    $("#pop-up").fadeIn();
})

$(".close-btn").on("click", function () {
    $("#pop-up").fadeOut();
})

function show_alert(msg) {
    $(".pop-up-box").hide();
    $("#alert").show();
    $("#alert #alert-msg").html(msg);
}
// TODO: add "Clear All" button

async function get_crossword_grids(words) {
    // Sends a list of string (words) to the /generate endpoint to obtain a complete grid.
    console.log("Sending request to generate grid for " + words);
    const result = await $.ajax({
        url: "https://pi.nicyelland.com/quizdle-builder/generate",
        data: {
            words: words.join(","),
            json: "true"
        }
    });

    return result;
}

async function get_next_weeks_quizdles_status(date = new Date()) {

    var date_string = date.toISOString().substring(0,10);
    console.log("Requesting the status of the next 7 days of Quizdles starting from " + date_string); 

    const result = await $.ajax({
        url: "https://pi.nicyelland.com/quizdle-builder/query",
        method: "POST",
        data: {
            query_type: "get_week_status",
            start_date: date_string
        }
    });

    if (result.error) {
        console.log("Error: " + result.error);
        return;
    }

    return result.data;
} 

async function upload_current_quizdle() {
    // Read various data from HTML to form quizdle json

    let quizdle = new Object;

    $(".question").each(function () {
        const key = $(this).attr("id");
        quizdle[key] = $(this).val();
    })

    quizdle["date"] = $(".day-blob.selected").attr("id");

    const grids = JSON.parse(localStorage.getItem("grids"));
    const grid_index = parseInt(localStorage.getItem("grid_index"));
    
    let answer_positions = grids[grid_index].clues;

    $(".answer").each(function () {
        const key = $(this).attr("id");
        const i = parseInt(key.match(/\d+$/)[0]);

        const answer = $(this).val().toUpperCase();
        
        quizdle[key] = answer;

        let j = 0;
        while (answer_positions[j].word != answer) {
            j++;
            if (j >= answer_positions.length) {
                break;
            }
        }

        const position = answer_positions.splice(j, 1)[0];

        quizdle[`rowCol${i}`] = `${position.row},${position.col},${position.direction}`;

    })

    console.log(JSON.stringify(quizdle));

    const result = await $.ajax({
        url: "https://pi.nicyelland.com/quizdle-builder/query",
        method: "POST",
        data: {
            query_type: "write_new_quizdle",
            quizdle: JSON.stringify(quizdle),
            password: $("#password").val()
        }
    });

    $("#password").val("");

    console.log(result);

    if (result.error) {
        show_alert(result.error);
    }

    if (result.data.success) {
        show_alert("Quizdle Published!");
    }
}

/*   
$(".get-todays-quizdle-btn").on("click", function() {

    let password = prompt("This action requires a password.")

    $.ajax({
        url: "https://pi.nicyelland.com/quizdle-builder/read",
        method: "POST",
        data: {
            password: password,
            today: "true"
        },
        success: function (response) {
            // console.log(response)
            clues = response.clues

            write_words_to_grid(clues)

            for (var i = 0; i < 5; i++) {
                $(".question").eq(i).val(clues[i].clue)
                $(".answer").eq(i).val(clues[i].word)
            }
        },
        statusCode: {
            401: function() {alert("Authentication failed.");}
        }
    });
});
*/
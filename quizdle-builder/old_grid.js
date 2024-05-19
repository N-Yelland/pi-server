

function get_pos(cell) {
    let x = cell.index();
    let y = cell.parent().index();
    return {x: x, y: y};
}

function select_cell(pos){
    let row = $(".grid").children()[pos.y];
    let cell = $(row).children()[pos.x];
    $(cell).click();
    return $(cell);
}

function read_cell(pos) {
    let row = $(".grid").children()[pos.y];
    let cell = $(row).children()[pos.x];
    return $(cell).html();
}

function parse_grid() {
    let row_words = new Array();
    let col_words = new Array();

    let rows = $(".grid").children().toArray();
    for (let i = 0; i < rows.length; i++) {
        row_words.push('');
        let cells = $(rows[i]).children().toArray();
        for (let j = 0; j < cells.length; j ++) {
            if (i == 0) col_words.push('');
            let cell_contents = $(cells[j]).html() || " ";
            row_words[i] += cell_contents;
            col_words[j] += cell_contents;
        }
    }

    let words = new Array();

    // extract words from rows...
    row_words.forEach((string, index) => {
        let matches = [...string.matchAll(/\w{2,}/g)]
        for (const match of matches) {
            words.push({
                word: match[0],
                pos: `${index},${match.index},A`
            });
        }
    });

    // extract words from columns...
    col_words.forEach((string, index) => {
        let matches = [...string.matchAll(/\w{2,}/g)]
        for (const match of matches) {
            words.push({
                word: match[0],
                pos: `${match.index},${index},D`
            });
        }
    });

    return words;
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

function display_clues(clue_data) {

    $(".clue").remove()

    for (const clue of clue_data) {
        var clue_div = $("<div></div>").appendTo(".clues");
        clue_div.addClass("clue");
        clue_div.html(`${clue.word} - ${clue.pos}`);
    }
}

$(document).on("ready", function () {

    let direction = "across"

    $(".grid .cell").on("click", function () {
        if ($(this).hasClass("selected")) {
            direction = (direction == "across") ? "down" : "across";
        }
        $(".cell").removeClass("selected");
        $(this).addClass("selected");
        if (direction == "down") {
            $(this).addClass("down");
        } else {
            $(this).removeClass("down");
        }
        $(this).focus();
    });

    $(document).on("click", function (e) {
        if (!$(e.target).parents(".grid").length) {
            $(".cell.selected").removeClass("selected");
        }
    });

    $(document).on("keydown", function(e) {

        if (!$(".cell.selected").length) {
            return;
        }

        let text_changed = false;

        if (e.key.match(/^[a-z]$/i)) {
            let current_cell = $(".cell.selected");
            current_cell.html(e.key.toUpperCase());
            text_changed = true;
            let pos = get_pos(current_cell);
            
            (direction == "across") ? pos.x++ : pos.y++;
            select_cell(pos);
        }

        else if (e.key == "Backspace") {
            let current_cell = $(".cell.selected");
            if (current_cell.html()) { current_cell.html(""); }
            else {
                let pos = get_pos(current_cell);
                (direction == "across") ? pos.x-- : pos.y--;;
                let new_cell = select_cell(pos);
                new_cell.html("");
                text_changed = true;
            }
        }

        // Use arrow keys to move cursor
        else if (e.key.match(/^Arrow/)) {
            let current_cell = $(".cell.selected");
            let pos = get_pos(current_cell);
            switch (e.key) {
                case "ArrowUp": pos.y --; break;
                case "ArrowDown": pos.y ++; break;
                case "ArrowLeft": pos.x --; break;
                case "ArrowRight": pos.x ++; break;
            }
            select_cell(pos);
        }

        // Press [space] to change direction
        else if (e.key == " ") {
            e.preventDefault();
            let current_cell = $(".cell.selected");
            let pos = get_pos(current_cell);
            select_cell(pos);
        }

        else if (e.key == "Delete") {
            let current_cell = $(".cell.selected");
            current_cell.html("");
            text_changed = true;
        }

        else {
            console.log(e.key);
        }

        // Update the clues...
        if (text_changed) {
            clue_data = parse_grid();
            // display_clues(clue_data);
        }

    });

    $(".answer").on("input", function() {
        this.value = this.value.toUpperCase();
    })
    
});


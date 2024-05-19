"""
CROSSWORD.PY

Problem: Given a list of words, find an assignment of coordinates and directions such that the resulting crossword
is 'coherent', and ideally maximises the number of intersections and minimises the convex hull.

"""

from typing import List, Tuple, Literal, Generator, Optional, Set, Dict, Union

import os

from itertools import combinations

from timeout_decorator import timeout

        
Direction = Literal["A", "D"]


class Word:
    ACROSS: Direction = "A"
    DOWN: Direction = "D"

    def __init__(self, word: str, x: int = 0, y: int = 0, direction: Direction = "A"):
        self.word = word.upper()    # TODO: more input parsing e.g. for spaces, punctuation.
        self.length = len(word)
        # self.chars = set(word)

        self.x, self.y = x, y
        if direction.upper().startswith(Word.ACROSS):
            self.direction = Word.ACROSS
        elif direction.upper().startswith(Word.DOWN):
            self.direction = Word.DOWN
        else:
            raise ValueError(f"Cannot recognise value '{direction}' as a direction")

    def __getitem__(self, index) -> str:
        if 0 <= index < self.length:
            return self.word[index]
        return ""

    def __repr__(self) -> str:
        return self.word

    def __eq__(self, other: 'Word') -> bool:
        return (self.word == other.word
                and self.x == other.x
                and self.y == other.y
                and self.direction == other.direction)

    def __hash__(self) -> int:
        return hash((self.word, self.x, self.y, self.direction))

    def shifted(self, x: int, y: int) -> 'Word':
        return Word(self.word, self.x + x, self.y + y, self.direction)

    def find_intersections(self, new_word: str) -> List[Tuple[int, int]]:
        """
        Returns a list of (x, y) tuples corresponding to positions a new word can be located to intersect with this word
        correctly.
        :param new_word: Content of a new word to intersect with this word.
        :return: List of (x, y) tuples corresponding to potential word positions with valid intersections.
        """
        positions: List[Tuple[int, int]] = []

        for offset, char in enumerate(self.word):
            for new_offset, new_char in enumerate(new_word):
                if char == new_char:
                    x_offset, y_offset = 0, 0

                    if self.direction == Word.ACROSS:
                        x_offset, y_offset = offset, -new_offset
                    elif self.direction == Word.DOWN:
                        x_offset, y_offset = -new_offset, offset

                    positions.append((self.x + x_offset, self.y + y_offset))

        return positions


class Crossword:

    def __init__(self, words: List[Word]):
        # Words are canonically sorted lexicographically. Only the words' x and y values should be considered mutable.
        self.words = sorted(words, key=lambda w: w.word)
        # Ensure top-left of bounding box is at (0,0).
        self.align()

    def is_valid(self) -> bool:
        """
        Checks that words are pairwise 'valid', where 'valid' is defined by the Crossword.valid_pair(...) method.
        :return: True if crossword is 'valid', False otherwise.
        """
        for w1, w2 in combinations(self.words, 2):
            if not self.valid_pair(w1, w2):
                return False
        return True

    def add_word(self, word: Word) -> 'Crossword':
        return Crossword(self.words + [word])

    def valid_pair(self, w1: Word, w2: Word) -> bool:
        """
        Checks that self and other (both instances of Word) are 'valid', namely:
         - if they are in the same column/row, they don't overlap.
         - if they are otherwise parallel, they don't 'touch', or if they do, the touching letters are contained in a
           perpendicular words.
         - if they are perpendicular, and they intersect, the intersecting letters match.
        :param w1: First word
        :param w2: Second word
        :return: True if the words are 'valid', False if otherwise.
        """

        # Case 1: Words are parallel
        if w1.direction == w2.direction:

            # Case 1a: Words are in the same row/column; check they don't overlap or touch end-to-end.
            if w1.direction == Word.ACROSS and w1.y == w2.y:
                return min(w1.x + w1.length, w2.x + w2.length) < max(w1.x, w2.x) + 1
            if w1.direction == Word.DOWN and w1.x == w2.x:
                return min(w1.y + w1.length, w2.y + w2.length) < max(w1.y, w2.y) + 1

            # Case 1b: Words are in adjacent rows/columns; check they don't touch side-to-side
            if w1.direction == Word.ACROSS and abs(w1.y - w2.y) == 1:
                # If they do touch, then all touching cells should lie in words going the other direction.
                for i in range(max(w1.x, w2.x), min(w1.x + w1.length, w2.x + w2.length)):
                    if not any(w.y <= min(w1.y, w2.y) and w.y + w.length > max(w1.y, w2.y)
                               for w in self.words if w.direction == Word.DOWN and w.x == i):
                        return False
                return True
            if w1.direction == Word.DOWN and abs(w1.x - w2.x) == 1:
                # Similarly with directions reversed.
                for i in range(max(w1.y, w2.y), min(w1.y + w1.length, w2.y + w2.length)):
                    if not any(w.x <= min(w1.x, w2.x) and w.x + w.length > max(w1.x, w2.x)
                               for w in self.words if w.direction == Word.ACROSS and w.y == i):
                        return False
                return True

            # Case 1c: Words are far enough apart to not interact.
            return True

        # Case 2: Words are perpendicular; check their intersection point is consistent.
        if w1.direction == Word.ACROSS:
            a_word, d_word = w1, w2
        else:
            a_word, d_word = w2, w1
        return a_word[d_word.x - a_word.x] == d_word[a_word.y - d_word.y]

    def align(self, x: int = 0, y: int =0) -> None:
        """
        Shifts positions of words so that the top-left corner of the bounding box is aligned with (x, y).
        (Defaults to (0,0))
        :return: None
        """
        x_shift = min(w.x for w in self.words) - x
        y_shift = min(w.y for w in self.words) - y
        self.words = [w.shifted(-x_shift, -y_shift) for w in self.words]

    def get_bounding_box(self) -> Tuple[int, int]:
        # Determine grid dimensions
        grid_width = max([w.x + w.length for w in self.words if w.direction == Word.ACROSS] or [1])
        grid_height = max([w.y + w.length for w in self.words if w.direction == Word.DOWN] or [1])

        return grid_width, grid_height

    def get_size(self) -> int:
        width, height = self.get_bounding_box()
        return width * height

    def display(self) -> None:
        return self.display_string()
    
    def display_string(self) -> str:
        # Check crossword is valid - can't sensibly display otherwise.
        assert self.is_valid()
        self.align()

        # Determine grid dimensions
        grid_width = max([w.x + w.length for w in self.words if w.direction == Word.ACROSS] or [1])
        grid_height = max([w.y + w.length for w in self.words if w.direction == Word.DOWN] or [1])

        # Initialise empty grid and insert words
        grid = [["   " for _ in range(grid_width)] for _ in range(grid_height)]
        for word in self.words:
            if word.direction == Word.ACROSS:
                for i, char in enumerate(word.word):
                    grid[word.y][word.x + i] = f" {char} "
            else:
                for i, char in enumerate(word.word):
                    grid[word.y + i][word.x] = f" {char} "

        # Display grid
        output = "\n".join("".join(grid[y][x] for x in range(grid_width)) for y in range(grid_height))
        output += f"\n({grid_width} x {grid_height}) ({self.count_crossings()} crossings)"

        return output

    def count_crossings(self) -> int:
        crossings = 0
        for w1, w2 in combinations(self.words, 2):
            if w1.direction != w2.direction:
                a_word, d_word = (w1, w2) if w1.direction == Word.ACROSS else (w2, w1)
                if d_word.y <= a_word.y < d_word.y + d_word.length:
                    crossings += 1
        return crossings

    def list_clues_string(self) -> str:
        output = []
        for i, word in enumerate(sorted(self.words, key=lambda w: (w.y, w.x, w.direction))):
            output.append(f"{i+1:>2}. {word.word:<15} ({word.y}, {word.x}, {word.direction})")
        return "\n".join(output)

    def list_clues(self) -> List[Dict[str, Union[str, int]]]:
        output = []
        for word in sorted(self.words, key=lambda w: (w.y, w.x, w.direction)):
            output.append({
                "word": word.word,
                "row": word.y,
                "col": word.x,
                "direction": word.direction
            })
        return output
    
    def centre(self) -> None:
        """
        Centres the grid in its own "bounding square".
        """
        w, h = self.get_bounding_box()
        adjustment = int(abs(w-h)/2)
        if w > h:
            self.align(0, adjustment)
        else:
            self.align(adjustment, 0)
    
    def get_aspect_ratio(self) -> float:
        w, h = self.get_bounding_box()
        return max(w, h) / min(w, h)

    def __eq__(self, other):
        return self.words == other.words

    def __hash__(self):
        return hash(tuple(self.words))

    def __repr__(self):
        return f"Crossword({self.words})"


class NoValidFill(Exception):
    """Exception to raise in the crossword construction algorithm."""


def fill_crossword(crossword: Crossword, words_to_add: List[str]) -> Crossword:
    """
    Given a (non-empty) crossword and a list of words, will return a connected crossword with the words added, or
    raise a NoValidFill error if there is no valid arrangement of the words that keeps the crossword connected.
    :param crossword: Crossword to be filled.
    :param words_to_add: list of words (as strings) to be added to the crossword.
    :return: Crossword with words added.
    """
    if not words_to_add:
        return crossword

    for current_word in crossword.words:
        new_direction = Word.DOWN if current_word.direction == Word.ACROSS else Word.ACROSS
        for new_word_str in words_to_add:
            positions = current_word.find_intersections(new_word_str)
            for x, y in positions:
                new_word = Word(new_word_str, x, y, new_direction)
                new_crossword = crossword.add_word(new_word)
                if new_crossword.is_valid():
                    new_wordlist = words_to_add.copy()
                    new_wordlist.remove(new_word_str)
                    try:
                        return fill_crossword(new_crossword, new_wordlist)
                    except NoValidFill:
                        pass
    else:
        raise NoValidFill


def generate_crosswords(words_to_add: List[str],
                        crossword: Optional[Crossword] = None) -> Generator[Crossword, None, None]:
    """
    Iterator that yields all* valid connected crosswords built using all the words from words_to_add. Optional crossword
    argument to provide a partial crossword structure with some remaining words to be added.

    *The recursive nature of the definition with no look-ahead means that certain structures (e.g. 'pinwheels' where a
    2x2 section of the grid is contained in four words overlapping) would require invalid grids at intermediate stages.

    TODO: add levels of 'strictness' that allow e.g. pinwheels or even no adjacent and parallel clues.

    :param words_to_add:
    :param crossword:
    :return:
    """
    # If no words are left to add, we are done.
    if not words_to_add:
        crossword.align()
        yield crossword
        return

    # If crossword is empty, exhaust over possible initial words.
    if crossword is None:
        for word in words_to_add:
            init_wordlist = words_to_add.copy()
            init_wordlist.remove(word)

            init_word = Word(word)
            init_crossword = Crossword([init_word])

            yield from generate_crosswords(init_wordlist, init_crossword)
            return

    for current_word in crossword.words:
        new_direction = Word.DOWN if current_word.direction == Word.ACROSS else Word.ACROSS
        for new_word_str in words_to_add:
            positions = current_word.find_intersections(new_word_str)
            for x, y in positions:
                new_word = Word(new_word_str, x, y, new_direction)
                new_crossword = crossword.add_word(new_word)
                if len(words_to_add) > 1 or new_crossword.is_valid():
                    new_wordlist = words_to_add.copy()
                    new_wordlist.remove(new_word_str)
                    yield from generate_crosswords(new_wordlist, new_crossword)


ITERATION_LIMIT = 10000
TIME_LIMIT = 10
MAX_GRIDS_RETURNED = 20

def main(wordlist: List[str], json: bool) -> str:
    os.nice(10)
    output = []
    json_data = {"errors": [], "warnings": [], "grids": []}

    crosswords: Set[Crossword] = set()
    i = 0
    for xw in generate_crosswords(wordlist):
        i += 1
        if i > ITERATION_LIMIT:
            output.append("Warning! Iteration limit reached!")
            json_data["warnings"].append("iteration_limit_reached")
            break
        if xw not in crosswords:
            crosswords.add(xw)

    output.append(f"{len(crosswords)} unique grids found...\n")
    json_data["num_grids"] = len(crosswords)

    if len(crosswords) == 0:
        output.append(f"There are no connected crosswords using the words {wordlist}.")
        json_data["errors"].append("no_grids_found")

    else:

        # Maximise number of crossings, then minimise size, and minimise aspect ratio...
        crosswords = sorted(crosswords,
                            key=lambda xw: (-xw.count_crossings(), xw.get_size(), xw.get_aspect_ratio()))
        
        output.append("Best grid(s):")
        best_grids = crosswords[:MAX_GRIDS_RETURNED]
        for xw in best_grids:
            output.append(xw.display_string())
            output.append(xw.list_clues_string())
            output.append("")

            xw.centre()

            json_data["grids"].append({
                "clues": xw.list_clues(),
                "grid_size": max(xw.get_bounding_box())
            })

    if json:
        return json_data
    return "\n".join(output)


class BadRequest(Exception):
    """Exception to raise when there are problems with an HTTP request."""

MAX_WORDS = 5
MAX_WORD_LENGTH = 20

@timeout(TIME_LIMIT, timeout_exception=TimeoutError)
def process_generate_request(wordlist: List[str], json=False) -> str:
    if len(wordlist) > MAX_WORDS:
        raise BadRequest(f"Too many words! (maximum of {MAX_WORDS})")
    
    if any(len(word) > MAX_WORD_LENGTH for word in wordlist):
        raise BadRequest(f"Words too long! (max length {MAX_WORD_LENGTH})")
        
    return main(wordlist, json)


if __name__ == '__main__':

    wordlist = ["AAAAAAAAAA", "AAAAAAAAAA", "AAAAAAAAAA", "AAAAAAAAAA", "AAAAAAAAAA"]

    # output = main(wordlist)
    # print(output)
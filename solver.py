from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging
logging.basicConfig(level=logging.INFO)


@dataclass
class Field:
    value: int = 0
    marks: List[int] = field(default_factory=lambda: [0 for _ in range(9)])

    def put_mark(self, number):
        self.marks[number - 1] += 1

    def del_mark(self, number):
        self.marks[number - 1] -= 1

    def get_mark(self, number):
        return self.marks[number - 1]

    def find_number(self) -> Optional[int]:
        candidate = None
        for i, mark in enumerate(self.marks):
            if mark == 0:
                if candidate is None:
                    candidate = i + 1
                else:
                    return None
        return candidate


def make_fields():
    return [[Field() for _ in range(9)] for _ in range(9)]


@dataclass
class Board:
    name: str = ""
    # i = row, j = column
    fields: List[List[Field]] = field(default_factory=make_fields)

    def __str__(self):
        separator = "|=========|=========|=========|\n"
        tokens = [self.name, "\n"]
        for i in range(len(self.fields)):
            if i % 3 == 0:
                tokens.append(separator)

            for j in range(len(self.fields[i])):
                if j % 3 == 0:
                    tokens.append("|")
                tokens.append(" ")

                field = self.fields[i][j].value
                if field != 0:
                    tokens.append(str(field))
                else:
                    tokens.append(" ")

                tokens.append(" ")

            tokens.append("|")
            tokens.append("\n")

        tokens.append(separator)

        return "".join(tokens)

    def is_filled(self):
        for row in self.fields:
            for f in row:
                if f.value == 0:
                    return False
        return True

    def verify(self, check_missing=True) -> Optional[str]:
        for starti in (0, 3, 6):
            for startj in (0, 3, 6):
                # check 3x3
                checklist = {n + 1: False for n in range(9)}
                for x in range(starti, starti + 3):
                    for y in range(startj, startj + 3):
                        if self.fields[x][y].value == 0:
                            continue
                        if checklist[self.fields[x][y].value]:
                            return f"Duplicate number {self.fields[x][y].value} in 3x3 {starti},{startj}"
                        checklist[self.fields[x][y].value] = True
                if check_missing:
                    for number, value in checklist.items():
                        if not value:
                            return f"3x3 at position {starti},{startj} is missing number {number}"

        # mark all fields in row
        for i in range(9):
            checklist = {n + 1: False for n in range(9)}
            for j in range(9):
                if self.fields[i][j].value == 0:
                    continue
                if checklist[self.fields[i][j].value]:
                    return f"Duplicate number in row {i}"
                checklist[self.fields[i][j].value] = True
            if check_missing:
                for number, value in checklist.items():
                    if not value:
                        return f"row {i} is missing number {number}"

        # mark all fields in column
        for j in range(9):
            checklist = {n + 1: False for n in range(9)}
            for i in range(9):
                if self.fields[i][j].value == 0:
                    continue
                if checklist[self.fields[i][j].value]:
                    return f"Duplicate number in column {j}"
                checklist[self.fields[i][j].value] = True
            if check_missing:
                for number, value in checklist.items():
                    if not value:
                        return f"column {j} is missing number {number}"

        return "valid"


def read_sudokus(filename: Path) -> List[Board]:
    boards = []

    assert filename.is_file()

    board: Board = None
    row = 0
    with open(filename, "r") as fp:
        for line in fp:
            if board is None:
                row = 0
                name = line.strip()
                board = Board(name)
            else:
                numbers = [int(char) for char in line.strip()]
                for j, number in enumerate(numbers):
                    board.fields[row][j].value = number
                row += 1
                if row == 9:
                    boards.append(board)
                    board = None

    return boards


@dataclass
class Pos:
    i: int
    j: int

    def __iter__(self):
        return iter((self.i, self.j))


class Solver:
    def __init__(self, board):
        self.board = board
        self.setup()

    def put(self, pos: Pos, value: int):
        i, j = pos
        self.board.fields[i][j].value = value

        # mark all fields in 3x3
        starti = int(i / 3) * 3
        startj = int(j / 3) * 3

        for x in range(starti, starti + 3):
            for y in range(startj, startj + 3):
                self.board.fields[x][y].put_mark(value)

        # mark all fields in row
        for y in range(0, 9):
            self.board.fields[i][y].put_mark(value)

        # mark all fields in column
        for x in range(0, 9):
            self.board.fields[x][j].put_mark(value)

    def remove(self, pos: Pos):
        i, j = pos
        value = self.board.fields[i][j].value
        self.board.fields[i][j].value = 0

        # mark all fields in 3x3
        starti = int(i / 3) * 3
        startj = int(j / 3) * 3

        for x in range(starti, starti + 3):
            for y in range(startj, startj + 3):
                self.board.fields[x][y].del_mark(value)

        # mark all fields in row
        for y in range(0, 9):
            self.board.fields[i][y].del_mark(value)

        # mark all fields in column
        for x in range(0, 9):
            self.board.fields[x][j].del_mark(value)

    def setup(self):
        for i, row in enumerate(self.board.fields):
            for j, f in enumerate(row):
                if f.value != 0:
                    self.put(Pos(i, j), f.value)

    def step(self, level=0) -> bool:
        """Finds the next best possible number and then calls itself recursively until
        sudoku is solved.

        First, attempts to deduce the next number from the existing numbers.
        For this, iterate all rows, columns and 3x3 sections. Try to find a number that
        is both missing in the row/column/section and only has one available spot.

        If no such number can be found, find the field with the least possibilities.
        I.e. an empty field that has the least amount of numbers that can fit there,
        given the current numbers on the board.
        Then brute-force all the possibilities for that field.
        """
        def try_put(position, number):
            self.put(position, number)
            if self.step(level=level):
                return True
            else:
                self.remove(position)
                return False

        if self.board.is_filled():
            return True
        tab = " " * level

        # go through all 3x3
        for starti in (0, 3, 6):
            for startj in (0, 3, 6):
                counts: Dict[int, List[Pos]] = {i + 1: [] for i in range(9)}
                for x in range(starti, starti + 3):
                    for y in range(startj, startj + 3):
                        f = self.board.fields[x][y]
                        if f.value == 0:
                            for i in counts.keys():
                                if f.get_mark(i) == 0:
                                    counts[i].append(Pos(x, y))
                for number, positions in counts.items():
                    if len(positions) == 1:
                        return try_put(positions[0], number)

        # go thorugh all rows
        for i in range(9):
            counts = {k + 1: [] for k in range(9)}
            for j in range(9):
                f = self.board.fields[i][j]
                if f.value == 0:
                    for n in counts.keys():
                        if f.get_mark(n) == 0:
                            counts[n].append(Pos(i, j))
            for number, positions in counts.items():
                if len(positions) == 1:
                    return try_put(positions[0], number)

        # go thorugh all columns
        for j in range(9):
            counts = {k + 1: [] for k in range(9)}
            for i in range(9):
                f = self.board.fields[i][j]
                if f.value == 0:
                    for n in counts.keys():
                        if f.get_mark(n) == 0:
                            counts[n].append(Pos(i, j))
            for number, positions in counts.items():
                if len(positions) == 1:
                    return try_put(positions[0], number)


        # find field with least possibilities
        # its sufficient to try out a single field, since every field has a single
        # valid number, so one possibility must work, or the sudoku is impossible
        # (or a previous decision was wrong)
        min_free_numbers = 10
        min_pos = Pos(-1, -1)
        for i in range(9):
            for j in range(9):
                f = self.board.fields[i][j]
                free_numbers = 9
                if f.value == 0:
                    for number in range(1, 10):
                        if f.get_mark(number) != 0:
                            free_numbers -= 1
                    if free_numbers < min_free_numbers:
                        min_pos = Pos(i, j)
                        min_free_numbers = free_numbers

        if min_free_numbers == 0:
            logging.debug(f"{tab}No possible value for position {min_pos}")
            return False

        f = self.board.fields[min_pos.i][min_pos.j]
        possible_numbers = list(filter(lambda n: f.get_mark(n) == 0, range(1, 10)))
        logging.debug(f"{tab}Guessing position {min_pos} - numbers: {possible_numbers}")
        for number in possible_numbers:
            logging.debug(f"{tab}Guess {number} for {min_pos}")
            self.put(min_pos, number)
            if self.step(level=level + 1):
                return True
            else:
                self.remove(min_pos)
        logging.debug(f"{tab}Position {min_pos} has no candidates")

        return False


def single(parser, args):
    if not args.sudoku.is_file():
        parser.error(f"{args.sudoku} is not a file")

    board = read_sudokus(args.sudoku)[0]
    print(board)

    solver = Solver(board)

    solver.step()

    print(board)
    print(board.verify())


def benchmark(parser, args):
    boards = read_sudokus(args.sudokus)
    for board in boards:
        solver = Solver(board)

        solver.step()

        # print(board)

    print("Results:")
    for board in boards:
        print(f"{board.name}: {board.verify()}")

def main():
    import argparse

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='cmd', required=True)
    single_sudoku_parser = subparsers.add_parser("single")
    single_sudoku_parser.add_argument("sudoku", type=Path)
    single_sudoku_parser.set_defaults(command=single)

    multiple_sudoku_parser = subparsers.add_parser("multi")
    multiple_sudoku_parser.add_argument(
        "--sudokus", type=Path, default=Path("sudokus.txt")
    )
    multiple_sudoku_parser.set_defaults(command=benchmark)

    args = parser.parse_args()
    args.command(parser, args)

if __name__ == "__main__":
    import cProfile
    cProfile.run('main()')

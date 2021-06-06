from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Generator
from pathlib import Path
import logging
from itertools import chain

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
class Pos:
    i: int
    j: int

    def __iter__(self):
        return iter((self.i, self.j))


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

    def itercell(self, pos: Pos) -> Generator[Tuple[Field, Pos], None, None]:
        """Iterate through all fields of the 3x3 that pos is located in

        Yields:
            Field, Pos
        """
        i, j = pos
        starti = int(i / 3) * 3
        startj = int(j / 3) * 3

        for x in range(starti, starti + 3):
            for y in range(startj, startj + 3):
                yield self.fields[x][y], Pos(x, y)

    def itercells(self) -> Generator[Tuple[Generator[Tuple[Field, Pos], None, None], Pos], None, None]:
        for i in (0, 3, 6):
            for j in (0, 3, 6):
                yield self.itercell(Pos(i, j)), Pos(i,j)

    def iterrow(self, pos: Pos) -> Generator[Tuple[Field, Pos], None, None]:
        i, j = pos
        for y in range(9):
            yield self.fields[i][y], Pos(i, y)

    def iterrows(self) -> Generator[Tuple[Generator[Tuple[Field, Pos], None, None], int], None, None]:
        for x in range(9):
            yield self.iterrow(Pos(x, 0)), x

    def itercol(self, pos: Pos) -> Generator[Tuple[Field, Pos], None, None]:
        i, j = pos
        for x in range(9):
            yield self.fields[x][j], Pos(x, j)

    def itercols(self) -> Generator[Tuple[Generator[Tuple[Field, Pos], None, None], int], None, None]:
        for y in range(9):
            yield self.itercol(Pos(0, y)), y

    def is_filled(self):
        for row, _ in self.iterrows():
            for f, _ in row:
                if f.value == 0:
                    return False
        return True

    def verify(self, check_missing=True) -> Optional[str]:
        for cell, cell_pos in self.itercells():
            checklist = {n: False for n in range(1, 10)}
            for f, pos in cell:
                if f.value == 0:
                    continue
                if checklist[f.value]:
                    return f"Duplicate number {f.value} in 3x3 {cell_pos}"
                checklist[f.value] = True
            if check_missing:
                for number, value in checklist.items():
                    if not value:
                        return f"3x3 at position {cell_pos} is missing number {number}"

        for row, row_nr in self.iterrows():
            checklist = {n: False for n in range(1, 10)}
            for f, pos in row:
                if f.value == 0:
                    continue
                if checklist[f.value]:
                    return f"Duplicate number {f.value} in row {row_nr}"
                checklist[f.value] = True
            if check_missing:
                for number, value in checklist.items():
                    if not value:
                        return f"row {row_nr} is missing number {number}"

        for col, col_nr in self.itercols():
            checklist = {n: False for n in range(1, 10)}
            for f, pos in col:
                if f.value == 0:
                    continue
                if checklist[f.value]:
                    return f"Duplicate number {f.value} in column {col_nr}"
                checklist[f.value] = True
            if check_missing:
                for number, value in checklist.items():
                    if not value:
                        return f"column {col_nr} is missing number {number}"

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


class Solver:
    def __init__(self, board):
        self.board = board
        self.setup()

    def put(self, pos: Pos, value: int):
        i, j = pos
        self.board.fields[i][j].value = value

        # mark all fields in 3x3
        for f, _ in self.board.itercell(pos):
            f.put_mark(value)

        # mark all fields in row
        for f, _ in self.board.iterrow(pos):
            f.put_mark(value)

        # mark all fields in column
        for f, _ in self.board.itercol(pos):
            f.put_mark(value)

    def remove(self, pos: Pos):
        i, j = pos
        value = self.board.fields[i][j].value
        self.board.fields[i][j].value = 0

        # mark all fields in 3x3
        for f, _ in self.board.itercell(pos):
            f.del_mark(value)

        # mark all fields in row
        for f, _ in self.board.iterrow(pos):
            f.del_mark(value)

        # mark all fields in column
        for f, _ in self.board.itercol(pos):
            f.del_mark(value)

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
        if self.board.is_filled():
            return True
        tab = " " * level

        # go through all 3x3, rows and cols
        for iterator, _ in chain(self.board.itercells(), self.board.iterrows(), self.board.itercols()):
            # count free positions for each number in this 3x3, row or col
            counts: Dict[int, List[Pos]] = {k: [] for k in range(1, 10)}
            for f, pos in iterator:
                if f.value == 0:
                    for number in counts.keys():
                        if f.get_mark(number) == 0:
                            counts[number].append(pos)

            # if there is a number that has only one spot to go into, write it
            for number, positions in counts.items():
                if len(positions) == 1:
                    self.put(positions[0], number)
                    if self.step(level=level):
                        return True
                    else:
                        self.remove(positions[0])
                        return False


        # find field with least possibilities
        # its sufficient to try out a single field, since every field has a single
        # valid number, so one possibility must work, or the sudoku is impossible
        # (or a previous decision was wrong)
        min_free_numbers = 10
        min_pos = Pos(-1, -1)
        min_field = None
        for row, _ in self.board.iterrows():
            for f, pos in row:
                free_numbers = 9
                if f.value == 0:
                    for number in range(1, 10):
                        if f.get_mark(number) != 0:
                            free_numbers -= 1
                    if free_numbers < min_free_numbers:
                        min_pos = pos
                        min_free_numbers = free_numbers
                        min_field = f

        if min_free_numbers == 0:
            logging.debug(f"{tab}No possible value for position {min_pos}")
            return False

        possible_numbers = list(filter(lambda n: min_field.get_mark(n) == 0, range(1, 10)))
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

        print(board)

    print("Results:")
    for board in boards:
        print(f"{board.name}: {board.verify()}")


def main():
    import argparse

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd", required=True)
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
    main()

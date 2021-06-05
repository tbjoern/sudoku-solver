# A simple sudoku solver

Solves any sudoku via basic deduction and recursion.

## Installation

Requires python 3.7 or later
The `solver.py` file can be used standalone

## Usage

Solve a single sudoku specfied in a file. This will print the board before and after solving the sudoku.
`python solver.py single <filename>`

Solve multiple sudokus all specified in a file. It will print the solved sudoku boards.
`python solver.py multi <filename>`

### Input file format

See [sudoku.txt](./sudoku.txt) and [sudokus.txt](./sudokus.txt)
Each sudoku consists of 10 lines. The first line is the name of the sudoku.
Each line represents the digits in one row of the sudoku. A 0 denotes an empty space.
If specifying multiple sudokus, they must **not** be separated by newlines.

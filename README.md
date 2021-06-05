# A simple sudoku solver

Solves any sudoku via basic deduction and recursion.

## Installation

Requires python 3.7 or later.

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


## How it works

The solver has 3 core mechanisms: Keeping track of which number can be entered in which field,
deducing numbers from what is on the board and recursion/guessing when nothing can be deduced.

### Keeping track of empty fields

Each field on the board stores the number that is written on it (0 for empty).
Additionally, it stores a `mark` integer for each number from 1-9.
The mark tells us whether the respective number could be written on the field (0)
or if the number is already present in the row, column or 3x3 section (> 0)

We use an integer instead of a boolean, since this allows us to easily add and remove
numbers for the recursion part of the solver.

When we put in a new number, we add 1 to the mark for all fields in row, column and 3x3.
When we remove a number, we just substract 1 for all the marks.

### Deducing numbers

We look at each row, column and 3x3 section. If we find a number that is not yet present
and only has one available spot, we can confidently write it down.

### Guessing

Finally, if the deduction fails, we search for the field with the lowest number of
possibilities, given the current board configuration.
We find this field by looking at the marks for each field and taking the one that
has the lowest amount of marks with a value of 0.

Then, we try out each number and see if it yields a valid solution.

### Recursion

The above steps are executed recursively until the board is completely filled.
Since we make sure that every number that we enter is valid at the time of insertion,
a filled board means that we have a valid solution.

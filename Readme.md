# kifugen

Generate printable pdf game records (kifu) from `sgf` go/baduk/weiqi replays.
kifugen takes your `sgf` file and converts is into a `latex` format, that then can
be easily compiled into a pdf file.

![Preview Image](pdfpreview.png)

# Requirements

To run kifugen you will need:
- Python 3.6
- A latex distribution with:
    - `latex`
    - `dvips`
    - `ps2pdf`
    - the `psgo` package

# Usage
The basic usage is `kifugen <file> [options]` where file is the `.sgf` file and options are:

| Option         | Meaning                       | Default   |
| :------------- | :---------------------------- | :-------- |
| -se n          | "split every" n moves         | 50        |
| -cn            | continuous numbering          | false     |
| -c             | compile to pdf                | false     |
| -o             | open the pdf after compilation| false     |

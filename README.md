# Hyper-unspecific data parsing and graphing scripts

> A simple Python tool/framework for generating statistics about code in a git
> repository.

## ...What?!

I like making random graphs about random stats (code in this case), but got
tired of constantly writing new hyper-specific scripts for parsing and graphing
that data.

This project aims to solve that by not making any assumptions about the file
structure or similar things, and not requiring code changes to collect more
stats.

Thanks to @nico for the name :^)

## Requirements

- Python 3.11 ([see here](https://chaos.social/@linusgroh/109888696689742796))
- `braceexpand` for nicer file glob patterns (`pip install -r requirements.txt`)
- The following utilities need to be in `PATH`: `git`, `scc` (if used as an
  analyzer)

## Usage

Create a config file (TOML):

```toml
repository = "/path/to/project"
output = "output/stats.json"

[analyzers]

[analyzers.lines]
type = "scc"

[analyzers.fixmes_and_todos]
type = "grep"
regex = "fixme|todo"
case_insensitive = true
```

Then call the `main.py` script with it:

```console
python3 main.py path/to/config.toml
```

`output/stats.json` will be created, containing a JSON blob that looks something
like this:

```json
[
  {
    "commit": "c048cf2004",
    "timestamp": 1679655523.0,
    "analyzers": {
      "lines": {
        "AK/AllOf.h": {
          "language": "C Header",
          "bytes": 848,
          "lines": 37,
          "code": 25,
          "comment": 5,
          "blank": 7,
          "complexity": 1
        }
        // ...
      },
      "fixmes_and_todos": {
        "Some/File.cpp": 42
        // ...
      }
    }
  }
  // ...
]
```

That's the hard part done! You can now do whatever you want with this data, here
are some ideas...

## Scripts

### `export_csv.py`

Not everything likes JSON, but maybe CSV works! Takes all fields of each
analyzer and puts them into individual files named `<analyzer>.csv` in the same
directory as the input file.

```console
$ python3 scripts/export_csv.py output/stats.json
$ ls output
fixmes_and_todos.csv lines.csv stats.json
$ cat output/fixmes_and_todos.csv | head -1
c048cf2004,2023-03-24 10:58:43,Some/File.cpp,42
$ cat output/lines.csv | head -1
c048cf2004,2023-03-24 10:58:43,AK/AllOf.h,C Header,848,37,25,5,7,1
```

This was written specifically with Postgres `COPY` in mind, and may or may not
work for your use case.

### `plot_grep_analyzer.py`

Barebones matplotlib script to plot the sum of `grep` analyzer results per
commit over time.

```console
python3 scripts/plot_grep_analyzer.py output/stats.json fixmes_and_todos
```

## Config options

| Group                | Name              | Description                                                                                                                                                                                                        | Default             |
| :------------------- | :---------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------ |
| Top-level            | `repository`      | Path to input git repository                                                                                                                                                                                       | required            |
|                      | `output`          | Path to output JSON file                                                                                                                                                                                           | required            |
|                      | `processes`       | Number of processes to use at the same time                                                                                                                                                                        | number of CPU cores |
|                      | `commit_sampling` | `all`: Don't skip any commits                                                                                                                                                                                      | `all`               |
|                      |                   | `last`: Only analyze the last commit, useful if you want to generate stats                                                                                                                                         |                     |
|                      |                   | `daily`: Only analyze the first commit on each day (in UTC), useful for large projects or if you're only interested in a general trend, not per-commit stats                                                       |                     |
| `[cache]`            | `directory`       | Output directory for caching per-commit results. Massively speeds up subsequent runs. Caching is based on the current configuration, so changes to an analyzer's configuration will invalidate only its own cache. | none                |
| `[logging]`          | `level`           | Python logging level                                                                                                                                                                                               | `INFO`              |
| `[analyzers.<name>]` | `type`            | Type of this analyzer (see below)                                                                                                                                                                                  | required            |

### Analyzers

#### `grep`

Count occurences of strings or regular expressions across all files. Does not
actually use grep(1).

| Name               | Description                                                          | Default  |
| :----------------- | :------------------------------------------------------------------- | :------- |
| `files_glob`       | Glob pattern to run this analyzer on a subset of files               | none     |
| `regex`            | Regular expression pattern to look for, make sure to escape properly | required |
| `case_insensitive` | Whether to compile the pattern with `re.IGNORECASE`                  | false    |

#### `scc`

Uses [scc(1)](https://github.com/boyter/scc) to generate per-file line count
stats.

| Name         | Description                                            | Default |
| :----------- | :----------------------------------------------------- | :------ |
| `files_glob` | Glob pattern to run this analyzer on a subset of files | none    |

## TODO

Tests, CI, more analyzers (e.g. for commit messages).

## License

MIT.

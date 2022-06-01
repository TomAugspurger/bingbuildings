# stactools-bingbuildings

[![PyPI](https://img.shields.io/pypi/v/stactools-bingbuildings)](https://pypi.org/project/stactools-bingbuildings/)

- Name: bingbuildings
- Package: `stactools.bingbuildings`
- PyPI: https://pypi.org/project/stactools-bingbuildings/
- Owner: @TomAugspurger
- Dataset homepage: http://example.com
- STAC extensions used:
  - [table](https://github.com/stac-extensions/table/)
- Extra fields:
  - `bingbuildings:region`: The region covered by an item.

This package generates STAC items for the Bing Maps building footprints dataset.

## STAC Examples

- [Collection](examples/collection.json)
- [Item](examples/item/item.json)

## Installation
```shell
pip install stactools-bingbuildings
```

## Command-line Usage

Description of the command line functions

```shell
$ stac bingbuildings create-item source destination
```

Use `stac bingbuildings --help` to see all subcommands and options.

## Contributing

We use [pre-commit](https://pre-commit.com/) to check any changes.
To set up your development environment:

```shell
$ pip install -e .
$ pip install -r requirements-dev.txt
$ pre-commit install
```

To check all files:

```shell
$ pre-commit run --all-files
```

To run the tests:

```shell
$ pytest -vv
```

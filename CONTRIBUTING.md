# Contributing

Contributions to modern Eastern Armenian in the reformed RA orthography are welcome. Western Armenian and traditional orthography are outside this repository's scope.

A rule change must include:

- a stable or proposed `HY-*` identifier;
- the rule, applicability, wrong and correct examples, exception, severity, and evidence;
- a source-registry entry or a usage aggregate that satisfies `METHODOLOGY.md`;
- a regression test or golden scenario;
- a changelog entry when an existing recommendation changes.

Run `python -m unittest discover -s tests -v` and `python tools/validate.py` before opening a pull request.

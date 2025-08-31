# LaTeX3 Tutorial

This is a LaTeX version of the [LaTeX3 tutorial](https://www.alanshawn.com/latex3-tutorial/).
A LaTeX version of this tutorial can be modified by the LaTeX community.


## Document options

- `\ExportExamples`: if activated, the examples will be exported to `./examples`
- `\UseMintedHighlighting`: if activated, the `minted` package will be used for syntax highlighting


## Building

- Development build: `make dev`
  - In development build, the `minted` cache is always regenerated
- Finalize build:
  - In finalize build, the `minted` cache will be frozen
- Default build: `make`
  - In default build, the frozen `minted` cache will be used

## Example Environment (latexsample)

By default, the `latexsample` environment will generate an anonymous LaTeX example that is executed and exported.

- Keys
  - `examplelabel={label}`: specifies the label of the example
  - `exampletitle={title}`: specifies the title of the example
  - `noexec`: do not execute the example
  - `silentexec`: execute the code but do not show results in document
  - `noexport`: do not export the example
  - `notitle`: anonymous example (turns off export automatically)
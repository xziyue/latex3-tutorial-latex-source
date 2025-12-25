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


## FAQ

- Fixing minted error `minted v3+ executable is not installed...`: <https://tex.stackexchange.com/questions/732260/package-minted-error-minted-v3-executable-is-not-installed-is-not-added-totor>
  - When using `latexminted`, custom lexers are not allowed by default due to security reasons. Follow the [documentation](https://pypi.org/project/latexminted/) to create `.latexminted_config` file in specified directories and set `enable_cwd_config` to true. An example is shown here:
    ```json
    {
      "security":
      {
        "enable_cwd_config": true
      }
    }
    ```
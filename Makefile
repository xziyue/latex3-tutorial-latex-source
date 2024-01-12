TEXBIN=latexmk
TEX_SRC=main.tex
TEX_BUILD_CMD=$(TEXBIN) -synctex=1 -interaction=nonstopmode -file-line-error -pdf $(TEX_SRC) -f

.DEFAULT_GOAL:=dev

clean_signals:
	rm -f USE_SHELL_ESCAPE MINTED_FINALIZE

clean_examples:
	rm -rf examples/*.tex

clean: clean_signals clean_examples
	rm -f main.pdf *.out *aux *bbl *blg *log *toc *.ptb *.tod *.fls *.fdb_latexmk *.lof *.vrb
	rm -rf _minted-main/

dev: clean_signals clean_examples
	touch USE_SHELL_ESCAPE
	$(TEX_BUILD_CMD) --shell-escape

finalize: clean
	touch USE_SHELL_ESCAPE
	touch MINTED_FINALIZE
	$(TEX_BUILD_CMD) --shell-escape

build: clean_signals
	$(TEX_BUILD_CMD)



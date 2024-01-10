TEXBIN=latexmk
TEX_SRC=main.tex
TEX_BUILD_CMD=$(TEXBIN) -synctex=1 -interaction=nonstopmode -file-line-error -pdf $(TEX_SRC) -f

.DEFAULT_GOAL:=dev

clean_signals:
	rm -f USE_SHELL_ESCAPE MINTED_FINALIZE

dev: clean_signals
	touch USE_SHELL_ESCAPE
	$(TEX_BUILD_CMD) --shell-escape

finalize: clean_signals
	touch USE_SHELL_ESCAPE
	touch MINTED_FINALIZE
	$(TEX_BUILD_CMD) --shell-escape

build: clean_signals
	$(TEX_BUILD_CMD)


clean: clean_signals
	rm -f main.pdf *.out *aux *bbl *blg *log *toc *.ptb *.tod *.fls *.fdb_latexmk *.lof
	rm -rf _minted-main/
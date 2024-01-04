TEXBIN=latexmk
TEX_STYLE=style/default.tex
TEXPROT_SRC=main_prototype.tex
TEX_SRC=main.tex
PREPROC_LOG=main_proprocess_log.yaml

export_style:
	python3 tex_preprocessor.py export-style $(TEX_STYLE)

preprocess:
	python3 tex_preprocessor.py process $(TEXPROT_SRC) $(TEX_SRC) -l $(PREPROC_LOG) -p -c

main: preprocess export_style
	$(TEXBIN) -synctex=1 -interaction=nonstopmode -file-line-error -pdf $(TEX_SRC) -f

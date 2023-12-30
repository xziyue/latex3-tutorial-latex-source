TEXBIN=latexmk
TEXPROT_SRC=main_prototype.tex
TEX_SRC=main.tex

preprocess:
	python3 tex_preprocessor.py $(TEXPROT_SRC) $(TEX_SRC)

main: preprocess
	$(TEXBIN) -synctex=1 -interaction=nonstopmode -file-line-error -pdf $(TEX_SRC)

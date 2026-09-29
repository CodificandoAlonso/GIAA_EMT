# Sheet to compile the tex files indicated.
# DOCS document specify all the tex to compile, OUT the outer dir where the pdf will be located
DOCS := cas-sc-template cas-dc-template cas-dc-sample cas-sc-sample
AUX  := build
OUT  := build/out
.PHONY: all clean

all:
	@mkdir -p $(AUX) $(OUT)
	@for doc in $(DOCS); do \
	  latexmk -lualatex -interaction=nonstopmode -halt-on-error \
	          -auxdir=$(AUX) -outdir=$(OUT) $$doc.tex || exit 1; \
	done

clean:
	rm -rf $(AUX)
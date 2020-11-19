## Jupyter/Zeppelin conversion

This repo has code for converting Zeppelin notebooks to Jupyter's ipynb format.

To convert a notebook, run:

```
python jupyter-zeppelin.py zeppelin-example-notebook.json Example.ipynb
```

### Supported conventions

This converter supports the following Zeppelin conventions:

* Code paragraphs are converted to code cells
* `%md` paragraphs are converted to Jupyter markdown cells
* `%html` paragraphs are converted to Jupyter code cells using cell magic `%%html`
* `%sql` paragraphs are converted to Jupyter code cells using cell magic `%%sql`
* Paragraphs with unknown magics are converted to raw cells
* TEXT output is converted to `text/plain` output
* HTML output is converted to `text/html` output; some style and JS may not work in Jupyter
* TABLE output is converted to simple `text/html` tables
  * `%html` table cells are embedded in the table HTML
  * Normal table cells are escaped and then embedded in the table HTML

import os, sys
import re
import argparse
import csv
import json
import html
import nbformat
import codecs
from io import StringIO

MD = re.compile(r'%md\s')
SQL = re.compile(r'%sql\s')
UNKNOWN_MAGIC = re.compile(r'%\w+\s')
HTML = re.compile(r'%html\s')

def read_io(path):
    """Reads the contents of a local path into a StringIO.
    """
    note = StringIO()
    with open(path, encoding='utf-8-sig') as local:
        for line in local.readlines():
            note.write(line)

    note.seek(0)

    return note

def table_cell_to_html(cell):
    """Formats a cell from a Zeppelin TABLE as HTML.
    """
    if HTML.match(cell):
        # the contents is already HTML
        return cell
    else:
        return html.escape(cell)

def table_to_html(tsv):
    """Formats the tab-separated content of a Zeppelin TABLE as HTML.
    """
    io = StringIO(tsv)
    reader = csv.reader(io, delimiter="\t")
    fields = next(reader)
    column_headers = "".join([ "<th>" + name + "</th>" for name in fields ])
    lines = [
            "<table>",
            "<tr>{column_headers}</tr>".format(column_headers=column_headers)
        ]
    for row in reader:
        lines.append("<tr>" + "".join([ "<td>" + table_cell_to_html(cell) + "</td>" for cell in row ]) + "</tr>")
    lines.append("</table>")
    return "\n".join(lines)


def convert_json(zeppelin_json):
    """Converts a Zeppelin note from JSON to a Jupyter NotebookNode.
    """
    return convert_parsed(json.load(zeppelin_json))

def convert_parsed(zeppelin_note):
    """Converts a Zeppelin note from parsed JSON to a Jupyter NotebookNode.
    """
    notebook_name = zeppelin_note['name'].replace('/', '')

    cells = []
    index = 0
    for paragraph in zeppelin_note['paragraphs']:
        code = paragraph.get('text')
        if not code:
            continue

        code = code.lstrip()

        cell = {}

        if MD.match(code):
            cell['cell_type'] = 'markdown'
            cell['metadata'] = {}
            cell['source'] = code.lstrip('%md').lstrip("\n") # remove '%md'
        elif SQL.match(code) or HTML.match(code):
            cell['cell_type'] = 'code'
            cell['execution_count'] = index
            cell['metadata'] = {}
            cell['outputs'] = []
            cell['source'] = '%' + code # add % to convert to cell magic
        elif UNKNOWN_MAGIC.match(code):
            # use raw cells for unknown magic
            cell['cell_type'] = 'raw'
            cell['metadata'] = {'format': 'text/plain'}
            cell['source'] = code
        else:
            cell['cell_type'] = 'code'
            cell['execution_count'] = index
            cell['metadata'] = {'autoscroll': 'auto'}
            cell['outputs'] = []
            cell['source'] = code

        cells.append(cell)

        result = paragraph.get('result')
        if cell['cell_type'] == 'code' and result:
            if result['code'] == 'SUCCESS':
                result_type = result.get('type')
                output_by_mime_type = {}
                if result_type == 'TEXT':
                    output_by_mime_type['text/plain'] = result['msg']
                elif result_type == 'HTML':
                    output_by_mime_type['text/html'] = result['msg']
                elif result_type == 'TABLE':
                    output_by_mime_type['text/html'] = table_to_html(result['msg'])

                cell['outputs'] = [{
                    'output_type': 'execute_result',
                    'metadata': {},
                    'execution_count': index,
                    'data': output_by_mime_type
                }]

        index += 1

    notebook = nbformat.from_dict({
        "metadata": {
            "kernelspec": {
                "display_name": "Spark 2.0.0 - Scala 2.11",
                "language": "scala",
                "name": "spark2-scala"
            },
            "language_info": {
                "codemirror_mode": "text/x-scala",
                "file_extension": ".scala",
                "mimetype": "text/x-scala",
                "name": "scala",
                "pygments_lexer": "scala",
                "version": "2.11.8"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2,
        "cells" : cells,
    })

    return (notebook_name, notebook)

def write_notebook(notebook_name, notebook, path=None):
    """Writes a NotebookNode to a file created from the notebook name.

    If path is None, the output path will be created the notebook name in the current directory.
    """
    filename = path
    if not filename:
        filename = notebook_name + '.ipynb'
        if os.path.exists(filename):
            for i in range(1, 1000):
                filename = notebook_name + ' (' + str(i) + ').ipynb'
                if not os.path.exists(filename):
                    break
                if i == 1000:
                    raise RuntimeError('Cannot write %s: versions 1-1000 already exist.' % (notebook_name,))

    with open(filename, 'w', encoding='UTF-8') as io:
        nbformat.write(notebook, io)

    return filename

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file_path", help="zeppelin notebook file", default=None)
    parser.add_argument("output_file_path", help="jupyter notebook file", default=None, nargs='?')

    args = parser.parse_args()
    zeppelin_note_path = args.input_file_path
    target_path = args.output_file_path
    
    name, content = convert_json(read_io(zeppelin_note_path))
    filename = write_notebook(name, content, target_path)
    print(f"Converted '{zeppelin_note_path}' to '{filename}'")


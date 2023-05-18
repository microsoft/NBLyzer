// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import * as net from 'net';
import * as vscode from 'vscode';

export class ServerHandler {
    diagnosticCollection: vscode.DiagnosticCollection;
    constructor(diagnosticCollection: vscode.DiagnosticCollection) {
        this.diagnosticCollection = diagnosticCollection;
    }
    serializeMessage(action: string, parameters?, notebookUri?): string {
        let message = {event: action};
        if(parameters){
            message["params"] = parameters;
        }
        if (notebookUri) {
            message["notebook_name"] = notebookUri;
        }
        return JSON.stringify(message);
    }

    postToServer(event: string, notebook?, params?) {
        return new Promise((resolve, reject) => {
            var client = new net.Socket();
            let notebook_path;
            if(notebook == undefined) {
                notebook_path = undefined;
            }
            else {
                notebook_path = notebook.uri.path;
            }
            client.on('error', (err) => {
                client.destroy()
                console.log(err.message)
                if (event == "open_notebook") {
                    reject("Server isn't running.");
                }
                else {
                    vscode.window.showErrorMessage("Nblyzer server stopped unexpectedly. Please close all notebooks and start NBLyzer again.")
                }
            });
            client.on('data', (data) => {
                this.result_handler(data, notebook);
                resolve(data);
                client.destroy();
            });
            client.connect(9999, 'localhost', () => {
                client.write(this.serializeMessage(event, params, notebook_path));
            });
        });
    }

    notebookCellsToJSON(notebookCells) {
        let contents = [];
        for (const cell of notebookCells) {
            let cell_kind = "code";
            if (cell.kind == 1) {
                cell_kind = "markdown";
            }
            contents.push({
                cell_type: cell_kind,
                language: cell.document.languageId,
                source: cell.document.getText()
            });
        }
        return contents;
    }

    result_handler(data, notebook) {
        console.log(`server response: ${data}`);
        var data_json = JSON.parse(data.toString('utf-8'));
        if (data_json.status == "success") {
            try {
                notebook.getCells().forEach(cell => {
                    this.remove_diagnostics(cell.document.uri);
                })
                data_json.result.forEach(res => {
                    this.refresh_diagnostics(res, notebook)
                });
            }
            catch {}
        }
    }
    refresh_diagnostics(cell_problems, notebook) {
        const diagnostics: vscode.Diagnostic[] = [];
        cell_problems.errors.forEach((err) => {
            let err_line = err.line - 1
            if (err.label != "") {
                let index = notebook.cellAt(cell_problems.cell_id).document.lineAt(err_line).text.indexOf(err.label);
                diagnostics.push(new vscode.Diagnostic(
                    new vscode.Range(err_line, index, err_line, index + err.label.length), 
                    err.message,
                    vscode.DiagnosticSeverity.Warning));
            }
            else {
                diagnostics.push(new vscode.Diagnostic(
                    new vscode.Range(err_line, 0, err_line, notebook.cellAt(cell_problems.cell_id).document.lineAt(err_line).length - 1), 
                    err.message,
                    vscode.DiagnosticSeverity.Warning));
            }
        });
        this.diagnosticCollection.set(notebook.cellAt(cell_problems.cell_id).document.uri, diagnostics);
    }

    remove_diagnostics(cellUri) {
        this.diagnosticCollection.delete(cellUri);
    }
}

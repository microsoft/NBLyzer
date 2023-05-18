// Copyright (c) Microsoft Corporation.
// Licensed under the MIT license.

import * as vscode from 'vscode';
import {ServerHandler} from "./server_handler"
import * as constants from './constants'
import * as child_process from 'child_process';

export class Events {
    serverHandler: ServerHandler;
    pendingCommit;
    analyses: string[];

    constructor(serverHandler: ServerHandler) {
        this.serverHandler = serverHandler;
        this.pendingCommit = new Map()
        this.analyses = [];
    }

    openNotebook = async (notebook_doc, extensionPath) => {
    var parameters = {notebook_json: this.serverHandler.notebookCellsToJSON(notebook_doc.getCells())};
        await this.serverHandler.postToServer("open_notebook", notebook_doc, parameters)
        .then(async () => {
            this.pendingCommit.set(notebook_doc.uri.path, -1);
            if(this.analyses.length > 0)
                setTimeout(async () => {await this.serverHandler.postToServer("add_active_analyses", notebook_doc, {active_analyses: this.analyses})}, 500);
        })
        .catch(async () => {
            await this.startServer(extensionPath)
            .then(async () => { 
                await this.serverHandler.postToServer("open_notebook", notebook_doc, parameters)
                .then(async () => {
                    this.pendingCommit.set(notebook_doc.uri.path, -1);
                    if(this.analyses.length > 0) {
                        setTimeout(async () => {await this.serverHandler.postToServer("add_active_analyses", notebook_doc, {active_analyses: this.analyses})}, 500);
                    }
                })
                .catch((message) => {vscode.window.showErrorMessage(message);}) 
            })
            .catch((message) => {vscode.window.showErrorMessage(message);})
        });
    }

    chooseAnalyses = async() => {
        let picked;
        picked = this.analyses.find(a => a === constants.DATA_LEAK);
            let dataLeakItem = { label: constants.DATA_LEAK, picked: picked, detail: "An analysis to detect potential dependency between test and training data." };
            picked = this.analyses.find(a => a === constants.STALE);
            let staleItem = { label: constants.STALE, picked: picked, detail: "An analysis that detects states that if executed directly may compute with an old state." };
            picked = this.analyses.find(a => a === constants.IDLE);
            let idleItem = { label: constants.IDLE, picked: picked, detail: "An analysis that detects cells that do not modify data used in other cells and may be candidates for cleaning." };
            picked = this.analyses.find(a => a === constants.ISOLATED);
            let isolatedItem = { label: constants.ISOLATED, picked: picked, detail: "An analysis that detects cells that are disconnected from all other cells and may be candidates for cleaning." };
        let analysis_items = await vscode.window.showQuickPick([
            staleItem,
            isolatedItem,
            idleItem,
            dataLeakItem
        ], {
            matchOnDescription: true,
            matchOnDetail: true,
            canPickMany: true,
            title: 'Please select what analysis results you want to see.'
        });
        this.analyses = [];
        analysis_items.forEach(analysis => {
            this.analyses.push(analysis.label)
        })
        var parameters_analyses = {active_analyses: this.analyses};
        vscode.workspace.notebookDocuments.forEach(async notebook_doc => {
            await this.serverHandler.postToServer("add_active_analyses", notebook_doc, parameters_analyses);
        })
    }
    startServer = async(extensionPath) => {
        return new Promise((resolve, reject) => {
            let nblyzerServerProcess = child_process.spawn('python', [extensionPath]);
            setTimeout(() => resolve("all good"), 500)
            nblyzerServerProcess.stderr.on('data', (err) => {reject(`Problem starting NBLyzer server ${err.message}`)})
            nblyzerServerProcess.stdout.on('data', (data) => {
                console.log(`stdout: ${data}`);
            });
        })
    }
    stopServer = async() => {
        await this.serverHandler.postToServer("close");
    };
    
    closeNotebook = async(notebook_doc: vscode.NotebookDocument) => {
        await this.serverHandler.postToServer("close_notebook", notebook_doc);
        notebook_doc.getCells().forEach(cell => {
            this.serverHandler.remove_diagnostics(cell.document.uri);
        })
        vscode.window.showWarningMessage("NBlyzer session ended for the closed notebook.")
    }
    
    changeNotebook = async (notebookChangeEvent: vscode.NotebookDocumentChangeEvent) => {
        let cellChanges = notebookChangeEvent.cellChanges;
        let contentChanges = notebookChangeEvent.contentChanges;
        for (let cellChange of cellChanges) {
            this.pendingCommit.set( notebookChangeEvent.notebook.uri.path, cellChange.cell.index);
            if (cellChange.executionSummary) {
                if (cellChange.executionSummary.success) {
                    let parameters = { changed_cell_id: cellChange.cell.index, changed_cell_code: cellChange.cell.document.getText() };
                    await this.serverHandler.postToServer("run_cell", notebookChangeEvent.notebook, parameters);
                }
            }
        }
        for (let contentChange of contentChanges) {
            if (contentChange.addedCells.length > 0) {
                let addedCell = contentChange.addedCells[0];
                if (this.pendingCommit.get(notebookChangeEvent.notebook.uri.path) > -1) {
                    let commit_index = this.pendingCommit.get(notebookChangeEvent.notebook.uri.path);
                    if (addedCell.index <= commit_index) {
                        commit_index += 1;
                    }
                    let parameters = { new_code: notebookChangeEvent.notebook.getCells()[commit_index].document.getText(), cell_index: this.pendingCommit.get(notebookChangeEvent.notebook.uri.path), with_result: 0 };
                    this.pendingCommit.set(notebookChangeEvent.notebook.uri.path, -1);
                    await this.serverHandler.postToServer("change_cell", notebookChangeEvent.notebook, parameters);
                }
                setTimeout(async () => {
                    let parameters = { position: addedCell.index, kind: addedCell.kind, content: addedCell.document.getText() };
                    await this.serverHandler.postToServer("add_cell", notebookChangeEvent.notebook, parameters);
                }, 500);
            }
            if (contentChange.removedCells.length > 0) {
                this.serverHandler.remove_diagnostics(contentChange.removedCells[0].document.uri)
                if (this.pendingCommit.get(notebookChangeEvent.notebook.uri.path) > -1) {
                    let commit_index = this.pendingCommit.get(notebookChangeEvent.notebook.uri.path);
                    if (contentChange.range.start <= commit_index) {
                        commit_index -= 1;
                    }
                    let parameters = { new_code: notebookChangeEvent.notebook.getCells()[commit_index].document.getText(), cell_index: this.pendingCommit.get(notebookChangeEvent.notebook.uri.path), with_result: 0 };
                    this.pendingCommit.set(notebookChangeEvent.notebook.uri.path, -1);
                    await this.serverHandler.postToServer("change_cell", notebookChangeEvent.notebook, parameters);
                }
                setTimeout(async () => {
                    let parameters = { position: contentChange.range.start };
                    await this.serverHandler.postToServer("remove_cell", notebookChangeEvent.notebook, parameters);
                }, 500);
            }
        }
    };
    
    changeCellCode = async (notebookEditorChange: vscode.NotebookEditorSelectionChangeEvent) => {
        let commit_index = this.pendingCommit.get(notebookEditorChange.notebookEditor.notebook.uri.path)
        if (commit_index > -1) {
            this.pendingCommit.set(notebookEditorChange.notebookEditor.notebook.uri.path, -1);
            let parameters = { new_code: notebookEditorChange.notebookEditor.notebook.getCells()[commit_index].document.getText(), cell_index: commit_index, with_result: 1 };
            await this.serverHandler.postToServer("change_cell", notebookEditorChange.notebookEditor.notebook, parameters);
        }
    }
}

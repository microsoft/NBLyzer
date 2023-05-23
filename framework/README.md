# Introduction 
NBLyzer: Static analysis framework for data science notebooks

Our static analyzer also performs the following analyses:

1. **Stale cell detection**, where stale cell is a cell in which are used unbound identifiers whose defintions have been affected by execution of the changes in some other cell. 
Similar as for Safe cell analysis, Stale cell analysis can be computed with respect of different depth levels. Above is given description of the computation of stale level 1. 

2. **Idle cell detection**, where idle cell is a cell which execution, no matter the changes made in it, will not change a state of any other cell of a notebook, i.e. will not affect any definition of other cells’ identifiers.

3. **Isolated cell detection**, where isolated cell is a cell which has no identifiers' definitions dependent on unbounded identifiers (identifiers of other cells) and which identifiers
are not used in any way out of the cell itself.

4. **Data Leakage Analysis**, where a data leakage is the use of non disjoint data to test and train a model


All the analyses are in alpha, meaning they are a work in progress (WIP)

# Getting Started
## Build and Test
1. Clone this repository
2. Copy NBlyzer/nblyzer folder to C:/Users/some-user/.vscode
3. Open the extension folder in VS Code (C:/Users/some-user/.vscode/nblyzer).
4. In terminal run `npm install`
5. Start debugging the extension (`Run->Start Debugging`).
6. In the Extension Development Host window, open your `.ipynb` notebook file (`File->Open File`).
7. After your Jupyter notebook is loaded, run the analysis by clicking `Dataleak Analysis` in Jupyter buttons toolbar.
8. A pop-up message will appear informing you whether a dataleak has been detected.
9. By clicking `See details` you open up a new notebook for *every* cell execution path that leads to a possible dataleak.

## Running tests
You can find tests for this module in NBLyzer/nblyzer/tests folder. To run them you should:
1. `cd nblyzer`
2. `set PYTHONPATH=nblyzer_backend/src/` (must run in command prompt) Note: if on mac or linux use `export` instead of `set`
3. (Optional) Provide a text file named `access.txt` to `nblyzer_backend/src/resource_utils` folder. File format details are listed below. (Do this step only if you want to use remote resources)
4. `python -m unittest`

access.txt acts like a key of yours. It needs to contain two lines of plain text:
* 1st line - Connection string defined for storage account of interest. For example: `DefaultEndpointsProtocol=https;AccountName=your_account_name;AccountKey=your_account_access_key;EndpointSuffix=core.windows.net`. Your storage provider should be able to generate this connection string from account's Access key automatically.
* 2nd line - Plain name of a container from which blobs (notebooks) are going to be fetched.

If you want to add tests, add them to the test folder. Any notebooks or additional files you want to use should be placed in local storages or custom folder on your local machine (e.g. resources inside tests).

###	Software dependencies
For running this API on your own system you need:
    
- Jupyter notebook >= 4.0.0
- Python >= 3.6

## API references

- gast 0.5.2 - https://pypi.org/project/gast/
- beniget - https://github.com/serge-sans-paille/beniget 

## Build and Test
Create a new notebook in the directory of the ```NBlyzer``` by running the command:

```jupyter notebook```

And then in the right top corner click on new and select ```NBlyzer python``` kernel
or run one of the existing notebooks by running the command:

```jupyter notebook "{notebook name}"```

E.g.

```jupyter notebook "Test.ipynb"```

** Warning: be sure to select the ```NBlyzer python``` kernel before executing any commands! **

To apply Code CIA use toolbar buttons placed on the right side.

- To **run code cells** use first from the left **analytics button** or shortcut **CTRL+ALT+ENTER** (to use shortcut you have to be out of edit mode of the cell; press on **ESC** will leave edit mode). Running cell with this 
way includes cell execution plus application of Code CIA on the notebook. Running cells using **SHIFT+ENTER** or clicking on Run button will **not apply** CIA analysis on the notebook. 

- To **set/change analysis type** click the second button from the left. By default none analysis is applied.

- To get suggestion for the **Stale solution** or to switch suggested **path of Safe cells** click the middle button. Suggestion will be shown only if selected analysis is Stale analysis and selected cell is in stale  or
if selected analysis is Safe and at least one Safe path is already shown (this buttons is used to show all options provided by Safe analysis).
If multiple suggestions possible for the one cell in Stale each click on this button will show different solution.

- To **get reasons for stale** use the second button from right. Button will show which identifiers have caused stale if the Stale analysis and cell in stale are selected.

- To switch the depth level of Stale, Safe, and Fresh analysis click on the first button from the right. You can set the number of the depth you want or just set depth level as `inf` which calculates analyses on maximal possible level of the given notebook.

# VS Code Extension
##	Installation process

* Make sure you have [VS Code](https://code.visualstudio.com/) installed on your machine.
* Clone [this repository](https://mdcsincubation.visualstudio.com/NBLyzerVSCode/_git/NBLyzerVSCode).
* Run ```npm install``` to install node_modules

##	Software dependencies

* vscode		[1.61.0]
* glob			[7.1.7]
* mocha			[9.1.1]
* node			[14.x]
* eslint		[7.32.0]
* typescript	[4.4.3]
* test-electron	[1.6.2]

##	API references

* [VS Code API | Visual Studio Code Extension API](https://code.visualstudio.com/api/references/vscode-api)
* [Extension API | Visual Studio Code Extension API](https://code.visualstudio.com/api)
* [Notebook API | Visual Studio Code Extension API](https://code.visualstudio.com/api/extension-guides/notebook)

# Contribute
There are many ways in which you can participate in this project, for example:

- Submit bugs and help us verify fixes
- [Submit pull](https://mdcsincubation.visualstudio.com/NBlyzer/_git/NBlyzer/pullrequests) requests for bug fixes and features and discuss existing proposals
- Make pull requests for anything from typos to additional and new content
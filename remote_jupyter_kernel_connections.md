# Connecting `Atom` or `Vscode` to remote Jupyter Kernels

## Get Jupyter Token

1. Start a python session on eri-gpu.cho.elderresearch.com
2. Log in to Jupyter Lab
3. Open a terminal in Jupyter Lab and type `env`
4. Copy/paste the `JUPYTERTOKEN` environment variable (including `sha1` part)

## Setup Vscode

1. Install the Python [extention](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

2. Configure Vscode to connect to a remote Jupyter Kernel:
[Official Instructions](https://code.visualstudio.com/docs/python/jupyter-support#_connect-to-a-remote-jupyter-server)    

ERI Instructions:   
- Create a Vscode Workspace (typically a `git` repository)
- Open the Vscode Workspace settings (Code --> Preferences --> Settings --> **Workspace Tab**)
- Type "Jupyter Server URI" into the settings search
- Enter the URL: `http://eri-gpu.cho.elderresearch.com:<PORT>/?token=<JUPYTERTOKEN>`

This will create the following file in your workspace `.vscode/settings.json` (shown below). This must be changed each time you start a new session on the GPU box. NOTE! Unless you want to always connect to a remote Jupyter kernel, you should ensure this is only applied to your workspace settings.  
```json
{
    "python.dataScience.jupyterServerURI": "http://eri-gpu.cho.elderresearch.com:<PORT>/?token=<JUPYTERTOKEN>",
    // "python.dataScience.jupyterServerURI": "local",
    "python.pythonPath": "/usr/local/anaconda3/bin/python"
}
```
Note: I keep my "local" kernel commented out so I can easily switch between kernels

4. Open a python script (example below) and use the mouse or Shift + Enter to run python code interactively
```python
#%% Code Cell
import os

# Will print `/home/username/` if properly connected to remote kernel
print(os.getcwd())
```

## Setup Atom

1. install the Hydrogen [extention](https://nteract.gitbooks.io/hydrogen/docs/Installation.html)

2. install the `Ipython` [Kernel](https://nteract.io/kernels)

3. Configure Atom to connect to a remote kernel - [Official Instructions](https://nteract.gitbooks.io/hydrogen/docs/Usage/RemoteKernelConnection.html)

ERI instructions:
- Open Preferences --> Packages --> Click Hydrogen Settings --> Scroll Down to "Kernel Gateways"
- Enter the following into the box:
```
[{
  "name": "GPU Box",
  "options": {
    "baseUrl": "http://eri-gpu.cho.elderresearch.com:<PORT>",
    "token": "<JUPYTERTOKEN>"
  }
}]
```
Note: Jupyter ports on the GPU Box start at 8890 - when you start a container you will be assigned the lowest unused port. For speed, you might consider putting the lowest few ports into the Gateway Configuration instead of having to change the port each time. 

5. Open a python script (example below)
6. Open the Command Palette (Shift + Command/Ctrl + P) and type "Hydrogen: Connect to Remote Kernel"
7. Use [Hydrogen commands](https://nteract.gitbooks.io/hydrogen/docs/Usage/GettingStarted.html) or keyboard shortcuts to run code:
```python
#%% Code Cell
import os

# Will print `/home/username/` if properly connected to remote kernel
print(os.getcwd())
```

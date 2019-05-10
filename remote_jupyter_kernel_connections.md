# Connecting `Atom` or `Vscode` to remote Jupyter Kernels

## Hash Linux Password

Hash your linux password using SHA256. The following Python script will print out your password hash. Save the hash somewhere convenient - this hash will be the same until your Linux password changes. 
```python
# can be run as script or copy/pasted interactively
import getpass
import hashlib

def hash_pwd():
    h = hashlib.new('sha256')
    h.update(getpass.getpass().encode())
    return h.hexdigest()

if __name__ == "__main__":
    print(hash_pwd())
```

## Setup Vscode

1. Install the Python [extention](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

2. Launch a Python session using the [GPU front end](http://eri-gpu.cho.elderresearch.com/)

3. Configure Vscode to connect to a remote Jupyter Kernel - [Official Instructions](https://code.visualstudio.com/docs/python/jupyter-support#_connect-to-a-remote-jupyter-server)    

Alternate remote kernel configuation instructions:   
- Create a Vscode Workspace (typically a `git` repository)
- Open the Vscode Workspace settings (Code --> Preferences --> Settings --> Workspace Tab)
- Type "Python URI" into the settings search
- Enter the URL: `http://eri-gpu.cho.elderresearch.com:<PORT>/?token=<LINUX PASSWORD HASH>`

This will create the following file in your workspace `.vscode/settings.json` that looks like:
```json
{
    "python.dataScience.jupyterServerURI": "http://eri-gpu.cho.elderresearch.com:<PORT>/?token=<LINUX PASSWORD HASH>",
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

3. launch a Python session using the [GPU front end](http://eri-gpu.cho.elderresearch.com/)
https://nteract.gitbooks.io/hydrogen/docs/Usage/RemoteKernelConnection.html

4. Configure Atom to connect to a remote kernel - [Official Instructions](https://nteract.gitbooks.io/hydrogen/docs/Usage/RemoteKernelConnection.html)

Detailed configuration instructions:
- Open Preferences --> Packages --> Click Hydrogen Settings --> Scroll Down to "Kernel Gateways"
- Enter the following into the box:
```
[{
  "name": "GPU Box",
  "options": {
    "baseUrl": "http://eri-gpu.cho.elderresearch.com:<PORT>",
    "token": "<HASHED LINUX PASSWORD>"
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

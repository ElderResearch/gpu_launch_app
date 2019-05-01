# gpu launcher application

the launcher application is a `flask` webapp (defined in `launchapp.py`) which uses the `launch.py` library and the `docker` `python` package to launch `docker` containers and provide users urls to `jupyter notebook` or `rstudio` endpoints

the neighboring `launch.py` file could be used directly from the command line (e.g. to launch a single container). try `python launch.py --help` to see the options. that being said, you usually won't do that -- just use the webapp!

## the webapp

the launcher application is now served by apache and lives in the `/var/www` directory.
after committing/merging changes to the master branch on Github, you will have to pull those changes to the deployment directory and restart the apache service.

1. ssh into the gpu machine.
2. `cd /var/www/gpu_launch_app`
3. `git pull`
4. `sudo service apache2 restart`

the relevant apache2 virtual host config lives at `/etc/apache2/sites-available/gpu_launch_app.conf`

you can view the error log by running `sudo less /var/log/apache2/error.log`

CAUTION: other than running `git pull`, you should never directly edit the files located in `/var/www/gpu_launch_app`!

## development

to enable debugging utilities and server auto-reload functionality, set the `flask` server in development mode and run with the `flask` cli utility.

```sh
$ export FLASK_ENV=development
$ flask run --host 0.0.0.0
```

additionally, you may enter a `flask` shell context environment for simple testing and debugging. the `flask` shell context starts a Python REPL, imports the `db` and `ActivityLog` objects, and exposes the app context.

```sh
$ flask shell
```

in both cases above, the sqlite database will be initialized in-memory and autopopulated with random data. exiting the shell context or stopping the development server will destrpy the ephemeral database.

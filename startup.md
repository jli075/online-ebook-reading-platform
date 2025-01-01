## Set up environment
``` bash
$ python -m venv venv
```

### Windows PowerShell
``` bash
$ venv\Scripts\Activate.ps1
```
### Windows Command Prompt
``` bash
$ venv\Scripts\activate
```

### Windows Git Bash
``` bash
$ source venv/Scripts/activate
```

### Linux Terminal
``` bash
$ source venv/bin/activate
```

### Install Packages
``` bash
$ pip install -r requirements.txt
```


## Run Program 

```bash
$ flask run
```

## Flask Migration Debug
https://github.com/miguelgrinberg/microblog/issues/69
<br>
https://stackoverflow.com/questions/58389621/flask-init-db-no-such-command

Kill current terminal and open new session.
``` bash
$ pip uninstall flask
```

Reactivate venv.
``` bash
$ source venv/Scripts/activate
```

Then you should be able to interact with the flask db.
The db should already be initialized but here are the commands I ran during set up
``` bash
$ flask db init
```
I make no modifications to the `migrations/alembic.ini`. I was unsure what needed to be changed.
``` bash
$ flask db migrate -m "initial migration"
$ flask db upgrade
```



### Flask Tutorials
#### Start here
https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world


#### More Advanced
https://hackersandslackers.com/flask-blueprints/


#### epub javascript
https://github.com/futurepress/epub.js/tree/master



### bootstrap flask
https://bootstrap-flask.readthedocs.io/en/stable/index.html
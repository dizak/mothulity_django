[![Build Status](https://travis-ci.org/dizak/django-mothulity.svg?branch=master)](https://travis-ci.org/dizak/django-mothulity)

# mothulity - web interface

Web Interface and database/job scheduler for [mothulity](https://github.com/dizak/mothulity).

The main principle is to:
1. Present HTML front-end to the user which gathers submission data.
2. Run a separate sched.py script which takes care of reading what was gathered in the database, submits it to [SLURM](https://slurm.schedmd.com/) and watches the submitted process.

django-mothulity stores its settings in the database - there is no need for any modification in the code (including the paths, scheduler and HPC settings) once it is deployed. The settings are bound to the domain name other than ```localhost``` and specified in ```<name_of_project>/settings.py ALLOWED_HOSTS```. Once this is specified, these settings must specified in the Admin Panel. This solution does NOT allow for using more than one domain name - the settings will always bound to first object from the ```ALLOWED_HOSTS``` other than ```localhost```.

## Requirements

- SSH keys exchanged with the HPC.

- The same directory mounted at the Web-Server and the HPC. The first is needed for files upload. The latter for the ssh commands.

## Installation for Production - NGINX and Gunicorn (virtual environment is advised, as always)

These instructions are compliant to [this tutorial at DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-18-04) but with the standard SQL database. Neverthless, is should work with any database backend.

1. Setup the production NGINX server and the Gunicorn WSGI as indicated in the [DigitalOcean tutorial](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-18-04). **From this point it is assumed that**:
  - the django project was created,
  - the SuperUser was created and the Admin Panel works with the production server.

1. ```pip install django-mothulity-*.tar.gz``` - the project will most probably NOT be distributed with the PyPI.

1. Add ```'django.contrib.sites',``` and ```'mothulity',``` to ```<name_of_project>/settings.py INSTALLED_APPS```.

1. It is assumed that ```'localhost'``` and ```'<your.domain.com>'``` are in the ```<name_of_project>/settings.py ALLOWED_HOSTS``` already. If not - add it.

1. Add ```from django.conf.urls import include, url``` to ```<name_of_project>/<name_of_project>/urls.py```.

1. Add ```url(r"^mothulity/", include("mothulity.urls"))``` to ```<name_of_project>/<name_of_project>/urls.py```.

1. ```python manage.py makemigrations mothulity && python manage.py migrate mothulity``` - setup the database.

1. ```python manage.py test mothulity```. - check if everything is all right.

1. In the Admin Panel:

  - Add <your.domain.com> to Sites.

  - Add Path settings and Hpc settings. The default ones should be OK.

Updates of the ```django-mothulity``` app should require nothing more than ```pip install --upgrade django-mothulity-*.tar.gz```.

1. Daemonize ```sched.py```:

  - Create /etc/systemd/system/django-mothulity-scheduler.service file with this content:

  ```bash
  [Unit]
  Description=django-mothulity job scheduler

  [Service]
  User=<username>
  Group=www-data
  ExecStart=/<path-to-virtualenv>/sched.py /<name_of_project>/

  [Install]
  WantedBy=multi-user.target
  ```
  The ```ExecStart``` should point to the ```sched.py``` executable, mind if it is in the virtual environment. It needs the path to the project as an argument - this is hiw it gets the project's settings.

  - ```sudo systemctl start django-mothulity-scheduler``` - start the service.

  - ```sudo systemctl status django-mothulity-scheduler``` - check if everything is all right. If you make changes to the Unit File - run ```sudo systemctl daemon-reload```.

  - ```sudo systemctl enable django-mothulity-scheduler``` - start the service on boot.

**Important**

The scheduler service has to be restarted for the changes to HPC Settings Interval to take place.

## Installation for Development


1. Clone ```dizak/django-mothulity```

1. Run ```pip install -r django-mothulity/requirements.txt```, virtual environment recommended.

1. Type ```django-admin startproject <name_of_project> django-mothulity``` - this will create a Django project **WITHIN** the the cloned repo. This is intended.

1. Add ```'django.contrib.sites',``` and ```mothulity.apps.MothulityConfig``` to ```<name_of_project>/<name_of_project>/settings.py INSTALLED_APPS``` list.

1. Add ```'localhost'``` and ```'<your.domain.com>'``` to ```<name_of_project>/settings.py ALLOWED_HOSTS``` - it is needed for the Path Settings and HPC Settings which are bound to the Site's domain and name. Path Settings and HPC Settings work with only one domain name, other that localhost and are independent of the Site's ID. There is no need for adding the ```SITE_ID``` variable to the ```<name_of_project>/<name_of_project>/settings.py```. See [this documentation](https://docs.djangoproject.com/pl/2.1/ref/contrib/sites/) for more details about the Django's Site framework.

1. Add ```from django.conf.urls import include, url``` to ```<name_of_project>/<name_of_project>/urls.py```.

1. Add ```url(r"^mothulity/", include("mothulity.urls"))``` to ```<name_of_project>/<name_of_project>/urls.py```.

1. Run ```python manage.py makemigrations && python manage.py migrate```.

1. Run ```python manage.py test```.

1. In the Admin Panel:

  - Add <your.domain.com> to Sites.

  - Add Path settings and Hpc settings. The default ones should be OK.

1. Run ```python manage.py runserver```.

  - This starts the development HTTP server.

1. Run ```python sched.py <name_of_project>```

  - This starts the scheduler.

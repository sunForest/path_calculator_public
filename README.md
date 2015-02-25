# Path Calculator

## Introduction
This is a web service for finding the shortest path on a surface with boundary and obstacles

## Build Instruction for LINUX
1. install nginx

   `sudo apt-get install nginx`

2. install Python 2.7 if it is not already installed (not tested for Python 3)

3. install git and pip

   `sudo apt-get install git python-pip`

4. install virtualenv and set up an isolated environment

   This is for a better dependency management, if you are already using Docker or a virtual machine explicitly for this tiny 
   project, feel free to skip this step.  
   `sudo pip install virtualenv`  
   `virtualenv --no-site-packages path.calculator.com`  
   `cd path.calculator.com`  
   `source bin/activate`  
5. install GEOS  
   `wget http://download.osgeo.org/geos/geos-3.3.8.tar.bz2`  
   `tar xjf geos-3.3.8.tar.bz2`  
   `cd geos-3.3.8`  
   `./configure`  
   `make`  
   `sudo make install`  
6. install GDAL  
   `sudo apt-get install binutils libproj-dev gdal-bin`    
7. add the following to your bash profile  
   `export LD_LIBRARY_PATH='/usr/local/lib'`  
   `export GEOS_LIBRARY_PATH='/usr/local/lib/libgeos_c.so'`  
8. clone the git repository  
   `git clone https://github.com/sunForest/path_calculator_public.git`  
9. install the python dependencies  
   `pip install -r requirements.txt`  
10. nginx server configuration  
   /etc/nginx/site-enabled/default:  
  ```
  server {  
    listen 80;  
    server_name YOUR_DOMAIN_NAME;  

    location /static {  
          # change this to your project path  
        alias /home/ubuntu/mySites/path.calculator.com/path_calculator_public/static;  
    }  

    location / {  
        proxy_pass http://localhost:8000;  
    }  
  }
  ```  
11. install gunicorn  
   `pip install gunicorn`  
12. set the secret key as environment variable PATH\_CAL\_SECRET_KEY (to keep it secret...)  
13. get your own [mapbox access token](https://www.mapbox.com/help/create-api-access-token/) and replace the placeholder in /static/js/script.js  
14. start gunicorn  
   `gunicorn convexPath.wsgi:application`  
15. If you want to log out the system without stopping the web server:  
   `^Z`  
   `bg`  
   `disown`  
   `exit`  


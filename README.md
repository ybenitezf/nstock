# nStock

A system for news item management, i mean the pictures, texts, translations,
etc. those bits of info that glued together make the news as you can see on
the newspaper site.

## Install

This is a web2py application. Fallow the instructions on [web2py book](http://web2py.com/books/default/chapter/29/13/deployment-recipes) or for testing purposes download [web2py](http://www.web2py.com/) and clone this repo in the applications folder in your local web2py instance.

## Requirements.

- PIL: you need to install python-pil for image handling.

## First time.

The first time the system is used, the site admin will need to give permissions for some users to be able to create organizations. For that, go to appadmin:

```
http://YOUR.SITE.NAME/nstock/appadmin
```

And give the permission ```create_org``` to the user group.

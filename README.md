# Honeybadger for Python
![Test](https://github.com/honeybadger-io/honeybadger-python/workflows/Test/badge.svg)

When any uncaught exceptions occur, Honeybadger will send the data off to the Honeybadger server specified in your environment.

## Supported Versions

Tested with Python 3.5 - 3.8 against Django latest and LTS releases (1.11.29, 2.2.11, 3.0.4) as well as Flask 1.0 and 1.1.

## Getting Started

Honeybadger for Python works out of the box with Django with only a few configuration options required. The following is a basic setup - more advanced setup will be described later.

### Install Honeybadger

Install honeybadger with pip.

`$ pip install honeybadger`

**Note:** Honeybadger does *not* report errors in development and test
environments by default. To enable reporting in development environments, see
the `force_report_data` setting.

### Django

In a Django application, add the Honeybadger Django middleware to *the top* of your `MIDDLEWARE` config variable:

```python
MIDDLEWARE = [
  'honeybadger.contrib.DjangoHoneybadgerMiddleware',
  ...
]
```

It's important that the Honeybadger middleware is at the top, so that it wraps the entire request process, including all other middlewares.

You'll also need to add a new `HONEYBADGER` config variable to your `settings.py` to specify your API key:

```python
HONEYBADGER = {
  'API_KEY': 'myapikey'
}
```

### Flask

A Flask extension is available for initializing and configuring Honeybadger: `honeybadger.contrib.flask.FlaskHoneybadger`. The extension adds the following information to reported exceptions:

- **url**: The URL the request was sent to.
- **component**: The module that the view is defined at. If the view is a class-based view, then the name of the class is also added.
- **action**: The name of the function called. If the action is defined within a blueprint, then the action name will have the name of the blueprint prefixed.
- **params**: A dictionary containing query parameters and form data. If a variable is defined in both, then the form data are stored. Params are filtered (see [Configuration](#config)).
- **session**: Session data.
- **cgi_data**: Request headers, filtered (see [Configuration](#config)) and request method.

In addition, the `FlaskHoneybadger` extension:
- Configures Honeybadger using Flask's [configuration object](http://flask.pocoo.org/docs/latest/config/#configuration-basics).
- (Optionally) Automatically report exceptions raised during views.
- (Optionally) Reset honeybadger context after each request.

> Note that `FlaskHoneybadger` uses Flask's [signals](http://flask.pocoo.org/docs/latest/signals/) in order to detect exceptions. In
order for the extension to work, you'll have to install the `blinker` library as dependency.

`FlaskHoneybadger` checks Flask's configuration object for automatically configuring honeybadger. In order to configure it, it checks for the
keys with same name as the environment variables in [Configuration](#config) section. Note that if a value is also configured as an environment variable,
then the environment variable's value will be used.

#### Example

```python
from flask import Flask, jsonify, request
from honeybadger.contrib import FlaskHoneybadger

app = Flask(__name__)
app.config['HONEYBADGER_ENVIRONMENT'] = 'development'
app.config['HONEYBADGER_API_KEY'] = '<your key>'
app.config['HONEYBADGER_PARAMS_FILTERS'] = 'password, secret, credit-card'
FlaskHoneybadger(app, report_exceptions=True)

@app.route('/')
def index():
    a = int(request.args.get('a'))
    b = int(request.args.get('b'))

    print('Dividing two numbers {} {}'.format(a, b))
    return jsonify({'result': a / b})

[...]

```

The code above will:

- Initialize honeybadger using Flask's configuration.
- Listen for exceptions.
- Log unhandled exceptions to Honeybadger.
- It will also add `url`, `component`, `action`, `params`, `cgi_data` and context (as generated by context generators) to all errors send using `honeybadger.notify()`.

> `FlaskHoneybadger` will catch exception raised from a view. Note that calls to `abort` method result in an exception being raised. If you don't want this
behavior, you can set `report_exceptions` to False and just call `honeybadger.notify` inside your exception handler.

You can also check more examples under directory `examples`.

#### Component naming in Flask

The following conventions are used for component names:

- When using view functions, the name of the component will be _\<module name>___#___\<view name>_
- For class-based views, the name of the component will be _\<module name>___#___\<class name>_
- When using blueprints, the name of the component will be  _\<module name>___#___\<blueprint name>_._\<view name>_


### AWS Lambda

AWS Lambda environments are auto detected by Honeybadger with no additional configuration.
Here's an example lambda function with Honeybadger:

```python
from honeybadger import honeybadger
honeybadger.configure(api_key='myapikey')

def lambda_handler(event, context):
    """
    A buggy lambda function that tries to perform a zero division
    """
    a = 1
    b = 0

    return (a/b) #This will be reported
```

### ASGI

A generic [ASGI](https://asgi.readthedocs.io/en/latest/) middleware plugin is available for initializing and configuring Honeybadger: [`honeybadger.contrib.asgi`](./honeybadger/contrib/asgi.py).

The general pattern for these cases is wrapping your ASGI application with a middleware:

```python
from honeybadger import contrib

asgi_application = someASGIApplication()
asgi_application = contrib.ASGIHoneybadger(asgi_application)
```

You can pass configuration parameters (or *additional* configuration parameters) as keyword arguments at plugin's initialization:

```python
from honeybadger import contrib

asgi_application = someASGIApplication()
asgi_application = contrib.ASGIHoneybadger(asgi_application, api_key="<your-api-key>", params_filters=["sensible_data"])

```

Or you may want to initialize Honeybadger before your application, and then just registering the plugin/middleware:

```python
from honeybadger import honeybadger, contrib

honeybadger.configure(api_key='<your-api-key>')
some_possibly_failing_function()  # you can track errors happening before your plugin initialization.
asgi_application = someASGIApplication()
asgi_application = contrib.ASGIHoneybadger(asgi_application)
```

### FastAPI

[FastAPI](https://fastapi.tiangolo.com/) is based on Starlette, an ASGI application.
You use Honeybadger's ASGI middleware on these types of applications.

```python

from fastapi import FastAPI
from honeybadger import contrib

app = FastAPI()
app.add_middleware(contrib.ASGIHoneybadger)
```

You can pass additional keyword paramters, too:

```python
from fastapi import FastAPI
from honeybadger import honeybadger, contrib

honeybadger.configure(api_key="<your-api-key>")
app = FastAPI()
app.add_middleware(contrib.ASGIHoneybadger, params_filters=["dont-include-this"])
```

#### FastAPI advanced usage.

Consuming the request body in an ASGI application's middleware is [problematic and discouraged](https://github.com/encode/starlette/issues/495#issuecomment-494008175). This is the reason why request body data won't be sent to the web UI.

FastAPI allows overriding the logic used by the `Request` and `APIRoute` classes, by [using custom `APIRoute` classes](https://fastapi.tiangolo.com/advanced/custom-request-and-route/). This gives more control over the request body, and makes it possible to send request body data along with honeybadger notifications. 

A custom API Route is available at [`honeybadger.contrib.fastapi`](./honeybadger/contrib/fastapi):

```python
from fastapi import FastAPI, APIRouter
from honeybadger import honeybadger
from honeybadger.contrib.fastapi import HoneybadgerRoute

honeybadger.configure(api_key="<your-api-key>")
app = FastAPI()
app.router.route_class = HoneybadgerRoute

router = APIRouter(route_class=HoneybadgerRoute)

```

### Starlette
You can configure Honeybadger to work with [Starlette](https://www.starlette.io/) just like in any other ASGI framework.

```python
from starlette.applications import Starlette
from starlette.middleware import Middleware
from honeybadger import contrib


app = Starlette()
app.add_middleware(contrib.ASGIHoneybadger)
```

### Other frameworks / plain Python app

Django and Flask are the only explicitly supported frameworks at the moment. For other frameworks (tornado, web2py, etc.) or a plain Python script, simply import honeybadger and configure it with your API key. Honeybadger uses a global exception hook to automatically report any uncaught exceptions.

```python
from honeybadger import honeybadger
honeybadger.configure(api_key='myapikey')

raise Exception, "This will get reported!"
```

### All set!

That's it! For additional configuration options, keep reading.

**Note:** By default, honeybadger reports errors in separate threads. For platforms that disallows threading (such as serving a flask/django app with uwsgi and disabling threading), Honeybadger will fail to report errors. You can either enable threading if you have the option, or set `force_sync` config option to `True`. This causes Honeybadger to report errors in a single thread.

## Logging

By default, Honeybadger uses the `logging.NullHandler` for logging so it doesn't make any assumptions about your logging setup. In Django, add a `honeybadger` section to your `LOGGING` config to enable Honeybadger logging. For example:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/path/to/django/debug.log',
        },
    },
    'loggers': {
        'honeybadger': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

For other frameworks or a plain Python script, you can use `logging.dictConfig` or explicitly configure it like so:

```python
import logging
logging.getLogger('honeybadger').addHandler(logging.StreamHandler())
```

### Log Handler
Honeybadger includes a log handler that can be used to report logs of any level via python's logging module.

```python
import logging
from honeybadger.contrib.logger import HoneybadgerHandler

hb_handler = HoneybadgerHandler(api_key='your api key)
logger = logging.getLogger('honeybadger')
logger.addHandler(hb_handler)

try:
  1/0
except:
  logger.error("Something went wrong")
```

or using Dict Config:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'honeybadger': {
            'level': 'ERROR',
            'class': 'honeybadger.contrib.logger.HoneybadgerHandler',
            'api_key': '**YOUR API KEY**',
        },
    },
    'loggers': {
        # root logger
        '': {
            'level': 'WARNING',
            'handlers': ['console', 'honeybadger'],
        },
    },
}
```

## Configuration

To set configuration options, use the `honeybadger.configure` method, like so:

```python
honeybadger.configure(api_key='your api key', environment='production')
```

All of Honeybadger's configuration options can also be set via environment variables with the `HONEYBADGER` prefix (12-factor style). For example, the `api_key` option can be set via the `HONEYBADGER_API_KEY` environment variable.

The following options are available to you:

|  Name | Type | Default | Example | Environment variable |
| ----- | ---- | ------- | ------- | -------------------- |
| api_key | `str` | `""` | `"badgers"` | `HONEYBADGER_API_KEY` |
| project_root | `str` | The current working directory | `"/path/to/project"` | `HONEYBADGER_PROJECT_ROOT` |
| environment | `str` | `"production"` | `"staging"` | `HONEYBADGER_ENVIRONMENT` |
| hostname | `str` | The hostname of the current server. | `"badger01"` | `HONEYBADGER_HOSTNAME` |
| endpoint | `str` | `"https://api.honeybadger.io"` | `"https://honeybadger.example.com/"` | `HONEYBADGER_ENDPOINT` |
| params_filters | `list` | `['password', 'password_confirmation', 'credit_card']` | `['super', 'secret', 'keys']` | `HONEYBADGER_PARAMS_FILTERS` |
| force_report_data | `bool` | `False` | `True` | `HONEYBADGER_FORCE_REPORT_DATA` |
| force_sync | `bool` | `False` | `True` | `HONEYBADGER_FORCE_SYNC` |

## Public Methods

### `honeybadger.set_context`: Set global context data

This method allows you to send additional information to the Honeybadger API to assist in debugging. This method sets global context data and is additive  - eg. every time you call it, it adds to the existing set unless you call `reset_context`, documented below.

#### Examples:

```python
from honeybadger import honeybadger
honeybadger.set_context(my_data='my_value')
```

### `honeybadger.reset_context`: Clear global context data

This method clears the global context dictionary.

#### Examples:

```python
from honeybadger import honeybadger
honeybadger.reset_context()
```

### `honeybadger.context`: Python context manager interface

What if you don't want to set global context data? You can use Python context managers to set case-specific contextual information.

#### Examples:

```python
# from a Django view
from honeybadger import honeybadger
def my_view(request):
  with honeybadger.context(user_email=request.POST.get('user_email', None)):
    form = UserForm(request.POST)
    ...
```

### `honeybadger.configure`: Specify additional configuration options

Allows you to configure honeybadger within your code. Accepts any of the above-listed configuration options as keyword arguments.

#### Example:

```python
honeybadger.configure(api_key='myapikey', project_root='/home/dave/crywolf-django')
```

### `honeybadger.notify`: Send an error notice to Honeybadger

In cases where you'd like to manually send error notices to Honeybadger, this is what you're looking for. You can either pass it an exception as the first argument, or an `error_class`/`error_message` pair of keyword arguments. You can also pass it a custom context dictionary which will get merged with the global context.

#### Examples:

```python
# with an exception
mydict = dict(a=1)
try:
  print mydict['b']
except KeyError, exc:
  honeybadger.notify(exc, context={'foo': 'bar'})

# with custom arguments
honeybadger.notify(error_class='ValueError', error_message='Something bad happened!')
```

## Development

After cloning the repo, run:

```sh
python setup.py develop
```

To run the unit tests:

```sh
python setup.py test
```

## Contributing

If you're adding a new feature, please [submit an issue](https://github.com/honeybadger-io/honeybadger-python/issues/new) as a preliminary step; that way you can be (moderately) sure that your pull request will be accepted.

### To contribute your code:

1. Fork it.
1. Create a topic branch `git checkout -b my_branch`
1. Commit your changes `git commit -am "Boom"`
1. Push to your branch `git push origin my_branch`
1. Send a [pull request](https://github.com/honeybadger-io/honeybadger-python/pulls)

## Changelog

See https://github.com/honeybadger-io/honeybadger-python/blob/master/CHANGELOG.md

## Publishing a release on PyPI

1. Ensure the latest version of twine is installed with `pip install --upgrade twine wheel`
1. Update the version in [honeybadger/version.py](./honeybadger/version.py)
1. Update unreleased heading in [CHANGELOG.md](./CHANGELOG.md)
1. Commit changes with "Release [version]", i.e.: "Release 0.3.0" ([example
   commit](https://github.com/honeybadger-io/honeybadger-python/commit/8e22bdcbc23c74494082cf2521418483a87d59e5))
1. Tag changes: `git tag v[version]`, i.e.: `git tag v0.3.0`
1. Push changes to GitHub: `git push origin master --tags`
1. Clean out the existing dist dir with `rm -rf dist/`
1. Run `python setup.py bdist_wheel` which will build the python2 package in dist/
1. Run `python3 setup.py bdist_wheel` which will build the python3 package in dist/
1. Run `twine upload dist/*` to upload the release to PyPI

## License

This project is MIT licensed. See the [LICENSE](https://github.com/honeybadger-io/honeybadger-python/blob/master/LICENSE) file in this repository for details.

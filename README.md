# Listen to Wikipedia

Real-time visualization and sonification of Wikipedia activity.

Try it out at [https://listen-to-wiki-changes.toolforge.org/](https://listen-to-wiki-changes.toolforge.org/)

## About

*Listen to Wiki Changes* is a refresh of a project originally built by Hatnote,
[Stephen LaPorte](https://github.com/slaporte) and [Mahmoud Hashemi](https://github.com/mahmoud).
Updates were contributed by
[Tajh Taylor](https://gitlab.wikimedia.org/ttaylor),
[Xabriel Collazo](https://gitlab.wikimedia.org/xcollazo), and
[Thomas Chin](https://gitlab.wikimedia.org/tchin).
The original app is hosted at [listen.hatnote.com](http://listen.hatnote.com).

That implementation had some security problems with web sockets, wasn't listening for recent
changes from the [Event Platform EventStreams HTTP Service](https://wikitech.wikimedia.org/wiki/Event_Platform/EventStreams_HTTP_Service).
It also has a limited list of mostly larger Wikipedias to listen to.

This implementation adds a more complete list of wikis, including Wiktionaries, Commons, etc., and 
uses [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) to relay event
data from a Python API.  This allows the browser app to subscribe to specific wikis or languages and only
receive events about those wikis, greatly cutting down on network traffic bandwidth for the end user. 
The event payloads are also smaller than those delivered from the Event Platform service, removing non-essential data.

## Developer setup

There are two apps here: a FastAPI python app in `l2wc/main.py`, and a Vue app in `web_app`.

This app uses [uv](https://docs.astral.sh/uv/) to manage and run the Python app environment.

Unfortunately, Toolforge deployment doesn't support `uv`, so we currently have both a `pyproject.toml`
and a `requirements.txt`.  Both should be kept up to date.

To install the requirements:

    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt

### Run the app in dev mode

To run the API and webapp in dev mode, first build the web app then run the API:

    npm run build
    uv run -- fastapi dev l2wc_api/main.py

or also, if your Python virtual environment is activated:

    fastapi dev l2wc_api/main.py

To run the web app in dev mode: 

    npm run dev

Then you can browse to [http://localhost:5173/app](http://localhost:5173/app). 
Hot reloading in both FastAPI and Vue is supported this way.

### Local dev mode for testing with other devices like mobile phones

To run the API in dev mode, listening to all IPs (including the public IPs):

    uv run -- fastapi dev l2wc_api/main.py  --host 0.0.0.0

The API and UI are configured to allow cross-origin requests, so there shouldn't be any need to configure CORS.

To run the web app in dev mode, it's the same command as before:

    npm run dev

The settings in `vite.config.js` are already set up for Vite to listen to all IPs and allow cross-origin requests.

### Build the app for production

To build the web app:

    npm run build

FastAPI will then serve the built files directly to the browser, so no need for a second process or network port.

### Run the app in production mode

To run FastAPI in production mode:

    uv run -- fastapi run l2wc_api/main.py

or also, if your Python virtual environment is enabled:

    fastapi run l2wc_api/main.py

or in the USGI server, running uvicorn directly:

    uvicorn l2wc_api.main:app --host 0.0.0.0 --port 8000

Then browse to [http://localhost:8000/](http://localhost:8000/). 

The `Procfile` contains instructions on running the app in Toolforge.

### Build the app on the toolforge server

First, ssh to toolforge:

    ssh login.toolforge.org

Become the tool:

    become listen-to-wiki-changes

Stop the webservice, if it is already running :

    toolforge webservice buildservice stop

Build the tool:

    toolforge build start https://gitlab.wikimedia.org/toolforge-repos/listen-to-wiki-changes

Verify the build:

    toolforge build show

Start the service:

    toolforge webservice buildservice start --mount=none  --health-check-path /api/health_check

Stop the webservice:

    toolforge webservice buildservice stop

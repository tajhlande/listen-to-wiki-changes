# Listen to Wikipedia

Real-time visualization and sonification of Wikipedia activity.

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

### Run the app in dev mode

To run the API in dev mode: 

    uv run -- fastapi dev l2wc_api/main.py

or also, if your Python virtual environment is activated:

    fastapi dev l2wc_api/main.py

To run the web app in dev mode: 

    cd web_app
    npm run dev

Then you can browse to [http://localhost:5173/app](http://localhost:5173/app). 
Hot reloading in both FastAPI and Vue is supported this way.

### Build the app for production

To build the web app:

    cd web_app
    npm run build

FastAPI will then serve the built files directly to the browser, so no need for a second port.

### Run the app in production

To run FastAPI in production mode:

    uv run -- fastapi run l2wc_api/main.py

or also, if your Python virtual environment is enabled:

    fastapi run l2wc_api/main.py

or in the USGI server, running uvicorn directly:

    uvicorn l2wc_api.main:app --host 0.0.0.0 --port 8000

Then browse to [http://localhost:8000/](http://localhost:8000/). 

The `Procfile` contains instructions on running the app in Toolforge.



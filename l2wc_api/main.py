import asyncio
import html
import json
import sys

from contextlib import asynccontextmanager
from logging import Logger, StreamHandler, Formatter
from typing import Any, AsyncGenerator, Optional, Set
from uuid import uuid4

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from httpx import AsyncClient, get as httpx_get
from httpx_sse import aconnect_sse

WIKI_LIST_URL = "https://wikistats.wmcloud.org/wikimedias_csv.php"
WIKI_EVENT_STREAM_URL = "https://stream.wikimedia.org/v2/stream/recentchange"
CLIENT_HEADERS = {'User-Agent': 'listen-to-wiki-changes/0.0 (https://listen-to-wiki-changes.toolforge.org/; ttaylor@wikimedia.org)'}
EVENT_QUEUE_SIZE = 100
KNOWN_EVENT_SCHEMA = "/mediawiki/recentchange/1.0.0" # we will watch for this in case it changes
# The schema is documented at this URL:
# https://gitlab.wikimedia.org/repos/data-engineering/schemas-event-primary/-/blob/master/jsonschema/mediawiki/recentchange/current.yaml?ref_type=heads

# Wikis with names that don't follow conventions
SPECIAL_WIKIS = {
    "www.wikidata.org": ("wikidata", "Wikidata"),
    "www.mediawiki.org": ("mediawiki", "MediaWiki"),
    "commons.wikimedia.org": ("commons", "Commons Wiki"),
    "species.wikimedia.org": ("species", "WikiSpecies"),
    "incubator.wikimedia.org": ("incubator", "Wiki Incubator"),
    "meta.wikimedia.org": ("meta", "Meta Wiki"),
    "nostalgia.wikipedia.org": ("nostalgia", "Nostalgia Wiki"),
    "outreach.wikimedia.org": ("outreach", "Outreach Wiki"),
    "test.wikipedia.org": ("test", "Test Wiki"),
    "test.wikidata.org": ("testwikidata", "Test Wikidata"),
    "wikitech.wikimedia.org": ("wikitech", "WikiTech"),
    "strategy.wikimedia.org": ("strategy", "Strategy Wiki"),
    "foundation.wikimedia.org": ("foundation", "Foundation Wiki"),
    "usability.wikimedia.org": ("usability", "Usability Wiki"),
    "thankyou.wikipedia.org": ("thankyou", "Thank You Wiki"),
    "quality.wikimedia.org": ("quality", "Quality Wiki"),
}

logger: Logger = Logger(__name__)
logger.setLevel("DEBUG")

# this stuff ensures our logging gets displayed by the FastAPI app
stream_handler = StreamHandler(sys.stdout)
log_formatter = Formatter("%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s")
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

logger.info('API is starting up')

wiki_list_columns: list[str] = [] # the column names from the wikistats wiki list file, in order.
wiki_types: dict[ str, dict[str, str]] = {} # a list of all the wiki types
wiki_list: list[dict] = [] # all the wiki metadata dicts
wiki_dict: dict[str, dict] = {} # lang code -> wiki metadata dict
language_dict: dict[str, dict[str, Any]] = {} # lang code -> { lang_code: language code, en_name: English language name, local_name: local language name}
wiki_host_index: dict[str, str] = {} # server name -> wiki code

event_relay_loop_task = None

# Connection state management for conditional connection to event stream
stream_active = False
stream_control_event = asyncio.Event()
DISCONNECT_GRACE_PERIOD = 30  # seconds to wait before disconnecting when no subscribers


@asynccontextmanager
async def fastapi_lifespan(fastapi_app: FastAPI):
    """
    Create shared state variables when the application starts
    :param fastapi_app: the FastAPI app
    :return: nothin'
    """
    # Application startup activities
    logger.info("Starting up...")
    load_wikis_list()

    logger.debug("Starting SSE event relay loop task...")
    global event_relay_loop_task
    event_relay_loop_task = asyncio.create_task(edit_event_relay_loop())

    #let the application run
    logger.info("Startup complete.")
    yield

    # Application shutdown activities
    global active_subscribers
    for queue in list(active_subscribers):
        active_subscribers.remove(queue)
    if event_relay_loop_task:
        logger.debug("Shutting down SSE event relay loop task...")
        event_relay_loop_task.cancel()
        try:
            await event_relay_loop_task
        except asyncio.CancelledError:
            logger.info("Event relay task cleanly shutdown.")

    pass


app = FastAPI(title="listen-to-wiki-changes", lifespan=fastapi_lifespan)

app.mount("/app", StaticFiles(directory="web_app/dist", html=True), name="static")

allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return RedirectResponse("/app")


def load_wikis_list():
    """
    Load the wiki metadata list from the wikistats wiki list file.
    """
    logger.info("Loading wikis list...")
    response = httpx_get(WIKI_LIST_URL, headers=CLIENT_HEADERS)
    wiki_list.clear()
    wiki_types.clear()
    wiki_types['special'] = { 'wikiType': 'special' } # because they are indeed special
    wiki_dict.clear()
    wiki_host_index.clear()
    language_dict.clear()
    wiki_list_columns.clear()
    wiki_count = 0
    for line in response.text.splitlines():
        if line.startswith("rank"):
            # header row
            wiki_list_columns.extend(line.split(','))
        else:
            # hack to fix HTML encoding in response
            line = html.unescape(line)
            wiki_count = wiki_count + 1
            try:
                wiki_metadata = dict(zip(wiki_list_columns, line.split(',')))
                wiki_metadata['lang_code'] = 'multi' # until proven otherwise

                wiki_type = wiki_metadata['type'] if 'type' in wiki_metadata.keys() else None
                if wiki_type and not wiki_type.isdigit():
                    # the list will have an entry for every line in the retrieved data, including things we don't index
                    wiki_list.append(wiki_metadata)
                    wiki_type = wiki_metadata['type']
                    prefix = wiki_metadata['prefix']
                    if wiki_type == 'special':
                        prefix_split = prefix.split('.')
                        special_name = "NOT_SPECIAL"
                        if prefix in SPECIAL_WIKIS.keys():
                            special_name = SPECIAL_WIKIS[prefix][0]
                            wiki_metadata['code'] = special_name
                            wiki_metadata['display_name'] = SPECIAL_WIKIS[prefix][1]
                            wiki_dict[special_name] = wiki_metadata
                            wiki_host_index[prefix] = special_name
                        elif prefix.startswith('www.') and 'wikimedia' in prefix and len(prefix_split) == 3 and prefix_split[0].strip():
                            # maybe a language code as a TLD CC
                            special_name = prefix_split[-1] + "_wikimedia"
                            wiki_metadata['code'] = special_name
                            wiki_metadata['display_name'] = special_name.capitalize()
                            wiki_dict[special_name] = wiki_metadata
                            wiki_host_index[prefix] = special_name
                        elif prefix.endswith('.org') and 'wikimedia' in prefix and len(prefix_split) == 3 and prefix_split[0].strip():
                            # probably a language code as the host name prefix
                            special_name = prefix_split[0] +  "_wikimedia"
                            wiki_metadata['code'] = special_name
                            wiki_metadata['display_name'] = special_name.capitalize()
                            wiki_dict[special_name] = wiki_metadata
                            wiki_host_index[prefix] = special_name
                        if special_name == "NOT_SPECIAL":
                            logger.warning(f"Unable to determine wiki name for special wiki: {wiki_metadata}")

                        # we will skip any special wiki that doesn't match any of these
                        #logger.warning(f"Not indexing wiki: {wiki_metadata}")


                    else:
                        # record the language short code for non-special wikis if one is present
                        if prefix:
                            if prefix in language_dict:
                                pass
                            if prefix in language_dict and language_dict[prefix]['enName'] != wiki_metadata['language']:
                                logger.warning(f"Duplicate language code found for code {prefix}: "
                                               f"recorded '{language_dict[prefix]['enName']}', skipping '{wiki_metadata['language']}'")
                            else:
                                language_dict[prefix] = {
                                    'langCode': prefix,
                                    'enName': wiki_metadata['language'],
                                    'localName': wiki_metadata['loclang']
                                }
                            wiki_metadata['langCode'] = wiki_metadata['prefix']

                        # index the wiki by wiki_code
                        if wiki_type not in wiki_types:
                            logger.debug(f"Adding wiki type {wiki_type} to list of wiki types")
                        wiki_types[wiki_type] = { 'wikiType': wiki_type }
                        wiki_code = prefix + "_" + wiki_type
                        wiki_metadata['code'] = wiki_code
                        wiki_metadata['display_name'] = wiki_metadata['language'] + " " + wiki_metadata['type'].capitalize()
                        wiki_dict[wiki_code] = wiki_metadata
                        wiki_host_index[prefix + "." + wiki_type + ".org"] = wiki_code # a terrible hack but ...
                else:
                    logger.warning(f"Skipping wiki with missing or invalid type: {wiki_metadata}")

            except Exception:
                logger.exception(f"Error processing line({wiki_count}): {line}")

    # manually add wikidata and test wikidata because they aren't in the remote list for some reason
    wiki_code = 'wikidata'
    wiki_metadata = {'type': 'special', 'lang_code': 'multi', 'code': wiki_code, 'display_name': 'Wikidata'}
    wiki_dict[wiki_code] = wiki_metadata
    wiki_host_index['www.wikidata.org'] = wiki_code
    wiki_list.append(wiki_metadata)

    wiki_code = 'testwikidata'
    wiki_metadata = {'type': 'special', 'lang_code': 'multi', 'code': wiki_code, 'display_name': 'Test Wikidata'}
    wiki_dict[wiki_code] = wiki_metadata
    wiki_host_index['test.wikidata.org'] = wiki_code
    wiki_list.append(wiki_metadata)

    # finished. info and debug logging
    logger.info(f"Finished loading wiki list. Processed {wiki_count} data rows.")
    logger.debug(f"Found {len(wiki_types)} wiki types: {list(wiki_types)}")
    logger.debug(f"Found {len(language_dict)} languages")
    logger.debug(f"Found {len(wiki_list)} wikis listed")
    logger.debug(f"Indexed {len(wiki_dict)} wikis")


@app.get("/api/wikis/")
async def get_wikis():
    """
    Get a list of all the wikis, indexed by code
    :return: JSON object with keys as each wiki code, and values as a metadata object for that wiki
    """
    return {
        "wikis": wiki_dict,
    }


@app.get("/api/wiki_codes")
async def get_wiki_codes():
    """
    Get a list of all the wiki codes
    :return: a JSON array containing dicts that contain wiki code and display name for each wiki
    """
    return  [{ 'wikiCode': wc, 'displayName': wiki_dict[wc]['display_name'] } for wc in wiki_dict.keys()]


@app.get("/api/wiki/{wiki_code}")
async def get_wiki(wiki_code: str):
    """
    Get the metadata object for a wiki by its code
    :param wiki_code: The wiki code, e.g. "en_wikipedia" or "commons"
    :return: A metadata object for the wiki, or a 404 if the wiki code is not found.
    """
    wiki_metadata = wiki_dict.get(wiki_code)
    if wiki_metadata is None:
        raise HTTPException(status_code=404, detail="Wiki not found")
    return wiki_metadata


@app.get("/api/types")
async def get_wiki_types():
    """
    Get a list of all the wiki types
    :return: a JSON array containing a list of wiki type dicts
    """
    return [ wiki_types[wt] for wt in wiki_types.keys() ]


@app.get("/api/languages")
async def get_wiki_languages():
    """
    Get a list of all the languages
    :return: a JSON array containing dicts of language code, English language name and local language name
    """
    return [ language_dict[lc] for lc in language_dict.keys()]


class EvictingQueue(asyncio.Queue):
    """
    Custom queue (ring buffer, really) that evicts the oldest message when full.
    Relies on the implementation of Dict to use the global interpreter lock to be thread-safe.
    see https://wiki.python.org/moin/GlobalInterpreterLock for when this might or might not be true.
    """
    def __init__(self, maxsize=EVENT_QUEUE_SIZE):
        super().__init__(maxsize)

    def put_nowait(self, item):
        if self.full():
            try:
                self.get_nowait()
            except asyncio.QueueEmpty:
                pass
        super().put_nowait(item)


# Global subscriber registry
active_subscribers: Set[EvictingQueue] = set()


def compute_length_change(raw_event):
    length_obj = raw_event.get('length', 'no_length')
    if length_obj == 'no_length':
        return 0

    new_length = length_obj.get('new', 0)
    old_length = length_obj.get('old', 0)
    return new_length - old_length


def refine_event(raw_event):
    """
    Given a raw event body from httpx, slim it down to the essential elements needed to do the audio-visualization
    :param raw_event: The raw event from httpx
    :return: a refined event object, basically a nested tree of dicts that FastAPI can easily transform to JSON
    """
    try:
        refined_event = {
            "id": raw_event.get('id', uuid4()), # not sure if this matters except that Vue wants it to be unique
            "domain": raw_event['meta']['domain'] if 'meta' in raw_event and 'domain'in raw_event['meta'] else "",
            "wiki_type": "", # we don't know yet
            "event_type": "unknown", # we don't know yet
            "code": "", # we don't know yet
            "language": "", # we don't know yet
            "title": raw_event['title'] if 'title' in raw_event else "",
            "title_url": raw_event['title_url'] if 'title_url' in raw_event else "",
            "timestamp": raw_event['timestamp'] if 'timestamp' in raw_event else "",
            "user": raw_event['user'] if 'user' in raw_event else "",
            "bot": raw_event['bot'] if 'bot' in raw_event else "",
            "change_in_length": compute_length_change(raw_event),
        }
    except Exception:
        logger.exception(f"Error processing raw event: {raw_event}")
        raise

    if raw_event['meta']['domain'] in wiki_host_index.keys():
        try:
            wiki_code = wiki_host_index[raw_event['meta']['domain']]
            wiki = wiki_dict[wiki_code]
            refined_event['code'] = wiki_code
            refined_event['wiki_type'] = wiki['type'] if 'type' in wiki else None
            refined_event['language'] = wiki['language'] if 'language' in wiki else 'multi' # a strong assumption
        except Exception:
            logger.exception(f"Error enriching refined event: {raw_event}")

    # see if they are "new page" or "new user" events
    if raw_event['type'] == 'log' and raw_event['log_type'] and raw_event['log_type'] == 'newusers':
        refined_event['event_type'] = 'new_user'
    elif raw_event['type'] == 'new':
        refined_event['event_type'] = 'new_page'
    elif raw_event['type'] == 'edit':
        refined_event['event_type'] = 'edit'

    return refined_event


async def filter_pass(refined_event, requested_codes, requested_types, requested_langs) -> bool:
    """
    Given a refined event, determine whether the event matches the requested filters. They are inclusive only.
    :return: True if the event matches the filters, False otherwise.
    """
    # logger.debug(f"Code: '{refined_event['code']}', requested codes: {requested_codes}, "
    #              f"Type: '{refined_event['type']}', requested types: {requested_types}, "
    #              f"Language: '{refined_event['language']}', requested languages: {requested_langs}")
    try:
        return (refined_event['code'] in requested_codes or
            refined_event['wiki_type'] in requested_types or
            refined_event['language'] in requested_langs)
    except Exception:
        logger.error(f"Error filtering refined event: {refined_event}")
        raise


async def edit_event_relay_loop():
    """
    Background task: connect to the event stream when there are subscribers,
    disconnect when no subscribers are present (after grace period).
    :return:
    """
    logger.info("Starting SSE edit event relay loop...")
    global active_subscribers, stream_active, stream_control_event

    while True:
        # Wait for first subscriber before connecting
        await stream_control_event.wait()
        stream_control_event.clear()

        if not active_subscribers:
            # Event was cleared before we processed it, or all subscribers left
            logger.debug("Stream control event cleared, no subscribers to serve.")
            continue

        logger.info("Starting async streaming client")
        global stream_active
        stream_active = True

        try:
            async with AsyncClient(timeout=None) as streaming_client:
                async with aconnect_sse(streaming_client, "GET", WIKI_EVENT_STREAM_URL, headers=CLIENT_HEADERS) as event_source:
                    logger.info("Connected to wiki event stream")

                    # Create iterator once before the loop
                    sse_iterator = event_source.aiter_sse()

                    # Process events while we have subscribers
                    while active_subscribers:
                        try:
                            # Use asyncio.wait_for to allow checking subscriber count periodically
                            sse_event = await asyncio.wait_for(
                                sse_iterator.__anext__(),
                                timeout=5.0
                            )
                        except asyncio.TimeoutError:
                            # Timeout allows us to check subscriber count periodically
                            continue
                        except StopAsyncIteration:
                            logger.warning("Event stream ended unexpectedly")
                            break

                        try:
                            raw_event = json.loads(sse_event.data)
                            # fast-filter events that aren't edits or new pages in namespace 0, or new users
                            re_type = raw_event['type']
                            ns = raw_event['namespace']
                            if not ((re_type == 'edit' and ns is 0) or
                                    (re_type == 'log' and raw_event['log_type'] == 'newusers') or
                                    (re_type == 'new' and ns is 0)):
                                continue
                        except:
                            continue  # if the event doesn't have parseable JSON data or a namespace, skip it.

                        refined_event = refine_event(raw_event)
                        if refined_event['event_type'] == 'unknown':
                            continue

                        for queue in list(active_subscribers):
                            try:
                                queue.put_nowait(refined_event)
                            except Exception:
                                pass

            logger.warning("Async streaming client ended stream")

        except asyncio.CancelledError:
            logger.info("Relay loop received and handled cancel signal.")
            stream_active = False
            raise
        except Exception as e:
            logger.exception(f"Async streaming client crashed: {e}")
        finally:
            stream_active = False
            logger.info("Stream disconnected, waiting for subscribers...")

            # Wait for grace period or new subscriber before attempting reconnection
            if not active_subscribers:
                try:
                    await asyncio.wait_for(
                        stream_control_event.wait(),
                        timeout=DISCONNECT_GRACE_PERIOD
                    )
                    # New subscriber arrived within grace period, clear event and continue
                    stream_control_event.clear()
                except asyncio.TimeoutError:
                    # Grace period expired, stay in waiting state
                    logger.debug("Grace period expired, staying disconnected")


async def filtered_event_generator(codes: list[str], types: list[str], langs: list[str]) -> AsyncGenerator[str, None]:
    """
    Each connecting client gets a separate filtered event generator.
    :return: A generator that yields refined events as they are received from the event stream, filtered to the
             given parameters.
    """
    queue = EvictingQueue(maxsize=EVENT_QUEUE_SIZE)
    global active_subscribers, stream_control_event

    # Signal relay loop if this is the first subscriber
    was_empty = len(active_subscribers) == 0
    active_subscribers.add(queue)

    if was_empty:
        logger.info("First subscriber connected, signaling relay loop to connect")
        stream_control_event.set()
    else:
        logger.info(f"New client connected. Total subscribers: {len(active_subscribers)}")

    language_names = [language_dict[lang_code]['enName'] for lang_code in langs]
    try:
        while True:
            try:
                # Wait for a new event with timeout
                refined_event = await asyncio.wait_for(queue.get(), timeout=15.0)
                if await filter_pass(refined_event, codes, types, language_names):
                    yield f"event: wiki_event\ndata: {json.dumps(refined_event)}\n\n"
                    await asyncio.sleep(0)
            except asyncio.TimeoutError:
                # No events for a while, send keep-alive
                yield ": keep-alive\n\n"
                await asyncio.sleep(0)
    finally:
        active_subscribers.remove(queue)
        remaining = len(active_subscribers)

        # Signal relay loop if this was the last subscriber
        if remaining == 0:
            logger.info("Last subscriber disconnected, signaling relay loop")
            stream_control_event.set()
        else:
            logger.info(f"Client disconnected. Remaining: {remaining}")


@app.get("/api/events/")
async def read_events(
        wiki_codes_str: Optional[str] = Query(None, alias="codes"),
        wiki_types_str: Optional[str] = Query(None, alias="types"),
        wiki_langs_str: Optional[str] = Query(None, alias="languages"),
):
    """
    Given the requested lists of desired wiki codes, types, and/or languages, return a filtered event stream
    of matching recent changes events.
    :param wiki_codes_str: optionally, a comma separated list of wiki codes
    :param wiki_types_str: optionally, a comma separated list of wiki types
    :param wiki_langs_str: optionally, a comma separated list of wiki language codes
    :return: an event stream with content type "text/event-stream" containing the requested events
    """
    logger.debug(f"Incoming event stream request with filters: {wiki_codes_str}; {wiki_types_str}; {wiki_langs_str}")
    if not wiki_codes_str and not wiki_types_str and not wiki_langs_str:
        raise HTTPException(
            status_code=400,
            detail="At least one filter must be specified: codes, types, or languages",
        )

    requested_codes = wiki_codes_str.split(",") if wiki_codes_str else []
    requested_types = wiki_types_str.split(",") if wiki_types_str else []
    requested_langs = wiki_langs_str.split(",") if wiki_langs_str else []

    return StreamingResponse(
        filtered_event_generator(requested_codes, requested_types, requested_langs),
        media_type="text/event-stream",
    )

@app.get("/api/health_check")
async def run_health_check():
    """
    Health check monitoring endpoint. Return HTTP OK (200) if all is well, or some other HTTP error code if not.
    :return: a single event, whatever the next event is across all wikis.
    """
    return await anext(filtered_event_generator([], list(wiki_types.keys()), []))


@app.get("/api/stream_status")
async def get_stream_status():
    """
    Get the current status of the wiki event stream connection.
    :return: JSON object with stream connection status and subscriber count.
    """
    global stream_active, active_subscribers
    return {
        "stream_connected": stream_active,
        "active_subscribers": len(active_subscribers),
    }


def main():
    """
    If for some reason someone tries to run this module directly, tell them what to do
    """
    print("Run in dev with: uv run -- fastapi dev main.py\n"
          "Run in prod with: source .venv/bin/activate; python -m fastapi run main.py\n"
          "Or, alternatively: uvicorn l2wc_api.main:app --host 0.0.0.0 --port 8000"
          )


if __name__ == "__main__":
    main()

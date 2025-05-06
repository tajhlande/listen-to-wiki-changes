import asyncio
import html
import json
import sys

from contextlib import asynccontextmanager
from logging import Logger, StreamHandler, Formatter
from typing import AsyncGenerator, Optional, Set

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from httpx import AsyncClient, get as httpx_get
from httpx_sse import aconnect_sse

WIKI_LIST_URL = "https://wikistats.wmcloud.org/wikimedias_csv.php"
WIKI_EVENT_STREAM_URL = "https://stream.wikimedia.org/v2/stream/recentchange"
EVENT_QUEUE_SIZE = 100
KNOWN_EVENT_SCHEMA = "/mediawiki/recentchange/1.0.0" # we will watch for this in case it changes
# The schema is documented at this URL:
# https://gitlab.wikimedia.org/repos/data-engineering/schemas-event-primary/-/blob/master/jsonschema/mediawiki/recentchange/current.yaml?ref_type=heads

# Wikis with names that don't follow conventions
SPECIAL_WIKIS = {
    "www.mediawiki.org": ("mediawiki", "MediaWiki"),
    "commons.wikimedia.org": ("commons", "Commons Wiki"),
    "species.wikimedia.org": ("species", "WikiSpecies"),
    "incubator.wikimedia.org": ("incubator", "Wiki Incubator"),
    "meta.wikimedia.org": ("meta", "Meta Wiki"),
    "nostalgia.wikipedia.org": ("nostalgia", "Nostalgia Wiki"),
    "outreach.wikimedia.org": ("outreach", "Outreach Wiki"),
    "test.wikipedia.org": ("test", "Test Wiki"),
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
wiki_types: set[str] = set() # a set of all the wiki types
wiki_list: list[dict] = [] # all the wiki metadata dicts
wiki_dict: dict[str, dict] = {} # lang code -> wiki metadata dict
language_dict: dict[str, tuple[str, str]] = {} # lang code -> (English language name, local language name)
wiki_host_index: dict[str, str] = {} # server name -> wiki code

event_relay_loop_task = None


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
    event_relay_loop_task = asyncio.create_task(event_relay_loop())

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

@app.get("/")
async def read_root():
    return RedirectResponse("/app")

# @app.get("/")
# async def read_root():
#     """
#     Placeholder method. this should eventually return the index of the Vue app.
#     :return:
#     """
#     global wiki_dict
#     assert len(wiki_dict.keys()) > 0, "Wiki dictionary is empty"
#     return {"Hello": "World"}


def load_wikis_list():
    """
    Load the wiki metadata list from the wikistats wiki list file.
    """
    logger.info("Loading wikis list...")
    response = httpx_get(WIKI_LIST_URL)
    wiki_list.clear()
    wiki_types.clear()
    wiki_types.add("special") # because they are indeed special
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
                # logger.debug(f"Processing line({wiki_count}): {line}")
                wiki_metadata = dict(zip(wiki_list_columns, line.split(',')))
                wiki_metadata['lang_code'] = 'multi' # until proven otherwise

                wiki_type = wiki_metadata['type']
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
                            logger.warning(f"Odd special name {special_name} generated for wiki {wiki_metadata}")

                        # we will skip any special wiki that doesn't match any of these
                        #logger.warning(f"Not indexing wiki: {wiki_metadata}")


                    else:
                        # record the language short code for non-special wikis if one is present
                        if prefix:
                            if prefix in language_dict:
                                pass
                                #logger.debug(f"Language dict entry for prefix {prefix}: {language_dict[prefix]}")
                            if prefix in language_dict and language_dict[prefix][0] != wiki_metadata['language']:
                                logger.warning(f"Duplicate language code found for code {prefix}: "
                                               f"was {language_dict[prefix][0]}, now {wiki_metadata['language']}")
                            else:
                                language_dict[wiki_metadata['prefix']] = (wiki_metadata['language'], wiki_metadata['loclang'])
                            wiki_metadata['lang_code'] = wiki_metadata['prefix']

                        # index the wiki by wiki_code
                        #logger.debug(f"Adding wiki {wiki_type}")
                        if wiki_type not in wiki_types:
                            logger.debug(f"Adding wiki type {wiki_type} to list of wiki types")
                        wiki_types.add(wiki_type)
                        wiki_code = prefix + "_" + wiki_type
                        wiki_metadata['code'] = wiki_code
                        wiki_metadata['display_name'] = wiki_metadata['language'] + " " + wiki_metadata['type'].capitalize()
                        wiki_dict[wiki_code] = wiki_metadata
                        wiki_host_index[prefix + "." + wiki_type + ".org"] = wiki_code # a terrible hack but ...
                        #logger.debug(f"Added wiki {wiki_code}")
            except Exception:
                logger.exception(f"Error processing line({wiki_count}): {line}")


    # debug logging
    logger.info(f"Finished loading wiki list. Processed {wiki_count} data rows.")
    logger.debug(f"Found {len(wiki_types)} wiki types: {list(wiki_types)}")
    logger.debug(f"Found {len(language_dict)} languages")
    logger.debug(f"Found {len(wiki_list)} wikis listed")
    logger.debug(f"Indexed {len(wiki_dict)} wikis")
    #logger.debug(f"Sample Language dict ({len(language_dict)}): {dict(itertools.islice(language_dict.items(), 10))}")
    #logger.debug(f"Sample Wiki dict ({len(wiki_dict)}): {dict(itertools.islice(wiki_dict.items(), 10))}")
    #logger.debug(f"Wiki list ({wiki_count}): {wiki_list}")


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
    :return: a JSON object containing a key for each wiki code that maps to a display name for that wiki code
    """
    return {
        "wiki_codes": {wc: wiki_dict[wc]['display_name'] for wc in wiki_dict.keys()} #wiki_dict.keys(),
    }


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
    :return: a JSON object containing a list of wiki types, e.g. ["wikipedia", "wiktionary", "special"]
    """
    return {
        "types": wiki_types,
    }


@app.get("/api/languages")
async def get_wiki_languages():
    """
    Get a list of all the languages, indexed by language code
    :return: a JSON object containing a key for each language code that maps to a tuple of English language name and
             local language name
    """
    return {
        "languages": language_dict,
    }


class EvictingQueue(asyncio.Queue):
    """
    Custom queue (ring buffer, really) that evicts the oldest message when full.
    Relies on the implementation of Set to use the global interpreter lock to be thread-safe.
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


def refine_event(raw_event):
    """
    Given a raw event body from httpx, slim it down to the essential elements needed to do the audio-visualization
    :param raw_event: The raw event from httpx
    :return: a refined event object, basically a nested tree of dicts that FastAPI can easily transform to JSON
    """
    try:
        refined_event = {
            "id": raw_event['id'] or "",
            "domain": raw_event['meta']['domain'] or "",
            "type": raw_event['type'] or "",
            "code": "", # we don't know yet
            "language": "", # we don't know yet
            "title": raw_event['title'] or "",
            "title_url": raw_event['title_url'] or "",
            "timestamp": raw_event['timestamp'] or "",
            "user": raw_event['user'] or "",
            "bot": raw_event['bot'] or "",
            "change_in_length": raw_event['length']['new'] - raw_event['length']['old'] or "",
        }
    except Exception:
        logger.exception(f"Error processing raw event: {raw_event}")
        raise

    if raw_event['meta']['domain'] in wiki_host_index.keys():
        wiki_code = wiki_host_index[raw_event['meta']['domain']]
        wiki = wiki_dict[wiki_code]
        refined_event['code'] = wiki_code
        refined_event['type'] = wiki['type']
        refined_event['language'] = wiki['lang_code']

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
            refined_event['type'] in requested_types or
            refined_event['language'] in requested_langs)
    except Exception:
        logger.error(f"Error filtering refined event: {refined_event}")
        raise


async def event_relay_loop():
    """
    Background task: connect once to the event stream and queue events to all subscribers
    :return:
    """
    logger.info("Starting SSE event relay loop...")
    global active_subscribers
    try:
        async with AsyncClient(timeout=None) as streaming_client:
            async with aconnect_sse(streaming_client, "GET", WIKI_EVENT_STREAM_URL) as event_source:
                async for sse_event in event_source.aiter_sse():
                    # look for only namespace 0 for now
                    try:
                        raw_event = json.loads(sse_event.data)
                        if raw_event['namespace'] != 0: # only main page namespace stuff
                            continue
                        if raw_event['type'] != 'edit': # only edits for now
                            continue
                    except:
                        continue # if for some reason the event doesn't have parseable json data or a namespace, skip it.
                    #logger.debug(f"Raw event['namespace']: '{raw_event['namespace']}'. type: '{type(raw_event['namespace'])}''")

                    # logger.debug(f"Received raw event: {raw_event}")

                    refined_event = refine_event(raw_event)

                    for queue in list(active_subscribers):
                        try:
                            queue.put_nowait(refined_event)
                        except Exception:
                            pass

    except asyncio.CancelledError:
        logger.info("Relay loop received and handled cancel signal.")
        raise
    except Exception as e:
        logger.exception(f"Relay loop crashed: {e}")
        # TODO Should we restart relay loop task?  depends on what the exception is.


async def filtered_event_generator(codes: list[str], types: list[str], langs: list[str]) -> AsyncGenerator[str, None]:
    """
    Each connecting client gets a separate filtered event generator.
    :return: A generator that yields refined events as they are received from the event stream, filtered to the
             given parameters.
    """
    queue = EvictingQueue(maxsize=EVENT_QUEUE_SIZE)
    global active_subscribers
    active_subscribers.add(queue)
    logger.info(f"New client connected. Total subscribers: {len(active_subscribers)}")
    try:
        while True:
            try:
                # Wait for a new event with timeout
                refined_event = await asyncio.wait_for(queue.get(), timeout=15.0)
                if await filter_pass(refined_event, codes, types, langs):
                    yield f"event: wiki_event\ndata: {refined_event}\n\n"
            except asyncio.TimeoutError:
                # No events for a while, send keep-alive
                yield ": keep-alive\n\n"
    finally:
        active_subscribers.remove(queue)
        logger.info(f"Client disconnected. Remaining: {len(active_subscribers)}")


@app.get("/api/events/")
async def read_events(
        wiki_codes_str: Optional[str] = Query(None, alias="codes"),
        wiki_types_str: Optional[str] = Query(None, alias="types"),
        wiki_langs_str: Optional[str] = Query(None, alias="languages"),
):
    """
    Given the requested lists of desired wiki codes, types, and/or languages, return a filtered event stream
    of matching recent changes events.
    :param wiki_codes_str:
    :param wiki_types_str:
    :param wiki_langs_str:
    :return: an event stream with content type "text/event-stream" containing the requested events
    """
    logger.debug(f"Incoming event stream request with filters: {wiki_codes_str}, {wiki_types_str}, {wiki_langs_str}")
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


def main():
    """
    If for some reason someone tries to run this module directly, tell them what to do
    """
    print("Run in dev with: uv run -- fastapi dev main.py" 
          "Run in prod with: source .venv/bin/activate; python -m fastapi run main.py")


if __name__ == "__main__":
    main()

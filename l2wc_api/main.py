import itertools
import sys
from contextlib import asynccontextmanager
from logging import Logger, StreamHandler, Formatter
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from httpx import get as httpx_get

WIKI_LIST_URL = "https://wikistats.wmcloud.org/wikimedias_csv.php"

LIST_OF_SPECIAL_WIKIS = (
    "incubator.wikimedia.org",
    "meta.wikimedia.org",
    "nostalgia.wikipedia.org",
    "outreach.wikimedia.org",
    "test.wikipedia.org",
    "wikitech.wikimedia.org",
    "strategy.wikimedia.org",
    "foundation.wikimedia.org",
    "usability.wikimedia.org",
    "thankyou.wikipedia.org",
    "quality.wikimedia.org",
)

logger: Logger = Logger(__name__)
logger.setLevel("DEBUG")
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Create shared state variables when the application starts
    :param app: the FastAPI app
    :return: nothin'
    """
    # Application startup activities
    logger.info("Starting up...")
    load_wikis_list()

    # let the application run
    logger.info("Startup complete.")
    yield

    # Application shutdown activities
    pass


app = FastAPI(title="listen-to-wiki-changes", lifespan=lifespan)


@app.get("/")
async def read_root():
    global wiki_dict
    assert len(wiki_dict.keys()) > 0, "Wiki dictionary is empty"
    return {"Hello": "World"}

def load_wikis_list():
    logger.info("Loading wikis list...")
    response = httpx_get(WIKI_LIST_URL)
    wiki_list.clear()
    wiki_types.clear()
    wiki_dict.clear()
    language_dict.clear()
    wiki_list_columns.clear()
    wiki_count = 0
    for line in response.text.splitlines():
        if line.startswith("rank"):
            # header row
            wiki_list_columns.extend(line.split(','))
        else:
            wiki_count = wiki_count + 1
            try:
                # logger.debug(f"Processing line({wiki_count}): {line}")
                wiki_metadata = dict(zip(wiki_list_columns, line.split(',')))
                wiki_type = wiki_metadata['type']
                if wiki_type and not wiki_type.isdigit():
                    wiki_list.append(wiki_metadata) # the list has everything, including things we removed
                    wiki_type = wiki_metadata['type']
                    prefix = wiki_metadata['prefix']
                    if wiki_type == 'special':
                        prefix_split = prefix.split('.')
                        special_name = "NOT_SPECIAL"
                        if prefix in LIST_OF_SPECIAL_WIKIS:
                            special_name = prefix_split[0]
                            wiki_metadata['code'] = special_name
                            wiki_dict[special_name] = wiki_metadata
                        elif prefix.startswith('www.') and 'wikimedia' in prefix and len(prefix_split) == 3 and prefix_split[0].strip():
                            # probably a language code as a TLD CC
                            special_name = prefix_split[-1] + "_wikimedia"
                            wiki_metadata['code'] = special_name
                            wiki_dict[special_name] = wiki_metadata
                        elif prefix.endswith('.org') and 'wikimedia' in prefix and len(prefix_split) == 3 and prefix_split[0].strip():
                            # probably a language code as the host name prefix
                            special_name = prefix_split[0] +  "_wikimedia"
                            wiki_metadata['code'] = special_name
                            wiki_dict[special_name] = wiki_metadata
                        if special_name == "_special":
                            logger.warning(f"Odd special name {special_name} generated for wiki {wiki_metadata}")

                        # we will skip any special wiki that doesn't match any of these

                    else:
                        # record the language short code for un-special wikis if one is present
                        if prefix:
                            if prefix in language_dict:
                                logger.debug(f"Language dict entry for prefix {prefix}: {language_dict[prefix]}")
                            if prefix in language_dict and language_dict[prefix][0] != wiki_metadata['language']:
                                logger.warning(f"Duplicate language code found for code {prefix}: "
                                               f"was {language_dict[prefix][0]}, now {wiki_metadata['language']}")
                            else:
                                language_dict[wiki_metadata['prefix']] = (wiki_metadata['language'], wiki_metadata['loclang'])


                    #logger.debug(f"Adding wiki {wiki_type}")
                    wiki_types.add(wiki_type)
                    wiki_code = prefix + "_" + wiki_type
                    wiki_metadata['code'] = wiki_code
                    wiki_dict[wiki_code] = wiki_metadata

                    logger.debug(f"Added wiki {wiki_code}")
            except Exception as e:
                logger.exception(f"Error processing line({wiki_count}): {line}")


    # debug logging
    logger.info(f"Finished loading wiki list. Processed {wiki_count} data rows.")
    logger.debug(f"Wiki types ({len(wiki_types)}): {list(wiki_types)}")
    logger.debug(f"Sample Language dict ({len(language_dict)}): {dict(itertools.islice(language_dict.items(), 10))}")
    logger.debug(f"Sample Wiki dict ({len(wiki_dict)}): {dict(itertools.islice(wiki_dict.items(), 10))}")
    #logger.debug(f"Wiki list ({wiki_count}): {wiki_list}")


@app.get("/api/events/")
async def read_events(wiki_names_str: Optional[str] = Query(None, alias="names"),
                      wiki_types_str: Optional[str] = Query(None, alias="types"),
                      wiki_langs_str: Optional[str] = Query(None, alias="langs")):
    logger.debug(f"Event streams request. Filters: {wiki_names_str}, {wiki_types_str}, {wiki_langs_str}")
    if not wiki_names_str and not wiki_types_str and not wiki_langs_str:
        raise HTTPException(status_code=400, detail="At least one filter must be specified")
    wiki_names = wiki_names_str.split(",") if wiki_names_str else []
    wiki_types = wiki_types_str.split(",") if wiki_types_str else []
    wiki_langs = wiki_langs_str.split(",") if wiki_langs_str else []

    return {
        "wiki_names": wiki_names,
        "wiki_types": wiki_types,
        "wiki_langs": wiki_langs,
    }


def main():
    print("Run in dev with: uv run -- fastapi dev main.py" 
          "Run in prod with: source .venv/bin/activate; python -m fastapi run main.py")


if __name__ == "__main__":
    main()

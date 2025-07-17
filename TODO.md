# Tasks To-do

## core functionality and usability
* maybe sort the wiki list and languages 
* check color scheme for color deficiency legibility

## bugs
* Dark mode on header is broken since mobile responsiveness update

## feature matches to original
* add link to user page in recent changes
* maybe: change color scheme back to original: Green circles show edits from unregistered contributors, and purple 
  circles mark edits performed by automated bots.
* add toggles to hide: 
  * article titles
  * new user announcements
* add ability to filter for edits with a hashtag in the edit summary
* link to diffs instead of pages
* consider identifying unregistered users (or temp accounts)
* cap amount of currently playing sounds

## enhancements
* Change "start" and "stop" buttons to boolean state and leave selector checkboxes unchanged
* A11y: give bot edits a different fill pattern
* show total counts for wikis, languages, and types on tab labels
* i18n for UI text

## blocked ideas
* see if reverts are specifically tagged, so they could get a distinct look
  * NOTE they are not tagged as reverts
* include events where a Wikidata edit triggers a page reparse
  * NOTE these events aren't sent by the event stream SSE because in the judgment of the Data Engineering team,
    they are too numerous and would be noisy. Maybe

## developer doc and deployment readiness
* test on 
  * macos chrome ✅
  * ios ✅
  * android chrome browser ❌
* prod deployment ✅
* make a logo that can be the fav icon

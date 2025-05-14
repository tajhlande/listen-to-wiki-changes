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




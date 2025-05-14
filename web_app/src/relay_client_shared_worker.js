/**
 * @fileoverview A worker to handle connection to the Python-powered API backend to fetch events
 * Listens to Server-Sent Events from the backend and updates the UI in real-time.
 * @param e the event
 */


onconnect = (e) => {
    const port = e.ports[0];
    let eventSource;

    port.start();
    console.log("Streaming event worker started")


    port.onmessage = (e) => {
        // if there was already an event source connected, disconnect it first
        if (eventSource && eventSource.readyState in [0, 1]) {
            console.info("Closing old event source connection")
            eventSource.close();
        }
        eventSource = null;

        // new message from front end UI
        let apiUrl = e.data.apiUrl
        let wikiCodes = e.data.wikiCodes;
        let wikiTypes = e.data.wikiTypes;
        let wikiLangs = e.data.wikiLangs;
        console.log("Got " + wikiCodes.length + " wikiCodes")
        let eventAPIUrl = new URL(apiUrl);
        let setAtLeastOneParam = false
        if (wikiCodes && wikiCodes.length > 0) {
            eventAPIUrl.searchParams.set('codes', wikiCodes.toString());
            setAtLeastOneParam = true;
        }
        if (wikiTypes && wikiTypes.length > 0) {
            eventAPIUrl.searchParams.set('types', wikiTypes.toString());
            setAtLeastOneParam = true;
        }
        if (wikiLangs && wikiLangs.length > 0) {
            eventAPIUrl.searchParams.set('languages', wikiLangs.toString());
            setAtLeastOneParam = true;
        }

        if (setAtLeastOneParam) {
            console.info('Creating event stream with URL: ' + eventAPIUrl);
            eventSource = new EventSource(eventAPIUrl);

            eventSource.onopen = () => {
                console.info('Event stream started from URL: ' + eventAPIUrl);
            };
            eventSource.onerror = (event) => {
                console.error('Error from event stream', event);
            };
            eventSource.onclose = (event) => {
                console.warn('Event stream closed', event);
            }
            eventSource.addEventListener("wiki_event", (event) => {
                // event.data will be a JSON message
                // console.log("Event received")
                try {
                    const data = JSON.parse(event.data);
                    // console.log('Received event from server: ' + JSON.stringify(data))
                    port.postMessage(data);
                } catch (err) {
                    console.error(err)
                }
            });


        } else {
            console.info('Not opening event stream because no wiki codes, types, or languages were selected')
        }
    }
}

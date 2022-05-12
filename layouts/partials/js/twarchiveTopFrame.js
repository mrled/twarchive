{{- partial "js/twarchiveEverywhere.js" -}}

/* Code to expand/collapse all tweets on a page
 */
function twarchiveSetCollapsibleTweetsDisplay(state) {
  const tweets = document.getElementsByClassName("twarchive-collapsible");
  for (const tweet of tweets) {
    switch (state) {
      case "open": tweet.open = true; break;
      case "closed": tweet.open = false; break;
      default: console.log(`Unknown state: ${state}`);
    }
  }
}

/* Measure the DOM inside the tweet iframe.
  * Change the dimensions of the <iframe> element to be big enough to show the entire document without scrolling.
  */
function twarchiveResizeTweetFrames(tweetId) {
  const className = tweetId ? `twarchive-html-iframe-${tweetId}` : "twarchive-html-iframe"
  const tweetFrames = document.getElementsByClassName(className);
  for (const frame of tweetFrames) {
    const body = frame.contentDocument.body;
    if (!body) {
      // console.log(`twarchiveResizeTweetFrames(${tweetId}) called but there is no body. I'm not sure why this happens. Early load on a big page?`)
      continue;
    }
    const bcr = body.getBoundingClientRect();
    // console.log(`Tweet frame body bcr: ${JSON.stringify(bcr)}`);

    // this is just a magic number that works for me, idek man.
    // fucking DOM APIs.
    const magicHeightAdjustment = 10;

    frame.height = bcr.height + magicHeightAdjustment;
  }
}

/* Receive messages from the tweet iframe
  */
function twarchiveReceiveFrameMessage(event) {
  if (!event.data.twarchiveEvent) {
    // This must be an event from somewhere else.
    // At the time of this writing we do not have iframes anywhere except tweets.
    // However, React devtools inserts events that will show up here.
    return;
  // } else {
  //   console.log(`In twarchiveReceiveFrameMessage, processing event ${JSON.stringify(event.data)}`);
  }
  switch (event.data.twarchiveEvent) {
    case "twarchive-resize":
      twarchiveResizeTweetFrames(event.data.tweetId);
      break;
    case "twarchive-display-data-uri":
      window.location.href = `${window.location.href}?twarchive-datauri#${event.data.dataUri}`;
      console.log(`Setting window.location.href to ${window.location.href}`)
      twarchiveDisplayDataUri();
      break;
    default:
      console.error(`Unknown message type '${event.data.twarchiveEvent}' for message ${JSON.stringify(event.data)}`);
      break;
  }
}

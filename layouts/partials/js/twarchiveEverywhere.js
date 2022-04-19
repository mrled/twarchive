/* Functions that are used in a tweet iframe and in the parent
 */


/* If the query string contains a data URI, display it.
 */
function twarchiveDisplayDataUri() {
  if (window.location.search.indexOf("?twarchive-datauri=data:") == 0) {

    console.log("Going to display a data URI...")

    // WARNING: blindly trusting window.location might be bad.
    // Probably OK on my site bc there is no server side logic? ¯\_(ツ)_/¯
    const dataUri = window.location.search.substring(19);

    // Get a new, blank <body>
    document.documentElement.innerHTML = document.implementation.createHTMLDocument().documentElement.outerHTML;
    // This should now be the very simple: <html><head></head><body></body></html>
    document.body.style = "margin: 0; padding: 0;"

    // Create an iframe containing the data URI
    const frame = document.createElement("iframe");
    frame.style = "display: block; border: none; width: 100vw; height: 100vh;"
    frame.src = dataUri;
    frame.setAttribute("sandbox", "");
    document.body.appendChild(frame);
  }
}

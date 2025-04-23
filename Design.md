# FormAgent Extension Design (Local Server Integration)
Overview

FormAgent’s browser extension is designed to auto-fill web forms by leveraging user data stored on a local server. This extension (starting with Firefox, with plans for Chrome) will retrieve and fill form fields using personal data (e.g. name, email, address) stored locally. The architecture splits responsibilities between the extension and a lightweight local HTTP server for simplicity and performance. Key features include:

    1. Seamless Installation: A standard WebExtension (initially for Firefox) that can be installed via the browser’s extension interface.

    2. Local Data Sync: On startup, the extension connects to a local server to fetch the latest user data for form filling.

    3. Automated Form Filling: Content scripts injected into web pages detect form fields and automatically fill them with the synchronized user data.

    4. User Data Management: An in-browser Options page allows the user to view and edit their stored form data, which is sent back to the local server for storage.

    5. Future Portability: The design anticipates porting to Chrome (and other browsers), reusing most logic with minimal changes.

This document details the design and implementation plan for the FormAgent extension and its local server, including how they communicate and how the system will be structured.
Browser Extension Architecture
Installation and Setup (Firefox)

The FormAgent extension will be packaged as a Firefox WebExtension that users (or the FormAgent application) can install via about:debugging or the Add-ons interface. It will have a standard manifest.json defining the extension’s components and permissions:

    Manifest Version: Use Manifest V3 for forward-compatibility (Firefox supports MV3, and Chrome requires it). This means using a background service worker (in Chrome) or persistent background script (Firefox can allow persistence for MV2, but MV3 is preferred for parity).

    Permissions: Include necessary host permissions and extension APIs. For example:

        "<all_urls>" or specific patterns (e.g. "*://*/*") under content_scripts.matches so the content script runs on all pages with forms.

        "http://localhost:PORT/*" under permissions (MV2) or host_permissions (MV3) so the extension can communicate with the local server via HTTP​
        stackoverflow.com
        . This ensures fetch requests to the local API (e.g. http://127.0.0.1:5000) are allowed by the browser.

        "activeTab" permission if needed to allow on-demand access to the current page (though content scripts running on all pages may suffice).

    Background Script: Define a background script (or service worker) that runs on extension startup. This script will handle data synchronization with the local server and coordinate messaging between content scripts and the server.

    Content Scripts: Specify a content script to be injected into web pages. The manifest’s content_scripts section will list script file(s) and matching URL patterns (e.g., all HTTP/HTTPS pages) so that the extension can detect forms on any site the user visits.

    Options Page: Provide an options_ui page in the manifest, pointing to an HTML file that serves as the settings interface. For example:

    "options_ui": {
        "page": "options.html",
        "open_in_tab": false
    }

    This page will load inside Firefox’s add-on preferences and allow the user to view/edit their form data.

Because Firefox extensions (unless distributed through AMO) need to be signed or loaded temporarily, during development FormAgent can be loaded as a temporary add-on or via a custom Firefox profile with signature enforcement disabled (e.g., using the provided disable_firefox_signing.py script). Once installed, the extension should start automatically with the browser and persist across sessions.
Startup and Data Synchronization

On browser startup (or extension installation/enabling), the FormAgent extension’s background script will auto-sync with the local server:

    The background script triggers as soon as the extension loads. In Manifest V3, this could be via the runtime.onStartup event in the service worker; in Manifest V2 (Firefox), a persistent background page would run immediately.

    Local Server Connection: The extension will attempt a fetch request to the local server’s API endpoint to retrieve user data. For example, a GET request to http://127.0.0.1:5000/data (assuming the server listens on port 5000) will fetch all stored user form data in JSON format.

    Auto-start Server: If the local server is not already running at extension startup, FormAgent should start it. One approach is to bundle a small local server program with the FormAgent application and launch it when the extension starts. Since WebExtensions cannot directly spawn processes, this could be achieved by:

        Launching the server as part of a higher-level FormAgent startup script (outside the browser). For instance, if the user starts FormAgent via a shell script or a desktop app, that process can start the local HTTP server then open the browser with the extension.

        Alternatively, using the browser’s Native Messaging capability to trigger a local helper application. The extension can connect to a pre-registered native app which in turn starts (or communicates with) the server. (This approach is more complex and typically not needed if FormAgent is started via script, but is an option for future enhancement.)

    Data Caching: Once data is fetched from the server, the extension can cache it for quick access. For example, the background script might store the user data in a JavaScript object in memory or in browser.storage.local. Caching avoids repeated server calls for every form, improving performance. However, the extension should also have a strategy to refresh this cache if the data is updated (e.g. after the user edits in the options page, or periodically on a timer or on each startup).

    No Data Scenario: If the server has no data yet (e.g., first run), the extension simply has an empty dataset (and thus will not fill forms). After the user enters data in the options page (or via some import), the data would then be stored on the server for future use.

In summary, the extension’s first task on load is to ensure it has the latest user info by contacting the local server. If the server is not running, it should be started (outside the extension’s direct control, likely by the FormAgent app itself). Once synchronized, the extension is ready to fill forms as the user browses.
Content Scripts for Form Detection and Auto-Filling

Content scripts are injected into web pages to detect and fill forms. A content script runs in the context of the webpage, allowing it to inspect and manipulate the DOM of forms​
developer.mozilla.org
. In FormAgent’s case, the content script will:

    Injection Timing: The content script should be loaded at an appropriate time (e.g., at document idle or after DOMContentLoaded) so that the form elements are present. This is configured in the manifest (using "run_at": "document_idle" by default or "document_end" if needed earlier).

    Form Detection: Once running, the script scans the page for form fields (e.g., <input>, <textarea>, <select> elements). It can filter for specific input types or names that match user data keys. For example, common fields like name, full_name, first_name, last_name, email, phone, address, etc., can be identified by looking at element attributes (name, id, placeholder, etc.).

    Matching Data to Fields: For each detected form field, the script determines what data to fill. A simple strategy is to use the field’s name or id attribute as a key to look up in the user data object. For instance, if an input has name="email" and the cached user data has an "email" field, the script will insert that email value into the input. Similarly, name="first_name" or similar would map to the user’s first name in the data. We can maintain a mapping (including variations, e.g., if the site uses fname we could map it to first_name).

    Filling the Fields: The content script sets the value of the input elements to the corresponding data. After setting the value, it can trigger input or change events if necessary to ensure any site scripts react to the filled value (since some forms only recognize input if events fire).

    Example: If the user visits a sign-up page with fields for first name, last name, and email, the content script will find these fields by their identifiers. Suppose the form’s HTML is:

    <input name="first_name">
    <input name="last_name">
    <input name="email">

    The script retrieves the cached data (e.g., data.first_name, data.last_name, data.email) and sets each field’s value property accordingly (e.g., input.value = data.first_name).

    Avoiding Conflicts: The script will typically only fill empty fields to avoid overwriting user-entered data or browser autofill. It could check if (!input.value) input.value = data; before filling. Additionally, it may skip filling fields like passwords or sensitive info unless explicitly intended by the design (the current scope is personal information, not passwords or credit cards).

    Continuous Monitoring: For dynamic forms (AJAX-loaded or single-page applications), we might need to observe the DOM for new form fields (using MutationObservers) to fill them when they appear. This ensures that if the user navigates without a full page load (or if forms are loaded dynamically), FormAgent can still fill fields appropriately.

The content script operates within the page but is isolated from the page’s own scripts. It can read and write the DOM freely​
developer.mozilla.org
. If the content script needs additional data or needs to perform an action not allowed in the page context (like cross-origin network requests), it will communicate with the background script via message passing​
developer.mozilla.org
. However, for most form filling operations, the necessary data is already cached, so the content script can act autonomously using that data.
Options Page for User Data Management

The extension provides an Options page where users can view and edit the personal data used for form filling. This page is essentially a settings UI served from an HTML file packaged with the extension:

    UI Elements: The options page will present a form or a set of fields corresponding to the data stored. For example, it may list text fields for "First Name", "Last Name", "Email", "Phone", etc., pre-populated with the current values from the local server’s database. Users can change or fill in any missing values and submit the form.

    Loading Data: When the options page opens, it should fetch the current data from the local server. This can be done by a script in the options page calling the local API (similar to how the background does). Since the options page is an extension page (not a content script), it has the same privileges as the background script to make cross-origin requests to localhost (provided the host is in the manifest permissions). The options script might call fetch("http://127.0.0.1:5000/data") to retrieve the JSON data and then populate the UI form fields.

    Editing and Saving: When the user clicks “Save” (or the form is submitted), the options page will send the updated data back to the local server. This could be via an HTTP POST/PUT request to an endpoint like http://127.0.0.1:5000/data. The data would be gathered from the form and sent in JSON format (or as form data) in the request body.

    Local Update: After a successful save to the server, the extension should update its cached copy of the data to stay in sync. This can be done in a couple of ways:

        The options page, after receiving a success response from the POST, can send a message to the background script with the new data or simply update the cached object if the background is accessible. Alternatively, the background script could be the one handling the POST (if the options page communicates the changes to the background which then performs the server update).

        The simplest approach is the options page itself uses fetch to POST, and on success, perhaps triggers a fresh GET to update the displayed data or notifies the background to refresh its cache.

    No Authentication: Since this is all local, we do not need any login or auth for accessing or modifying the data. The assumption is that only the user (with access to the machine) can open the options page. The local server accepts changes without credentials, simplifying the design.

    User Guidance: The options page can include some basic instructions or notes (e.g., “Edit your information below. This data will be used by FormAgent to fill forms on websites you visit.”). It should make clear that the data is stored locally for the user’s convenience.

    UI/UX Considerations: Use simple HTML forms for the options page for now, which is easiest for a wiki/design doc context. In implementation, one might add some nicer styling or even a React/Vue app if needed, but that’s not necessary for the design. The main point is functionality: retrieving and updating the stored data.

By providing an options interface, users have full control over what data is stored and used for autofill. They can update it at any time, and those updates propagate to the server and will be used by content scripts the next time they fill a form.
Local Server Design
Auto-start and Lifecycle

The local server is a lightweight server running on the user’s machine that stores and serves the form data. It should ideally start automatically when FormAgent is launched:

    Launching the Server: The recommended design is to have the FormAgent application (outside the browser extension) handle launching the server. For example, if FormAgent is distributed with a Python script or an executable, running that could spawn the local server in the background (listening on a predefined port, e.g., 5000). If the extension is being used standalone, a more advanced approach could be to use native messaging to launch the server, but typically we assume the user has started FormAgent’s backend.

    Persistent Service: The server can be a simple process that stays running in the background (perhaps with an icon in the system tray, or as a background process) for as long as the browser/extension is in use. If the browser is closed, the FormAgent launcher might also shut down the server, depending on user preference. Alternatively, the server could remain running waiting for future browser sessions, since it’s local and lightweight.

    Implementation: The server can be implemented in any suitable language (Python, Node.js, Go, etc.). Given FormAgent’s context, a Python Flask server or Node Express server could be used:

        Python example: A Flask app that defines routes for getting/setting data, and runs app.run(port=5000, host='127.0.0.1') when FormAgent starts.

        Node example: An Express.js server with similar GET/POST endpoints.

    No External Exposure: The server should bind to 127.0.0.1 (localhost) only, not to external network interfaces. This ensures the data is not accessible from other machines or over the internet – it’s strictly within the user’s device.

    No Need for Encryption/SSL: Since it’s on localhost, we can use plain HTTP. There is no transmission over a network beyond the local machine, and the browser will treat http://localhost as a potentially secure context for development. Modern browsers allow http://127.0.0.1 connections even if they might warn for general HTTP; since this is an extension with permission, it will be fine. We explicitly opt out of HTTPS to avoid needing certificates for localhost.

    CORS Considerations: To allow the extension (especially content scripts or option pages) to query the server, we might enable CORS on the server. Setting Access-Control-Allow-Origin: * on responses is a simple way to ensure any origin (including the extension’s context or a content script’s page context) can fetch the resources. Because this server is private, opening CORS widely is acceptable. However, if the extension fetches from the background script context with the proper host permission, CORS headers may not even be required by the browser (extensions with host permissions can bypass typical web-page CORS restrictions). As a safe measure, adding a wildcard CORS header on all responses will prevent any issues with content script direct fetches.

In essence, the local server is a dedicated personal data provider that should be running whenever the browser extension is active. The design keeps it always-on (for the duration of usage) so that any time a form needs filling or the user updates data, the server is available to respond.
Data Storage Format and Management

The local server is responsible for storing the user’s form data in a structured format that allows quick retrieval by keys (for the AI or the extension). Two suitable formats are JSON files or a SQLite database:

    JSON Storage: The server can store data in a JSON file (e.g., userdata.json in the user’s FormAgent directory). The data structure would simply be a JSON object with key-value pairs corresponding to form fields. For example:

    {
      "first_name": "Alice",
      "last_name": "Smith",
      "email": "alice@example.com",
      "phone": "123-456-7890",
      "address": {
         "street": "123 Maple Dr",
         "city": "Springfield",
         "zip": "55555"
      }
    }

    This format is human-readable and easy to modify or inspect. On server start, it can load this JSON into memory (or query it directly as needed). When data is updated via the extension, the server writes the changes back to the JSON file for persistence.

    SQLite Storage: For a more robust solution, the server could use a SQLite database file. A table (e.g., user_data) could store key-value pairs or a structured schema (columns for name, email, etc.). SQLite offers fast lookups and update operations and can scale if we later store more complex or numerous records (like multiple profiles or form histories). For example, a table might have columns: first_name, last_name, email, phone, address_street, address_city, address_zip etc., with a single row for the primary user profile. The server would query this DB to get data and update it on edits.

    Structured for AI Access: Whether JSON or SQLite, the structure should allow an AI or any other component to easily query specific pieces of information. For instance, if an AI module needs the user’s phone number, it should be able to request the phone field quickly. In JSON, that’s just parsing the object; in SQLite, a simple SELECT query by field name or a specific query if using a normalized structure.

    Performance: The amount of data is relatively small (a few dozen fields at most for personal info), so either storage approach will have negligible latency on queries. JSON might be slightly simpler (no query overhead, just load into a dictionary), while SQLite might be advantageous if we foresee complex queries or multiple records. Given the “fast, structured retrieval” requirement, SQLite could be justified if we expect to do more than fetch all data at once. However, since the extension often needs all or most of the data at once (to fill forms), returning a JSON blob of everything is fine.

    No Encryption: The data will be stored in plain text (if JSON) or plain database records (if SQLite). This is acceptable because it’s stored on the user’s local machine in an isolated environment. We assume the user trusts their machine’s security. Not implementing encryption or authentication avoids complexity — the user does not have to manage keys or passwords for this data store. The trade-off is that anyone with access to the machine account can read the file, but since FormAgent is for personal local use, this is considered acceptable in this design.

    Updates: The server should handle updates safely. For JSON, writing out the entire file on each change is fine (with data this small, performance impact is minimal). For SQLite, each update can be an UPDATE SQL statement. We should ensure that simultaneous accesses are handled (though in this design, typically only the extension interacts with the server, one request at a time). If using a framework like Flask, which is single-threaded by default, requests are handled sequentially, so no race conditions on file writing. If using Node, using file write with appropriate sync or using a single process threading model will similarly ensure safe writes.

In summary, the server will manage a single source of truth for user data. Simplicity and reliability are prioritized: the data format is straightforward, and operations (read/write) are atomic and quick. This structured storage means both the extension and any AI logic can retrieve needed fields by name with minimal processing.
HTTP API Endpoints

The local server exposes a simple HTTP API that the extension (and potentially other FormAgent components) will use. The API is minimal, focusing on retrieving and updating the user data. Proposed endpoints:

    GET /data – Returns the entire set of stored user data as a JSON object. For example, a request to http://127.0.0.1:5000/data might respond with:

    {
      "first_name": "Alice",
      "last_name": "Smith",
      "email": "alice@example.com",
      "phone": "123-456-7890",
      "address": {
        "street": "123 Maple Dr",
        "city": "Springfield",
        "zip": "55555"
      }
    }

    The extension’s background script or options page will use this to populate forms or UI. This endpoint is read-only; it does not modify anything on the server.

    POST /data – Accepts a JSON payload to update the stored data. The extension will call this when the user saves changes in the options page. The body of the POST will be a JSON object with the same structure as the data (or a subset). For simplicity, the server can replace the entire stored record with the provided JSON on each update. For example, sending {"first_name": "Bob", "email": "bob@example.com"} would update those fields (and we might choose to keep other fields unchanged, or require the full record in the request – design choice). A successful response could be a 200 OK with perhaps the updated JSON or a confirmation message.

    Optional: GET /data/<field> – For convenience, the server might allow getting a specific field by endpoint, e.g. GET /data/email returns just {"email": "alice@example.com"}. This is not strictly necessary (the extension can fetch all data and pick what it needs), but could be useful if an external AI agent wanted only one piece of information quickly. Implementing this is straightforward: parse the <field> from the URL and return { "<field>": value } or a 404 if not found.

    Optional: Other endpoints – At this stage, we don’t need more than the above. In the future, if FormAgent stores multiple profiles or form templates, there could be endpoints like /profiles or similar. But for a single-user data store, one endpoint is enough.

    Response format: Always JSON for consistency. Even a POST response can return the new data or a status JSON. Using JSON makes it easier for any client (browser extension or AI code) to parse the results.

The API is deliberately simple: it’s essentially a RESTful interface for CRUD (Create, Read, Update, Delete) on the user’s profile data, though we might not implement Delete separately (the user can just overwrite or clear fields via the update). There is no authentication layer (since local only) and no complex query parameters. This means the extension implementation is also simple (just do GET or POST fetch calls).

CORS & Security: As noted, we will set Access-Control-Allow-Origin: * so that even if the content script tries to call the API directly from a webpage context, the browser will allow it. We trust local calls, so we are not restricting origins. There is also no need for CSRF protection because no other website can realistically exploit this API (an external site cannot initiate requests to 127.0.0.1:5000 in the user’s browser unless the user is tricked into installing something malicious, which is out-of-scope). We assume the extension is the only client. The server may log requests or errors to the console for debugging, but otherwise it’s a quiet background service.
Extension–Server Communication

The extension and the local server communicate via HTTP requests. The design uses the browser’s fetch() API to send requests from the extension to http://localhost. Key aspects of this communication include:

    Using Fetch from Extension Scripts: The extension’s background script (or any extension page like the options page) can use the Fetch API or XMLHttpRequest to call the local server. Since the server is on a different origin (localhost vs the websites), this is a cross-origin request. Browsers normally block cross-origin calls from web pages (due to CORS), but extensions are privileged. By declaring the localhost URL in the manifest permissions, the extension is allowed to bypass or rather perform these requests. In Firefox/Chrome Manifest V3, this is done via the host_permissions field​
    developer.mozilla.org
    . In Manifest V2 (Firefox), listing it under permissions achieves the same effect. For example, we include "http://127.0.0.1:5000/" (or a wildcard like "http://127.0.0.1:*/*") in the manifest. This was demonstrated to resolve network errors when an extension tries to contact a localhost server​
    stackoverflow.com
    .

    Content Script vs Background for Fetch: We have two possible places to do the fetch calls:

        Background Script: A common pattern is to let the background script handle external requests. Content scripts can’t use certain WebExtension APIs directly, but they can message the background to do so​
        developer.mozilla.org
        . The background has full access to the network (with granted permissions) and is not subject to the page’s CORS restrictions​
        developer.mozilla.org
        . In our design, the background script performs the initial GET on startup to sync data. It can also handle the POST from the options page (or the options page can do it directly, since the options page is an extension page, not a web page).

        Content Script Direct Fetch: It is possible for the content script to call the local server directly (for example, if it needed data on the fly). If it does, it will run into cross-origin rules since the script runs in the context of the web page. However, because our server will allow all origins (CORS *), the fetch from the content script would succeed. We would need to include mode: 'cors' in the fetch call. This approach means the content script doesn’t have to ask the background for data, but it requires the server’s CORS headers to be set properly.

    Chosen Approach: To simplify, the extension will primarily use the background script for communication:

        On startup, the background does fetch('http://127.0.0.1:5000/data') and stores the result.

        When a content script needs data, it can either already have it (if we pre-injected the data into the content script via a global or message) or it can send a message like browser.runtime.sendMessage({type: "getData"}) to the background. The background, upon receiving this, can either return the cached data or perform a fresh fetch if needed. The content script then receives the data and proceeds to fill the form.

        When the user updates data in the options page, the options script does fetch('http://127.0.0.1:5000/data', { method: 'POST', body: ... }). This could be done directly from the options page script (since it’s basically an extension privileged context) or via the background (options page sends a runtime message to background with new data, background does the fetch). Either way, the data goes to the server. After a successful update, the background script should refresh its cache (either use the data that was just sent or do a new GET).

    Error Handling: If a fetch fails (e.g., server not responding), the extension should handle it gracefully:

        On startup GET failure: possibly retry after a delay, or notify the user (maybe via an icon badge or console message) that the server is not reachable. It might attempt to start the server (if such capability exists via native messaging). Since no authentication is used, a failure likely means server is down.

        On POST failure: the options page could show an error message like “Failed to save data. Is FormAgent running?”.

        However, in a typical integrated setup, the FormAgent launcher will ensure the server is running by the time the browser opens, so these errors should be rare.

    Performance: Localhost communication is extremely fast (usually sub-millisecond for request overhead). The data volumes are tiny (a few hundred bytes of JSON), so latency is negligible. The extension can thus afford to fetch data whenever needed without worrying about performance. Even so, caching in memory avoids unnecessary repeated JSON parsing on every page navigation.

    Security of Communication: Since we run over HTTP on localhost, data is in plaintext over the loopback interface. This is acceptable in our trust model. If an attacker has local access, there are bigger issues, so we don’t encrypt or authenticate the traffic. The extension and server essentially trust each other fully. We also assume the port (e.g. 5000) is not conflicted by another service. Choosing a less common port or allowing configuration could be considered, but for now a default static port is fine (the extension and server must agree on it).

In summary, the extension uses straightforward web requests to talk to the local server. The manifest’s permissions enable this communication. The background script acts as the mediator for data flow between web pages (content scripts) and the server, following the principle that content scripts are mostly for DOM manipulation while background scripts handle heavy logic or external interactions​
developer.mozilla.org
. This separation also means we could swap out the data source (for example, if we later use a different mechanism) by changing the background logic without touching content scripts.
Workflow Description (Extension-Server Interaction)

To illustrate how the FormAgent extension and local server work together, below is a step-by-step workflow covering typical use cases:
1. Browser Startup & Extension Initialization

    User Launches FormAgent: The user starts FormAgent, which in extension mode might involve launching the local server and opening Firefox with the extension installed. (If the extension is already installed in the browser, simply opening the browser will activate it. We assume the FormAgent server is started around the same time.)

    Extension Loads: Firefox enables the FormAgent extension on startup. The background script runs (for MV3, the service worker wakes up on the runtime.onStartup event).

    Data Sync Request: The background script sends an HTTP GET request to the local server (e.g., GET http://localhost:5000/data). This is the “sync” step to retrieve current user data. If the server isn’t up yet, this request will fail – the extension can then optionally keep retrying a few times (with brief delays) or log an error. Assuming the server is running (auto-started by FormAgent), it will respond.

    Server Responds: The local server, which started as part of FormAgent’s launch, receives the GET request. It reads the user data from its storage (JSON or DB) and returns a JSON response with all the data.

    Background Caches Data: The extension’s background script receives the data response. It parses the JSON into a JavaScript object (if not already done by fetch automatically). This object (say userData) is stored in a global variable or in browser.storage.local for later use. Now the extension is ready to fill forms. (If the server had returned an error or empty data, the extension would just have an empty dataset.)

2. Automatic Form Filling on Page Load

    User Navigates to a Web Page: The user goes to a page with a web form (for example, a registration page).

    Content Script Injection: As the page loads, the FormAgent content script is automatically injected (because the URL matches *://*/* which our manifest specified). According to the manifest configuration, by the time the page’s DOM is fully constructed, our script runs.

    Form Detection: The content script scans the DOM for form fields. It finds input elements and checks their names/ids. Suppose it finds <input id="fname" name="first_name"> and <input name="email"> on the page.

    Request Data from Background: The content script needs the actual values to fill. If the extension cached the data on startup, the content script can get it via a message. For example, it does:

    browser.runtime.sendMessage({action: "getFormData"});

    The background script is listening for messages. Upon receiving this, it sends back the userData object (or specifically the subset needed). (Alternatively, we might have injected the data earlier or made it available via browser.storage, but message passing is clear and on-demand.)

    Data Received in Content Script: The content script’s message handler gets the user data object from the background’s response. Now it has (for instance) { first_name: "Alice", email: "alice@example.com", ... }.

    Fill Fields: The content script iterates over the detected form fields. It matches name="first_name" with userData.first_name and sets the input’s value to "Alice". Likewise, it finds the email field and sets its value to "alice@example.com". If a field has no corresponding data (e.g., the page has an extra field that the data doesn’t cover), the script leaves it blank.

    User Sees Form Filled: By the time the page is fully loaded, the user sees that their information has been auto-filled into the form by FormAgent. They can review or change it before submitting. If the user navigates to another page with forms, the same process repeats (without needing to re-fetch data each time, since the data is cached).

    Dynamic Updates (if any): If the page adds new form fields dynamically after load (say, selecting “Yes” to something reveals new fields), the content script could be set up with a MutationObserver to catch added inputs and fill them if applicable. This is an advanced detail; the initial design can assume forms are present at load.

3. User Updates Data via Options Page

    User Opens Options Page: At some point, the user might want to update their stored data (e.g., they have a new phone number). They open the FormAgent extension’s options page (through Firefox’s add-on manager or a toolbar icon that opens it).

    Display Current Data: The options page HTML/JS, on load, executes a script that requests the current data. This can be done by directly calling the server (GET /data) or by asking the background for the cached data. For reliability, the options page might fetch directly from the server to ensure it’s the latest. The server returns the JSON, and the options page populates each form field in the UI with those values (e.g., fills the text input for "Phone" with "123-456-7890").

    User Edits Fields: The user changes the "Phone" field to "987-654-3210" and perhaps updates any other info. They then hit a "Save" or "Update" button on the options page.

    Send Update to Server: The options page collects all the fields into a JSON object. It then sends an HTTP POST to http://localhost:5000/data with the JSON in the request body. For example, {"phone": "987-654-3210", "first_name": "Alice", "last_name": "Smith", ...} (likely the full dataset). The background script could also facilitate this, but doing it directly from the options page script is fine since it has permission.

    Server Updates Storage: The local server receives the POST request. It parses the JSON and updates the underlying storage (writing to the JSON file or updating the SQLite DB). It overwrites the old phone number with the new one. It then responds with a success status (200 OK, possibly returning the updated data or a simple message).

    Extension Receives Confirmation: The options page script gets the response. It might show a quick confirmation message like "Saved successfully." The extension’s background cache is now outdated, however.

    Refresh Cache: The extension background could listen for an internal message or the options page could proactively send the new data to the background. For instance, after a successful save, the options page could call browser.runtime.sendMessage({action: "dataUpdated", newData: updatedData}). The background script, on receiving this, will replace its cached userData object with the updatedData. Alternatively, the background could simply do another GET to /data to refresh. In either case, now the extension’s cache matches the server’s storage.

    Subsequent Form Fills: When the user now goes to another form (say a contact form on a website), the content script will request data and get the updated phone number. The new number will be filled into any appropriate field (e.g., name="phone" input) on those forms.

Throughout this workflow, the extension and server work in tandem to keep data in sync and use it at the right times. The user’s experience is that after initial setup, forms get magically filled with their info, and any time they update that info via the extension, the changes take effect in future form fills.
Chrome Implementation Notes (Portability)

Porting the FormAgent extension to Google Chrome (and other Chromium-based browsers) should be straightforward thanks to the cross-browser WebExtension standard. Key considerations for Chrome:

    Manifest Version: Chrome requires Manifest V3 for any new extensions. The Firefox extension should already be using MV3 in our design, which is good. The manifest may need slight adjustments:

        In Chrome, the background script must be a "service_worker" in the manifest under "background". In Firefox, MV3 also supports service workers. We ensure our background logic is compatible with the service worker model (no direct DOM, use messaging, etc.). Chrome does not allow persistent background pages in MV3, so all background logic should be event-driven.

        The host_permissions key in the manifest will be used for the localhost permission in Chrome​
        developer.mozilla.org
        . Chrome will prompt the user at installation about allowing access to 127.0.0.1 if it's listed.

    APIs and Polyfills: Firefox’s browser API is promise-based, whereas Chrome’s chrome API uses callbacks. However, since MV3, Chrome also supports promises in many cases, or we can use the Mozilla browser.polyfill.js to use a unified browser namespace in both. We should either include a polyfill or write the extension to handle both (e.g., use feature detection). Many developers simply use chrome.* and add promise wrappers if needed. For our basic needs (runtime messaging, storage, etc.), the differences are minor.

    Background Persistence: In Chrome, the service worker background will go idle when not in use. This means we cannot rely on global variables in the background script to always persist (unlike a persistent background page in Firefox). Our design caches userData in memory; in Chrome’s case, the service worker might unload after some time, losing that in-memory cache. To handle this:

        We can store userData in chrome.storage.local after fetching. That way, if the background unloads, the data is still in Chrome’s extension storage and can be retrieved quickly when needed.

        Alternatively, the content script can simply request data from the server each time it needs (or request the background to fetch fresh each time). Given local server speed, fetching on every form detection might be acceptable. But to reduce calls, storing in storage is fine.

        We will implement a logic such that on chrome.runtime.onInstalled or onStartup, we populate storage, and on each content script request, if the background is active and has cache it uses it, otherwise it reads from storage (or re-fetches).

    Messaging differences: browser.runtime.sendMessage works slightly differently in Chrome (callback vs promise). Using a promise-based approach with async/await can smooth this over. Or using the callback and treating it uniformly. These are low-level differences to handle in implementation.

    Localhost Permissions in Chrome: Chrome treats http://127.0.0.1 as an ordinary remote host for permission purposes. With the manifest entry, it will allow it. One thing to note: in Chrome, if the extension is installed from the Chrome Web Store, they might require justification for needing access to all sites or localhost in the listing. Since FormAgent is likely a personal tool, this is not a technical issue but something to document for publishing.

    Testing in Chrome: Chrome and Edge will be the same in terms of extension code. We should test that content scripts can indeed fill forms and that fetch calls to the local server succeed. We may find that Chrome’s service worker cannot directly call fetch on install (if it’s not yet activated). We might need to use chrome.runtime.onStartup in the service worker to trigger the fetch, and ensure the service worker stays alive long enough (maybe by awaiting the fetch promise).

    Native Messaging (if needed): If in Firefox we skipped native messaging, in Chrome the same approach applies – we likely won’t need it since we’re using an HTTP server. But if we ever did, Chrome’s native messaging is available and similar to Firefox’s.

    Content Script Injection: Chrome’s manifest for content scripts is the same format as Firefox. The form detection and fill logic will remain identical. Just ensure not to use any Firefox-specific DOM APIs (we aren’t; standard DOM is fine).

    Options Page: Chrome supports an options_page (for MV2) or options_ui (for MV3) in the manifest just like Firefox. The same HTML/JS will work. Chrome opens it in a separate tab by default (or in a popup if open_in_tab:false, but Chrome actually always opens options in a full tab, unlike Firefox which can do a popup). Minor UI difference but no code changes needed. The communication to the server via fetch will work the same.

    Storage Format: The local server is independent of browser, so no changes there. The Chrome extension will talk to the same server on localhost.

Overall, the design is largely browser-agnostic. By using web standards (HTTP, fetch, and content scripts) and avoiding browser-proprietary technologies, we make the porting straightforward. The main differences are in extension manifest and background script lifecycles between Firefox and Chrome, which we have accounted for. Documentation will be updated to indicate how to load the extension in Chrome (likely via Developer Mode in chrome://extensions for testing, or via the Chrome Web Store for distribution).
Summary of Cross-Browser Compatibility

    Use Manifest V3 syntax for background scripts (service worker), content scripts, and host permissions – compatible with Chrome, Firefox, Edge.

    Use polyfills or simple code patterns to abstract API differences (browser vs chrome).

    Test the fetch workflow on both browsers to ensure CORS and permissions are handled (in both cases, including "http://localhost:5000/*" in manifest does the job).

    Keep the core logic (data sync, form fill) in plain JavaScript that works in all modern browsers.

By following these practices, the FormAgent extension’s codebase can be largely shared between Firefox and Chrome, with only the manifest and small tweaks changed. This allows easier maintenance and ensures the extension behaves consistently across browsers.
Conclusion

This design document outlines a comprehensive plan for implementing the FormAgent browser extension with a local server backend. The solution provides a maintainable separation of concerns: the extension focuses on browser interactions (detecting and filling forms, providing UI for data input), while the local server manages data storage and retrieval. The communication between them is done through standard HTTP calls, which keeps the system modular and easy to debug (you can test the server API independently of the extension, for example).

With this design, users will gain the convenience of automatic form filling using their personal data, without having to trust a cloud service or store sensitive information remotely. All data stays on their machine, and the integration is seamless once set up. Furthermore, the architecture is poised to evolve – for instance, an AI component could be introduced later to intelligently decide how to fill more complex forms using the data, simply by querying the same local server. The extension can also be extended to Chrome and other browsers with minimal changes, as detailed above.

By following the above specifications and workflow, the implementation of FormAgent’s extension mode will result in a powerful yet privacy-preserving form autofill solution. This document can serve as a blueprint for development and as a reference for the FormAgent wiki, ensuring all contributors understand how the pieces fit together.
# Threadline Browser Actions

This Chrome Manifest V3 extension lets Threadline capture browser page actions and replay a saved task in a new tab.

## Install in Chrome

1. Start the Threadline backend on `http://localhost:8000` and the frontend on `http://localhost:5173`.
2. Open `chrome://extensions` and enable **Developer mode**.
3. Choose **Load unpacked** and select this `browser-extension` folder.
4. In the extension's Details, set **Site access** to **On all sites**. Click the extension's **Reload** icon, then reload the Threadline page.
5. Choose **Capture something → Record & run**, and start a recording.
6. Switch to the Chrome page where the task happens. Stop from the Threadline tab to save the steps.
7. Choose **Review** beside the saved task, inspect its steps, then click **Run Agent**. Threadline opens a new tab and replays the recorded steps.

Chrome asks for permission to run on websites because the extension observes page controls and performs the replay. It sends recorded selectors and completed text field values to the local Threadline API only while a recording is active. Those values are stored in the local SQLite database.

## Limits

- This controls Chrome web pages, not native desktop apps, Safari, or other browsers.
- Replay is designed for a sequence in one browser tab. Tasks that open popups, switch tabs, or interact with embedded cross-origin frames may not replay correctly.
- Password, file, hidden, and commonly labeled secret fields are skipped. Do not record passwords, payment details, or private information.
- Replay uses recorded page URLs and element selectors. A site redesign, sign-in page, expired session, or dynamic content can make a step fail; Threadline stops and reports the failed step.
- A replay can submit a form or send a message. Threadline asks you to confirm before each run.
- File uploads, drag and drop, browser chrome controls, and actions inside cross-origin embedded frames are not captured.

Uninstall the extension from `chrome://extensions` to remove its access to pages. Captured task steps remain in Threadline until the workspace data is deleted.

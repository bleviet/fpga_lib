# Beginner's Guide to VS Code Extension Development

Welcome to the **FPGA IP Core Visual Editor** project! This guide is designed for developers who are new to VS Code extension development, **even if you have no prior experience with web technologies** like React or TypeScript.

This project is a great way to learn modern software development patterns.

---

## 1. The Core Concept: The "Two Worlds"

A VS Code extension like this one isn't just one program. It's actually **two separate programs** running side-by-side that talk to each other.

### World 1: The "Extension Host" (The Manager)
*   **What it is:** This is the logic that runs in the background. It behaves like a standard script (e.g., Python or C++) but written in JavaScript/TypeScript.
*   **Role:** It manages files, talks to VS Code (e.g., "Open this file", "Show this error message"), and handles the heavy lifting.
*   **Limitation:** It cannot draw buttons, tables, or fancy UI. It has no screen!

### World 2: The "Webview" (The Screen)
*   **What it is:** This is basically a mini web browser embedded inside VS Code.
*   **Role:** It displays the user interface (the text boxes, dropdowns, and tables you see).
*   **Technology:** It uses **HTML** (structure), **CSS** (styling), and **React** (logic) to draw the screen.
*   **Limitation:** It is trapped in a "sandbox" for security. It cannot directly read user files on your hard drive.

---

## 2. A Crash Course in the Tech Stack

We use standard web technologies to build the "Screen" (World 2). Here is what they do:

### TypeScript (The Language)
You might know Python or C. **TypeScript** is very similar but built for the web.
*   It is "JavaScript with types".
*   In Python, you might write `def add(a, b):`. You don't know if `a` is a number or text.
*   In TypeScript, we write `function add(a: number, b: number)`. The computer checks your work *before* you run it, preventing many bugs.

### React (The UI Builder)
Instead of writing one giant HTML file, **React** lets us build the UI out of small, reusable **Components**. Think of them like Lego bricks.
*   **Component:** A small piece of UI, like a `Checkbox` or a `SaveButton`. We write the code for it once and reuse it everywhere.
*   **Props:** Data passed *down* into a component. Like arguments to a function. (e.g., Telling a Button component: `label="Save"`)
*   **State:** The memory of a component. (e.g., A Checkbox remembers if it is currently `checked` or `unchecked`).

### HTML & CSS (The Look & Feel)
*   **HTML:** The skeleton. It says "This is a heading", "This is a paragraph".
*   **CSS:** The skin. It says "Headings are bold and blue", "Paragraphs have 10px spacing".

---

## 3. How the Worlds Talk: Message Passing

Since "The Screen" (Webview) can't save files, and "The Manager" (Extension Host) can't see buttons, they must send messages to each other. Think of it like writing letters.

### Analogy: The Restaurant
*   **The Webview (You):** You are sitting at the table. You look at the menu and decide what you want. But you cannot go into the kitchen and cook it yourself.
*   **The Message:** You write your order on a slip of paper ("I want the Steak").
*   **The Extension Host (The Waiter/Kitchen):** The waiter takes your note, goes to the kitchen (File System), cooks the meal (Saves the file), and comes back to tell you "It's done!".

### In Code:
1.  **Frontend (React):** "User clicked Save! Send a message to the Manager."
    ```typescript
    vscode.postMessage({ command: 'save', data: myData });
    ```

2.  **Backend (Extension):** "I received a message! Oh, it's a 'save' command. I will write this data to the disk."
    ```typescript
    webview.onDidReceiveMessage(message => {
        if (message.command === 'save') {
            writeFile(message.data);
        }
    });
    ```

---

## 4. Project Structure (Where things live)

*   `src/extension.ts`: **The Entry Point**. This is where everything starts.
*   `src/providers/`: **The Manager's Code**. Logic for opening files and handling messages.
*   `src/webview/`: **The Screen's Code**. All the React components live here.
    *   `src/webview/components/`: Reusable UI bricks (Tables, Buttons).
    *   `src/webview/ipcore/IpCoreApp.tsx`: The main "page" for the editor.

---

## 5. How to Start Hacking

1.  **Open the project** in VS Code.
2.  Press **F5**. This launches a special "Debug Window" of VS Code with your extension loaded.
3.  **Open a `.yml` file** in that new window. You will see your editor!
4.  **Try changing something:**
    *   Go to `src/webview/ipcore/components/layout/NavigationSidebar.tsx`.
    *   Change a text label.
    *   Save the file.
    *   In the Debug Window, run the command **"Developer: Reload Window"**.
    *   See your change!

Happy Coding!

import time

from interpreter import interpreter

interpreter.llm.supports_vision = True
interpreter.shrink_images = True  # Faster but less accurate

interpreter.llm.model = "gpt-4-vision-preview"
interpreter.llm.api_key = ""

interpreter.llm.supports_functions = False
interpreter.llm.context_window = 110000
interpreter.llm.max_tokens = 4096
interpreter.auto_run = True

interpreter.force_task_completion = True
interpreter.force_task_completion_message = """Proceed with what you were doing (this is not confirmation, if you just asked me something). You CAN run code on my machine. If you want to run code, start your message with "```"! If the entire task is done, say exactly 'The task is done.' If you need some specific information (like username, message text, skill name, skill step, etc.) say EXACTLY 'Please provide more information.' If it's impossible, say 'The task is impossible.' (If I haven't provided a task, say exactly 'Let me know what you'd like to do next.') Otherwise keep going. CRITICAL: REMEMBER TO FOLLOW ALL PREVIOUS INSTRUCTIONS. If I'm teaching you something, remember to run the related `computer.skills.new_skill` function."""
interpreter.force_task_completion_breakers = [
    "The task is done.",
    "The task is impossible.",
    "Let me know what you'd like to do next.",
    "Please provide more information.",
]

interpreter.system_message = r"""

You are the 01, an executive assistant that can complete any task.
When you execute code, it will be executed on the user's machine. The user has given you full and complete permission to execute any code necessary to complete the task.
Run any code to achieve the goal, and if at first you don't succeed, try again and again.
You can install new packages.
Be concise. DO NOT MAKE PLANS. RUN CODE QUICKLY.
Try to spread complex tasks over multiple code blocks. Don't try to complex tasks in one go.
Manually summarize text.

Act like you can just answer any question, then run code (this is hidden from the user) to answer it.
Your responses should be very short, no more than 1-2 sentences long.
DO NOT USE MARKDOWN. ONLY WRITE PLAIN TEXT.

# GUI CONTROL (RARE)

You are a computer controlling language model. You can control the user's GUI.
You may use the `computer` module to control the user's keyboard and mouse, if the task **requires** it:

```python
computer.display.info() # Returns a list of connected monitors/Displays and their info (x and y cordinates, width, height, width_mm, height_mm, name). Use this to verify the monitors connected before using computer.display.view() when neccessary
computer.display.view() # Shows you what's on the screen (primary display by default), returns a `pil_image` `in case you need it (rarely). To get a specific display, use the parameter screen=DISPLAY_NUMBER (0 for primary monitor 1 and above for secondary monitors). **You almost always want to do this first!**
computer.keyboard.hotkey(" ", "command") # Opens spotlight
computer.keyboard.write("hello") # Uses keyboard to type the string
computer.keyboard.press("enter") # presses a key on the keyboard
computer.mouse.click("text onscreen") # This clicks on the UI element with that text. Use this **frequently** and get creative! To click a video, you could pass the *timestamp* (which is usually written on the thumbnail) into this.
computer.mouse.move("open recent >") # This moves the mouse over the UI element with that text. Many dropdowns will disappear if you click them. You have to hover over items to reveal more.
computer.mouse.click(x=500, y=500) # Use this very, very rarely. It's highly inaccurate
computer.mouse.click(icon="gear icon") # Moves mouse to the icon with that description. Use this very often
computer.mouse.scroll(-10) # Scrolls down. If you don't find some text on screen that you expected to be there, you probably want to do this
```

You are an image-based AI, you can see images.
Clicking text is the most reliable way to use the mouse— for example, clicking a URL's text you see in the URL bar, or some textarea's placeholder text (like "Search" to get into a search bar).
If you use `plt.show()`, the resulting image will be sent to you. However, if you use `PIL.Image.show()`, the resulting image will NOT be sent to you.
It is very important to make sure you are focused on the right application and window. Often, your first command should always be to explicitly switch to the correct application. On Macs, ALWAYS use Spotlight to switch applications.
When searching the web, use query parameters. For example, https://www.amazon.com/s?k=monitor

# SKILLS

Try to use the following special functions (or "skills") to complete your goals whenever possible.
THESE ARE ALREADY IMPORTED. YOU CAN CALL THEM INSTANTLY.

---
{{
import sys
import os
import json
import ast
from platformdirs import user_data_dir

directory = os.path.join(user_data_dir('open-interpreter'), 'skills')
if not os.path.exists(directory):
    os.mkdir(directory)

def get_function_info(file_path):
    with open(file_path, "r") as file:
        tree = ast.parse(file.read())
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
        for function in functions:
            docstring = ast.get_docstring(function)
            args = [arg.arg for arg in function.args.args]
            print(f"Function Name: {function.name}")
            print(f"Arguments: {args}")
            print(f"Docstring: {docstring}")
            print("---")

files = os.listdir(directory)
for file in files:
    if file.endswith(".py"):
        file_path = os.path.join(directory, file)
        get_function_info(file_path)
}}

YOU can add to the above list of skills by defining a python function. The function will be saved as a skill.
Search all existing skills by running `computer.skills.search(query)`.

**Teach Mode**

If the USER says they want to teach you something, exactly write the following, including the markdown code block:

---
One moment.
```python
computer.skills.new_skill.create()
```
---

If you decide to make a skill yourself to help the user, simply define a python function. `computer.skills.new_skill.create()` is for user-described skills.


# MANUAL TASKS

Translate things to other languages INSTANTLY and MANUALLY. Don't ever try to use a translation tool.
Summarize things manually. DO NOT use a summarizer tool.

# CRITICAL NOTES

Code output, despite being sent to you by the user, cannot be seen by the user. You NEED to tell the user about the output of some code, even if it's exact. >>The user does not have a screen.<<
ALWAYS REMEMBER: You are running on a device called the O1, where the interface is entirely speech-based. Make your responses to the user VERY short. DO NOT PLAN. BE CONCISE. WRITE CODE TO RUN IT.
Try multiple methods before saying the task is impossible. **You can do it!**

""".strip()


# Check if required packages are installed

# THERE IS AN INCONSISTENCY HERE.
# We should be testing if they import WITHIN OI's computer, not here.

packages = ["cv2", "plyer", "pyautogui", "pyperclip", "pywinctl"]
missing_packages = []
for package in packages:
    try:
        __import__(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    interpreter.display_message(
        f"> **Missing Package(s): {', '.join(['`' + p + '`' for p in missing_packages])}**\n\nThese packages are required for OS Control.\n\nInstall them?\n"
    )
    user_input = input("(y/n) > ")
    if user_input.lower() != "y":
        print("\nPlease try to install them manually.\n\n")
        time.sleep(2)
        print("Attempting to start OS control anyway...\n\n")

    for pip_name in ["pip", "pip3"]:
        command = f"{pip_name} install 'open-interpreter[os]'"

        interpreter.computer.run("shell", command, display=True)

        got_em = True
        for package in missing_packages:
            try:
                __import__(package)
            except ImportError:
                got_em = False
        if got_em:
            break

    missing_packages = []
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages != []:
        print(
            "\n\nWarning: The following packages could not be installed:",
            ", ".join(missing_packages),
        )
        print("\nPlease try to install them manually.\n\n")
        time.sleep(2)
        print("Attempting to start OS control anyway...\n\n")

interpreter.display_message("> `This profile simulates the 01.`")

# Should we explore other options for ^ these kinds of tags?
# Like:

# from rich import box
# from rich.console import Console
# from rich.panel import Panel
# console = Console()
# print(">\n\n")
# console.print(Panel("[bold italic white on black]OS CONTROL[/bold italic white on black] Enabled", box=box.SQUARE, expand=False), style="white on black")
# print(">\n\n")
# console.print(Panel("[bold italic white on black]OS CONTROL[/bold italic white on black] Enabled", box=box.HEAVY, expand=False), style="white on black")
# print(">\n\n")
# console.print(Panel("[bold italic white on black]OS CONTROL[/bold italic white on black] Enabled", box=box.DOUBLE, expand=False), style="white on black")
# print(">\n\n")
# console.print(Panel("[bold italic white on black]OS CONTROL[/bold italic white on black] Enabled", box=box.SQUARE, expand=False), style="white on black")

if not interpreter.offline and not interpreter.auto_run:
    api_message = "To find items on the screen, Open Interpreter has been instructed to send screenshots to [api.openinterpreter.com](https://api.openinterpreter.com/) (we do not store them). Add `--offline` to attempt this locally."
    interpreter.display_message(api_message)
    print("")

if not interpreter.auto_run:
    screen_recording_message = "**Make sure that screen recording permissions are enabled for your Terminal or Python environment.**"
    interpreter.display_message(screen_recording_message)
    print("")

# # FOR TESTING ONLY
# # Install Open Interpreter from GitHub
# for chunk in interpreter.computer.run(
#     "shell",
#     "pip install git+https://github.com/KillianLucas/open-interpreter.git",
# ):
#     if chunk.get("format") != "active_line":
#         print(chunk.get("content"))

import os

from platformdirs import user_data_dir

directory = os.path.join(user_data_dir("open-interpreter"), "skills")
interpreter.computer.skills.path = directory
interpreter.computer.skills.import_skills()


# Initialize user's task list
interpreter.computer.run(
    language="python",
    code="tasks = []",
    display=interpreter.verbose,
)

# Give it access to the computer via Python
interpreter.computer.run(
    language="python",
    code="import time\nfrom interpreter import interpreter\ncomputer = interpreter.computer",  # We ask it to use time, so
    display=interpreter.verbose,
)

if not interpreter.auto_run:
    interpreter.display_message(
        "**Warning:** In this mode, Open Interpreter will not require approval before performing actions. Be ready to close your terminal."
    )
    print("")  # < - Aesthetic choice

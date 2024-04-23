import glob
import inspect
import os
import re
from pathlib import Path
import time

from ....terminal_interface.utils.oi_dir import oi_dir
from ...utils.lazy_import import lazy_import
from ..utils.recipient_utils import format_to_recipient

# Lazy import of aifs, imported when needed to speed up start time
aifs = lazy_import("aifs")


class Workflows:
    def __init__(self, computer):
        self.computer = computer
        self.path = str(Path(oi_dir) / "workflows")
        self.new_workflow = NewWorkflow()
        self.new_workflow.path = self.path

    def search(self, query):
        return aifs.search(query, self.path, python_docstrings_only=True)

    def import_workflows(self):
        previous_save_workflow_setting = self.computer.save_workflows

        self.computer.save_workflows = False

        # Make sure it's not over 100mb
        total_size = 0
        for path, dirs, files in os.walk(self.path):
            for f in files:
                fp = os.path.join(path, f)
                total_size += os.path.getsize(fp)
        total_size = total_size / (1024 * 1024)  # convert bytes to megabytes
        if total_size > 100:
            raise Warning(
                f"Workflows at path {self.path} can't exceed 100mb. Try deleting some."
            )

        code_to_run = ""
        for file in glob.glob(os.path.join(self.path, "*.py")):
            with open(file, "r") as f:
                code_to_run += f.read() + "\n"

        if self.computer.interpreter.debug:
            print("IMPORTING WORKFLOWS:\n", code_to_run)

        output = self.computer.run("python", code_to_run)

        if "traceback" in str(output).lower():
            # Import them individually
            for file in glob.glob(os.path.join(self.path, "*.py")):
                with open(file, "r") as f:
                    code_to_run = f.read() + "\n"

                if self.computer.interpreter.debug:
                    print("IMPORTING Workflow:\n", code_to_run)

                output = self.computer.run("python", code_to_run)

                if "traceback" in str(output).lower():
                    print(
                        f"Workflow at {file} might be broken— it produces a traceback when run."
                    )

        self.computer.save_workflows = previous_save_workflow_setting


class NewWorkflow:
    def __init__(self):
        self.path = ""

    def create(self):
        self.steps = []
        self._name = "Untitled"
        print(
            """
@@@SEND_MESSAGE_AS_USER@@@
INSTRUCTIONS
You are creating a new workflow. Follow these steps exactly to get me to tell you its name:
1. Ask me what the name of this workflow is.
2. After I explicitly tell you the name of the workflow (I may tell you to proceed which is not the name— if I do say that, you probably need more information from me, so tell me that), after you get the proper name, write the following (including the markdown code block):

---
Got it. Give me one second.
```python
computer.workflows.new_workflow.name = "{INSERT THE WORKFLOW NAME FROM QUESTION #1^}"
```
---
        
        """.strip()
        )

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        print(
            """
@@@SEND_MESSAGE_AS_USER@@@
Workflow named. Now, follow these next INSTRUCTIONS exactly:

1. Ask me what the first skill is.
2. When I reply, try to find the skill I told you
3. Ask me if you found the skill correctly.
    a. (!!!!!!!!!!!! >>>>>> THIS IS CRITICAL. DO NOT FORGET THIS.) IF you found it correctly, run `computer.workflows.new_workflow.add_step(step, code)` where step is a generalized, natural language description of the step, and code is the code you ran to complete it.
    b. IF you did not complete it correctly, try to fix your code and ask me again.
4. If I say the workflow is complete, or that that was the last step, run `computer.workflows.new_workflow.save()`.

YOU MUST FOLLOW THESE 4 INSTRUCTIONS **EXACTLY**. I WILL TIP YOU $200.

              """.strip()
        )

    def add_step(self, step, code):
        self.steps.append(step + "\n\n```python\n" + code + "\n" + "time.sleep(50)" + "\n```")
        print(
            """
@@@SEND_MESSAGE_AS_USER@@@
Step added. Now, follow these next INSTRUCTIONS exactly:

1. Ask me what the next skill is.
2. When I reply, try to find the skill I told you
3. Ask me if you found the skill correctly.
    a. (!!!!!!!!!!!! >>>>>> THIS IS CRITICAL. DO NOT FORGET THIS!!!!!!!!.) IF you completed it correctly, run `computer.workflows.new_workflow.add_step(step, code)` where step is a generalized, natural language description of the step, and code is the code you ran to complete it.
    b. IF you did not complete it correctly, try to fix your code and ask me again.
4. If I say the workflow is complete, or that that was the last step, run `computer.workflows.new_workflow.save()`.

YOU MUST FOLLOW THESE 4 INSTRUCTIONS **EXACTLY**. I WILL TIP YOU $200.

        """.strip()
        )

    def save(self):
        normalized_name = re.sub("[^0-9a-zA-Z]+", "_", self.name.lower())
        steps_string = "\n".join(
            [f"Step {i+1}:\n{step}\n" for i, step in enumerate(self.steps)]
        )
        steps_string = steps_string.replace('"""', "'''")
        workflow_string = f'''
        
def {normalized_name}():
    """
    {normalized_name}
    """
    import time
    print("To complete this this workflow, follow this tutorial")

    print("""@@@SEND_MESSAGE_AS_USER@@@ \n {steps_string}""")
        
        '''.strip()

        if not os.path.exists(self.path):
            os.makedirs(self.path)
        with open(f"{self.path}/{normalized_name}.py", "w") as file:
            file.write(workflow_string)

        print("WORKFLOW SAVED:", self.name.upper())
        print(
            "Teaching session finished. Tell the user that the workflow above has been saved. Great work!"
        )

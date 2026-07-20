import Util.FileManager as FileManager
import ipywidgets as widgets
import time
import threading

try:
    from IPython.display import display, clear_output
except ImportError:
    display = clear_output = None

def problem_creator():
    def reset_button(button, description, tooltip, icon=None, sleep=False):
        if sleep:
            time.sleep(1)
        button.disabled = False
        button.description = description
        button.tooltip = tooltip
        button.icon = icon

    def on_button_click(button, button_info, problem_number=None):
        # Disable and show loading state
        button.disabled = True
        button.description = "Creating file..."
        button.tooltip = "Creating file..."
        button.icon = "spinner"

        threading.Thread(target=reset_button, args=(button, *button_info, True)).start()

        problem_output = FileManager.create_problem(problem_number)

        status_label.value= problem_output

    def on_next_problem(button):
        on_button_click(button, next_problem_button_info)

    next_problem_button = widgets.Button()
    next_problem_button_info = ["Create", "Create the next available problem", "plus"]
    reset_button(next_problem_button, *next_problem_button_info)
    next_problem_button.on_click(on_next_problem)

    description_text = widgets.HTML(
        value="<span style='font-size:17px; '>Create a file for the next unsolved problem:</span>"
    )

    problem_creation_box = widgets.HBox(
        children=[description_text, next_problem_button],
        layout=widgets.Layout(
            align_items="center",
            justify_content="space-between",
            width="100%",
            padding="14px 18px",
            border="1px solid #424242",
            border_radius="10px",
            background_color="#fafafa"
        )
    )

    def on_specific_problem(button):
        on_button_click(button, specific_problem_button_info, specific_problem_text_box.value)

    specific_problem_button = widgets.Button()
    specific_problem_button_info = ["Create", "Create the specified problem", "plus"]
    reset_button(specific_problem_button, *specific_problem_button_info)
    specific_problem_button.on_click(on_specific_problem)

    specific_problem_text_box = widgets.IntText(value=FileManager.get_next_problem())
    specific_problem_box = widgets.HBox(
        children=[specific_problem_text_box, specific_problem_button],
        layout=widgets.Layout(
            align_items="center",
            justify_content="space-between",
            width="100%",
            padding="14px 18px"
        )
    )

    accordion = widgets.Accordion(children=[specific_problem_box],
                                  layout=widgets.Layout(width="100%", margin="14px 0 0 0"))
    accordion.set_title(0, "Create a specific problem")

    status_label = widgets.Label(
        value="",
        layout=widgets.Layout(margin="10px 0 0 5px")
    )

    box_children = [problem_creation_box, accordion, status_label]

    total_problem_creation_box = widgets.VBox(
        children= box_children,
        layout=widgets.Layout(
            align_items="stretch",
            width="100%"
        )
    )

    # Outer wrapper to create padding between cell and widgets
    page_wrapper = widgets.Box(
        children=[total_problem_creation_box],
        layout=widgets.Layout(padding="14px 0 0 0", width="100%")
    )

    return page_wrapper

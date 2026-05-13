__author__ = "Adel Tchernitsky"


import tkinter as tk
from tkinter import ttk, messagebox
from queue import Queue, Empty


request_queue = Queue()
response_queue = Queue()
root = None
current_frame = None


# Pallet of colors
BG_COLOR = "#121826"
CARD_COLOR = "#1f2937"
TEXT_COLOR = "#eef2ff"
SUBTEXT_COLOR = "#94a3b8"
ACCENT_COLOR = "#60a5fa"
ACCENT_HOVER = "#3b82f6"
SUCCESS_COLOR = "#22c55e"
ERROR_COLOR = "#f97316"
INPUT_BG = "#0f172a"
INPUT_BORDER = "#334155"
LIST_BG = "#111827"
LIST_FG = "#eef2ff"
SELECT_BG = "#2563eb"
SELECT_FG = "#f8fafc"

# Fonts
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SUBTITLE = ("Segoe UI", 11)
FONT_CARD_TITLE = ("Segoe UI", 14, "bold")
FONT_BODY = ("Segoe UI", 11)
FONT_BUTTON = ("Segoe UI", 11, "bold")


def initialize_gui():
    """
    Initialize the main Tkinter window, configure styles, and start queue polling
    :return: The root GUI window
    """
    global root
    root = tk.Tk()
    root.title("CTF Game Client")
    root.geometry("740x620")
    root.minsize(720, 560)
    root.configure(bg=BG_COLOR)
    configure_style()

    check_queue()
    return root


def configure_style():
    """
    Configure ttk styles (colors, fonts, widgets) for the application
    """
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TFrame", background=BG_COLOR)
    style.configure("Card.TFrame", background=CARD_COLOR, relief="flat")
    style.configure("Header.TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=FONT_TITLE)
    style.configure("Subtitle.TLabel", background=BG_COLOR, foreground=SUBTEXT_COLOR, font=FONT_SUBTITLE)
    style.configure("CardHeader.TLabel", background=CARD_COLOR, foreground=TEXT_COLOR, font=FONT_CARD_TITLE)
    style.configure("CardText.TLabel", background=CARD_COLOR, foreground=TEXT_COLOR, font=FONT_BODY, wraplength=640)

    style.configure("Accent.TButton", background=ACCENT_COLOR, foreground=TEXT_COLOR, font=FONT_BUTTON,
                    borderwidth=0, focusthickness=3, focuscolor=ACCENT_HOVER)
    style.map("Accent.TButton",
              background=[("active", ACCENT_HOVER), ("disabled", "#475569")])

    style.configure("Secondary.TButton", background="#334155", foreground=TEXT_COLOR, font=FONT_BUTTON,
                    borderwidth=0)
    style.map("Secondary.TButton",
              background=[("active", "#475569")])

    style.configure("Card.TLabelframe", background=CARD_COLOR, borderwidth=0)
    style.configure("Card.TLabelframe.Label", background=CARD_COLOR, foreground=SUBTEXT_COLOR, font=FONT_BODY)
    style.configure("TEntry", fieldbackground=INPUT_BG, foreground=TEXT_COLOR, background=INPUT_BG,
                    bordercolor=INPUT_BORDER, lightcolor=ACCENT_COLOR, darkcolor=INPUT_BORDER)
    style.configure("TLabel", background=BG_COLOR, foreground=TEXT_COLOR, font=FONT_BODY)


def check_queue():
    """
    Continuously gets data from the request queue and trigger the appropriate UI updates
    """
    try:
        while True:
            request_type, data = request_queue.get_nowait()
            if request_type == "show_welcome_screen":
                show_welcome_screen()
            elif request_type == "show_ctf_choice":
                show_ctf_choice(data)
            elif request_type == "show_question":
                show_question(data)
            elif request_type == "show_response":
                show_response(data)
            elif request_type == "show_final_score":
                show_final_score(data)
            elif request_type == "show_error":
                show_error(data)
            elif request_type == "close_app":
                root.quit()

    except Empty:
        pass

    root.after(100, check_queue)


def clear_frame():
    """
    Destroy the current frame and create a new empty frame for the next screen
    """
    global current_frame
    if current_frame:
        current_frame.destroy()

    current_frame = ttk.Frame(root)
    current_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)


def create_header(title, subtitle):
    """
    Create and display a header section with title and subtitle
    :param title: Main heading text
    :param subtitle: Secondary descriptive text
    """
    header_frame = ttk.Frame(current_frame, style="Card.TFrame")
    header_frame.pack(fill=tk.X, pady=(0, 18), ipadx=14, ipady=14)

    title_label = ttk.Label(header_frame, text=title, style="Header.TLabel")
    title_label.pack(anchor="w")

    subtitle_label = ttk.Label(header_frame, text=subtitle, style="Subtitle.TLabel")
    subtitle_label.pack(anchor="w", pady=(6, 0))


def unbind_enter():
    """
    Remove any existing binding for the Enter key
    """
    if root:
        root.unbind("<Return>")


def show_instructions_window():
    """Open a modal window displaying game instructions."""
    instructions_window = tk.Toplevel(root)
    instructions_window.title("Game Instructions")
    instructions_window.configure(bg=BG_COLOR)
    instructions_window.geometry("640x670")  # Instruction window size
    instructions_window.minsize(620, 480)
    instructions_window.transient(root)
    instructions_window.grab_set()

    container = ttk.Frame(instructions_window, style="Card.TFrame")
    container.pack(fill=tk.BOTH, expand=True, padx=18, pady=18)

    title_label = ttk.Label(container, text="How to Play", style="CardHeader.TLabel")
    title_label.pack(anchor="w", pady=(0, 8))

    intro_text = (
        "Welcome to the CTF game!\n\n"
        "Choose a CTF category and answer each question with the correct flag format. "
        "Questions appear one at a time, and your score is tracked as you progress."
    )
    intro_label = ttk.Label(container, text=intro_text, style="CardText.TLabel", wraplength=590, justify=tk.LEFT)
    intro_label.pack(anchor="w", pady=(0, 14))

    instructions = [
        "1. Enter a unique username to start. Every username is stored as a separate player.",
        "2. Select a CTF from the list to begin the challenge.",
        "3. Answer each question using the required format: CTF{your_answer}.",
        "4. If you enter a new username, your progress and stages are saved separately for that user.",
        "5. Use the Request Hint button to get a helpful hint when available.",
        "6. After each question, continue to the next stage until the game ends.",
        "7. Answers are case-sensitive and should be entered exactly in the accepted flag format.",
        "8. Keep your answers concise and avoid extra spaces around the flag.",
    ]

    for item in instructions:
        bullet_label = ttk.Label(container, text=item, style="CardText.TLabel", wraplength=590, justify=tk.LEFT)
        bullet_label.pack(anchor="w", pady=(0, 8))

    close_button = ttk.Button(container, text="Close Instructions", command=instructions_window.destroy, style="Accent.TButton")
    close_button.pack(pady=(14, 0), ipadx=10, ipady=8, anchor="e")

    close_button.focus_set()
    instructions_window.wait_window()


def show_welcome_screen():
    """
    Display the welcome screen with Sign Up and Log In options
    """
    clear_frame()
    unbind_enter()
    create_header("Welcome to the CTF System", "Choose an option to continue.")

    card = ttk.Frame(current_frame, style="Card.TFrame")
    card.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    button_frame = ttk.Frame(card, style="Card.TFrame")
    button_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=18)

    def sign_up():
        show_sign_up()

    def log_in():
        show_log_in()

    sign_up_button = ttk.Button(button_frame, text="Sign Up", command=sign_up, style="Accent.TButton")
    sign_up_button.pack(pady=(20, 10), ipadx=20, ipady=10)

    log_in_button = ttk.Button(button_frame, text="Log In", command=log_in, style="Secondary.TButton")
    log_in_button.pack(pady=(10, 20), ipadx=20, ipady=10)


def show_sign_up():
    """
    Display the sign up screen for creating new accounts
    """
    clear_frame()
    unbind_enter()
    create_header("Sign Up", "Create a new account to join the CTF system.")

    card = ttk.Frame(current_frame, style="Card.TFrame")
    card.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    input_frame = ttk.Frame(card, style="Card.TFrame")
    input_frame.pack(fill=tk.X, padx=24, pady=18)

    username_var = tk.StringVar()
    password_var = tk.StringVar()

    ttk.Label(input_frame, text="Username:", style="CardText.TLabel").pack(anchor="w", pady=(10, 0))
    username_entry = ttk.Entry(input_frame, textvariable=username_var, width=34)
    username_entry.configure(font=FONT_BODY)
    username_entry.pack(fill=tk.X, pady=(5, 10))
    username_entry.focus()

    ttk.Label(input_frame, text="Password:", style="CardText.TLabel").pack(anchor="w")
    password_entry = ttk.Entry(input_frame, textvariable=password_var, show="*", width=34)
    password_entry.configure(font=FONT_BODY)
    password_entry.pack(fill=tk.X, pady=(5, 10))

    def submit_sign_up():
        username = username_var.get().strip()
        password = password_var.get().strip()
        if not username or not password:
            messagebox.showwarning("Input Required", "Please enter both username and password.")
            return

        from shared.Protocol import SignUpRequest
        response_queue.put(SignUpRequest(username, password))
        username_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)

    submit_button = ttk.Button(card, text="Sign Up", command=submit_sign_up, style="Accent.TButton")
    submit_button.pack(pady=(0, 20), ipadx=10, ipady=8)

    password_entry.bind("<Return>", lambda e: submit_sign_up())


def show_log_in():
    """
    Display the log in screen for existing users
    """
    clear_frame()
    unbind_enter()
    create_header("Log In", "Enter your credentials to access the CTF system.")

    card = ttk.Frame(current_frame, style="Card.TFrame")
    card.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    input_frame = ttk.Frame(card, style="Card.TFrame")
    input_frame.pack(fill=tk.X, padx=24, pady=18)

    username_var = tk.StringVar()
    password_var = tk.StringVar()

    ttk.Label(input_frame, text="Username:", style="CardText.TLabel").pack(anchor="w", pady=(10, 0))
    username_entry = ttk.Entry(input_frame, textvariable=username_var, width=34)
    username_entry.configure(font=FONT_BODY)
    username_entry.pack(fill=tk.X, pady=(5, 10))
    username_entry.focus()

    ttk.Label(input_frame, text="Password:", style="CardText.TLabel").pack(anchor="w")
    password_entry = ttk.Entry(input_frame, textvariable=password_var, show="*", width=34)
    password_entry.configure(font=FONT_BODY)
    password_entry.pack(fill=tk.X, pady=(5, 10))

    def submit_log_in():
        username = username_var.get().strip()
        password = password_var.get().strip()
        if not username or not password:
            messagebox.showwarning("Input Required", "Please enter both username and password.")
            return

        from shared.Protocol import LogInRequest
        response_queue.put(LogInRequest(username, password))
        username_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)

    submit_button = ttk.Button(card, text="Log In", command=submit_log_in, style="Accent.TButton")
    submit_button.pack(pady=(0, 20), ipadx=10, ipady=8)

    password_entry.bind("<Return>", lambda e: submit_log_in())


def show_ctf_choice(message):
    """
    Display a list of available CTF challenges and send selected choice
    :param message: Object containing CTF categories and names
    """
    clear_frame()
    unbind_enter()
    create_header("Choose Your CTF", "Browse the available challenges and select one to start.")

    card = ttk.Frame(current_frame, style="Card.TFrame")
    card.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    list_frame = ttk.Frame(card, style="Card.TFrame")
    list_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=18)

    scrollbar = ttk.Scrollbar(list_frame, style="Vertical.TScrollbar")
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    ctf_listbox = tk.Listbox(list_frame, background=LIST_BG, foreground=LIST_FG, selectbackground=SELECT_BG,
                             selectforeground=SELECT_FG, activestyle="none", font=FONT_BODY, borderwidth=0,
                             highlightthickness=0)
    ctf_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=ctf_listbox.yview)
    ctf_listbox.config(yscrollcommand=scrollbar.set)

    flat_list = []
    for category, ctfs in message.categories.items():
        ctf_listbox.insert(tk.END, f"--- {category.upper()} ---")
        ctf_listbox.itemconfig(ctf_listbox.size() - 1, foreground="#93c5fd")
        for ctf in ctfs:
            clean_name = ctf.split(" (")[0]
            ctf_listbox.insert(tk.END, f"  {ctf}")
            flat_list.append((clean_name, ctf))

    def submit_choice(event=None):
        selection = ctf_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select a CTF.")
            return "break"

        selected_index = selection[0]
        actual_index = 0
        for i, item in enumerate(ctf_listbox.get(0, tk.END)):
            if not item.startswith("---"):
                if i == selected_index:
                    if actual_index < len(flat_list):
                        chosen = flat_list[actual_index][0]
                        response_queue.put(chosen)

                    return "break"
                actual_index += 1

    ctf_listbox.bind("<Return>", submit_choice)
    ctf_listbox.bind("<Double-Button-1>", submit_choice)
    ctf_listbox.focus_set()

    button_frame = ttk.Frame(card, style="Card.TFrame")
    button_frame.pack(fill=tk.X, padx=24, pady=(0, 20))

    submit_button = ttk.Button(button_frame, text="Select CTF", command=submit_choice, style="Accent.TButton")
    submit_button.pack(side=tk.LEFT, padx=(0, 6), ipadx=10, ipady=8)

    instructions_button = ttk.Button(button_frame, text="Instructions", command=show_instructions_window, style="Secondary.TButton")
    instructions_button.pack(side=tk.LEFT, ipadx=10, ipady=8)

    root.bind("<Return>", lambda e: submit_choice())


def show_question(message):
    """
    Display a question, optional hint, and input for user's answer
    :param message: Object containing question text, hint, and metadata
    """
    clear_frame()
    create_header(f"Question {message.question_number}", "Submit the correct answer or request a hint.")

    card = ttk.Frame(current_frame, style="Card.TFrame")
    card.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    question_text = ttk.Label(card, text=message.question, style="CardText.TLabel", wraplength=660, justify=tk.LEFT)
    question_text.pack(fill=tk.X, padx=24, pady=(18, 14))

    if message.hint:
        hint_frame = ttk.Labelframe(card, text="Hint", style="Card.TLabelframe", padding=14)
        hint_frame.pack(fill=tk.X, padx=24, pady=(0, 18))
        hint_label = ttk.Label(hint_frame, text=message.hint, style="CardText.TLabel", wraplength=620, justify=tk.LEFT, foreground="#86efac")
        hint_label.pack()

    answer_frame = ttk.Labelframe(card, text="Your Answer", style="Card.TLabelframe", padding=14)
    answer_frame.pack(fill=tk.X, padx=24, pady=(0, 18))

    answer_var = tk.StringVar()
    answer_entry = ttk.Entry(answer_frame, textvariable=answer_var, width=52)
    answer_entry.configure(font=FONT_BODY)
    answer_entry.pack(fill=tk.X)
    answer_entry.focus()

    button_frame = ttk.Frame(card, style="Card.TFrame")
    button_frame.pack(fill=tk.X, padx=24, pady=(0, 20))

    def submit_answer():
        answer = answer_var.get().strip()
        if not answer:
            messagebox.showwarning("Input Required", "Please enter an answer.")
            return
        response_queue.put(answer)
        answer_entry.delete(0, tk.END)

    submit_button = ttk.Button(button_frame, text="Submit Answer", command=submit_answer, style="Accent.TButton")
    submit_button.pack(side=tk.LEFT, padx=(0, 8), ipadx=10, ipady=8)

    if not message.hint:
        hint_button = ttk.Button(button_frame, text="Request Hint", command=lambda: response_queue.put("hint"), style="Secondary.TButton")
        hint_button.pack(side=tk.LEFT, ipadx=10, ipady=8)

    answer_entry.bind("<Return>", lambda e: submit_answer())


def show_response(message):
    """
    Display feedback for the submitted answer (correct/incorrect)
    :param message: Object containing correctness, question, and points
    """
    clear_frame()
    unbind_enter()
    create_header("Answer Feedback", "Review your answer result before continuing.")

    card = ttk.Frame(current_frame, style="Card.TFrame")
    card.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    is_correct = message.is_correct
    result_text = "✓ Correct!" if is_correct else "✗ Incorrect"
    result_color = SUCCESS_COLOR if is_correct else ERROR_COLOR

    result_label = ttk.Label(card, text=result_text, font=("Segoe UI", 22, "bold"), foreground=result_color, background=CARD_COLOR)
    result_label.pack(padx=24, pady=(24, 12), anchor="w")

    question_label = ttk.Label(card, text="Question", style="CardHeader.TLabel")
    question_label.pack(padx=24, pady=(8, 4), anchor="w")

    question_text = ttk.Label(card, text=message.question, style="CardText.TLabel", wraplength=660, justify=tk.LEFT)
    question_text.pack(fill=tk.X, padx=24, pady=(0, 18))

    points_label = ttk.Label(card, text=f"Points for this question: {message.points_for_correct_answer}", style="CardText.TLabel")
    points_label.pack(padx=24, pady=(0, 24), anchor="w")

    def continue_action(event=None):
        response_queue.put(None)

    continue_button = ttk.Button(card, text="Continue", command=continue_action, style="Accent.TButton")
    continue_button.pack(padx=24, pady=(0, 24), ipadx=10, ipady=8, anchor="w")

    root.bind("<Return>", continue_action)


def show_final_score(message):
    """
    Display the final score and exit option.
    :param message: Object containing the final score
    """
    clear_frame()
    unbind_enter()
    create_header("Game Completed", "Well done! Review your final score below.")

    card = ttk.Frame(current_frame, style="Card.TFrame")
    card.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    score_label = ttk.Label(card, text=f"{message.score}", font=("Segoe UI", 52, "bold"), foreground=ACCENT_COLOR, background=CARD_COLOR)
    score_label.pack(padx=24, pady=(24, 10))

    detail_label = ttk.Label(card, text="Your final score has been recorded.", style="CardText.TLabel")
    detail_label.pack(padx=24, pady=(0, 20), anchor="w")

    def exit_action(event=None):
        response_queue.put(None)
        root.quit()

    exit_button = ttk.Button(card, text="Exit Game", command=exit_action, style="Accent.TButton")
    exit_button.pack(padx=24, pady=(0, 24), ipadx=10, ipady=8, anchor="w")

    root.bind("<Return>", exit_action)


def show_error(message):
    """
    Display an error message and return to username input screen
    :param message: Object containing error details
    """
    error_text = message.error
    if hasattr(message, 'user_name') and message.user_name:
        error_text = f"Username '{message.user_name}' is already taken. Please try another."
    messagebox.showerror("Error", error_text)
    show_welcome_screen()


def handle_authentication_choice():
    """
    Request authentication choice from GUI and wait for user response
    :return: SignUpRequest or LogInRequest
    """
    request_queue.put(("show_welcome_screen", None))
    return response_queue.get()


def handle_ctf_choice(message):
    """
    Request CTF selection from GUI and wait for user choice
    :param message: Object containing CTF options
    :return: str - Selected CTF name
    """
    request_queue.put(("show_ctf_choice", message))
    return response_queue.get()


def get_answer(message):
    """
    Request answer input from GUI and wait for user response
    :param message: Object containing the question
    :return: str - User's answer or 'hint' request
    """
    request_queue.put(("show_question", message))
    return response_queue.get()


def handle_show_result(message):
    """
    Display answer result and wait for user to continue
    :param message: Object containing result details
    """
    request_queue.put(("show_response", message))
    response_queue.get()


def handle_show_final_score(message):
    """
    Display final score and wait for user to exit
    :param message: Object containing score
    """
    request_queue.put(("show_final_score", message))
    response_queue.get()


def handle_show_error(message):
    """
    Send an error message to the GUI for display
    :param message: Object containing error details
    """
    request_queue.put(("show_error", message))

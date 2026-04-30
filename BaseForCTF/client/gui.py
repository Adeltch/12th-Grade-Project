__author__ = "Adel Tchernitsky"


import tkinter as tk
from tkinter import ttk, messagebox
from queue import Queue, Empty


request_queue = Queue()
response_queue = Queue()
root = None
current_frame = None


def initialize_gui():
    global root
    root = tk.Tk()
    root.title("CTF Game Client")
    root.geometry("600x500")
    root.resizable(True, True)
    check_queue()
    return root


def check_queue():
    try:
        while True:
            request_type, data = request_queue.get_nowait()
            
            if request_type == "show_username_input":
                show_username_input()
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
    global current_frame
    if current_frame:
        current_frame.destroy()
    current_frame = ttk.Frame(root)
    current_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


def show_username_input():
    clear_frame()
    
    title_label = ttk.Label(current_frame, text="Welcome to CTF Game", font=("Arial", 16, "bold"))
    title_label.pack(pady=20)
    
    instruction = ttk.Label(current_frame, text="Enter your username:", font=("Arial", 12))
    instruction.pack(pady=10)
    
    username_var = tk.StringVar()
    username_entry = ttk.Entry(current_frame, textvariable=username_var, width=40)
    username_entry.pack(pady=10)
    username_entry.focus()
    
    def submit_username():
        username = username_var.get().strip()
        if not username:
            messagebox.showwarning("Input Required", "Please enter a username.")
            return
        response_queue.put(username)
        username_entry.delete(0, tk.END)
    
    submit_button = ttk.Button(current_frame, text="Enter Game", command=submit_username)
    submit_button.pack(pady=10)
    
    username_entry.bind("<Return>", lambda e: submit_username())


def show_ctf_choice(message):
    clear_frame()
    
    title_label = ttk.Label(current_frame, text="Select a CTF Challenge", font=("Arial", 16, "bold"))
    title_label.pack(pady=15)
    
    list_frame = ttk.Frame(current_frame)
    list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    scrollbar = ttk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    ctf_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 11), height=15)
    ctf_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=ctf_listbox.yview)
    
    flat_list = []
    for category, ctfs in message.categories.items():
        ctf_listbox.insert(tk.END, f"--- {category.upper()} ---")
        ctf_listbox.itemconfig(ctf_listbox.size() - 1, {'fg': 'blue'})
        
        for ctf in ctfs:
            clean_name = ctf.split(" (")[0]
            ctf_listbox.insert(tk.END, f"  {ctf}")
            flat_list.append((clean_name, ctf))
    
    def submit_choice():
        selection = ctf_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Required", "Please select a CTF.")
            return
        
        selected_index = selection[0]
        actual_index = 0
        for i, item in enumerate(ctf_listbox.get(0, tk.END)):
            if not item.startswith("---"):
                if i == selected_index:
                    if actual_index < len(flat_list):
                        chosen = flat_list[actual_index][0]
                        response_queue.put(chosen)
                    return
                actual_index += 1
    
    button_frame = ttk.Frame(current_frame)
    button_frame.pack(pady=10)
    
    submit_button = ttk.Button(button_frame, text="Select CTF", command=submit_choice)
    submit_button.pack(side=tk.LEFT, padx=5)


def show_question(message):
    clear_frame()
    
    question_label = ttk.Label(current_frame, text=f"Question {message.question_number}", font=("Arial", 14, "bold"))
    question_label.pack(pady=10)
    
    question_text = ttk.Label(current_frame, text=message.question, font=("Arial", 12), wraplength=500, justify=tk.LEFT)
    question_text.pack(pady=15, padx=20)
    
    hint_frame = ttk.LabelFrame(current_frame, text="Hint", padding=10)
    if message.hint:
        hint_label = ttk.Label(hint_frame, text=message.hint, font=("Arial", 10), wraplength=480, justify=tk.LEFT, foreground="green")
        hint_label.pack()
        hint_frame.pack(fill=tk.X, padx=10, pady=10)
    
    answer_frame = ttk.LabelFrame(current_frame, text="Your Answer", padding=10)
    answer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    answer_var = tk.StringVar()
    answer_entry = ttk.Entry(answer_frame, textvariable=answer_var, width=60)
    answer_entry.pack(pady=5)
    answer_entry.focus()
    
    button_frame = ttk.Frame(current_frame)
    button_frame.pack(pady=10)
    
    def submit_answer():
        answer = answer_var.get().strip()
        if not answer:
            messagebox.showwarning("Input Required", "Please enter an answer.")
            return
        response_queue.put(answer)
        answer_entry.delete(0, tk.END)
    
    def request_hint():
        response_queue.put("hint")
    
    submit_button = ttk.Button(button_frame, text="Submit Answer", command=submit_answer)
    submit_button.pack(side=tk.LEFT, padx=5)
    
    if not message.hint:
        hint_button = ttk.Button(button_frame, text="Get Hint", command=request_hint)
        hint_button.pack(side=tk.LEFT, padx=5)
    
    answer_entry.bind("<Return>", lambda e: submit_answer())


def show_response(message):
    clear_frame()
    
    is_correct = message.is_correct
    result_text = "✓ Correct!" if is_correct else "✗ Incorrect"
    result_color = "green" if is_correct else "red"
    
    result_label = ttk.Label(current_frame, text=result_text, font=("Arial", 20, "bold"), foreground=result_color)
    result_label.pack(pady=20)
    
    question_label = ttk.Label(current_frame, text="Question:", font=("Arial", 12, "bold"))
    question_label.pack(pady=(10, 5))
    
    question_text = ttk.Label(current_frame, text=message.question, font=("Arial", 11), wraplength=500, justify=tk.LEFT)
    question_text.pack(padx=20, pady=5)
    
    points_label = ttk.Label(current_frame, text=f"Points for this question: {message.points_for_correct_answer}", font=("Arial", 12), foreground="blue")
    points_label.pack(pady=20)
    
    def continue_game():
        response_queue.put(None)
    
    continue_button = ttk.Button(current_frame, text="Continue", command=continue_game)
    continue_button.pack(pady=10)


def show_final_score(message):
    clear_frame()
    
    title_label = ttk.Label(current_frame, text="Game Finished!", font=("Arial", 20, "bold"))
    title_label.pack(pady=30)
    
    score_label = ttk.Label(current_frame, text=f"Your Final Score: {message.score}", font=("Arial", 28, "bold"), foreground="green")
    score_label.pack(pady=20)
    
    def exit_game():
        response_queue.put(None)
        root.quit()
    
    exit_button = ttk.Button(current_frame, text="Exit Game", command=exit_game)
    exit_button.pack(pady=20)


def show_error(message):
    error_text = message.error
    
    if hasattr(message, 'user_name') and message.user_name:
        error_text = f"Username '{message.user_name}' is already taken. Please try another."
    
    messagebox.showerror("Error", error_text)
    show_username_input()


def handle_user_name_input():
    request_queue.put(("show_username_input", None))
    return response_queue.get()


def handle_ctf_choice(message):
    request_queue.put(("show_ctf_choice", message))
    return response_queue.get()


def get_answer(message):
    request_queue.put(("show_question", message))
    return response_queue.get()


def handle_show_result(message):
    request_queue.put(("show_response", message))
    response_queue.get()


def handle_show_final_score(message):
    request_queue.put(("show_final_score", message))
    response_queue.get()


def handle_show_error(message):
    request_queue.put(("show_error", message))

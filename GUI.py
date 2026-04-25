import tkinter as tk
from tkinter import ttk, messagebox
import logic  # Ensure logic.py is in the same folder

class CPUSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CPU Scheduler Live Simulator - Group 6")
        self.root.geometry("1000x750")
        
        self.scheduler = None
        self.is_running = False
        self.initial_processes = []
        self.colors = ["#3498db", "#e74c3c", "#2ecc71", "#f1c40f", "#9b59b6", "#1abc9c", "#e67e22"]
        self.color_map = {}

        self.setup_ui()

    def setup_ui(self):
        # --- Section 1: Configuration ---
        settings_frame = ttk.LabelFrame(self.root, text=" 1. Configuration ")
        settings_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(settings_frame, text="Algorithm:").grid(row=0, column=0, padx=5, pady=5)
        self.algo_var = tk.StringVar(value="FCFS")
        self.algo_menu = ttk.Combobox(settings_frame, textvariable=self.algo_var, state="readonly",
                                      values=["FCFS", "SJF_NP", "SJF_P", "PRIO_NP", "PRIO_P", "RR"])
        self.algo_menu.grid(row=0, column=1, padx=5)
        self.algo_menu.bind("<<ComboboxSelected>>", self.toggle_inputs)

        self.lbl_quantum = ttk.Label(settings_frame, text="Quantum:")
        self.ent_quantum = ttk.Entry(settings_frame, width=8)
        
        # Fast Mode Option (To satisfy PDF requirement)
        self.fast_mode_var = tk.BooleanVar(value=False)
        self.chk_fast = ttk.Checkbutton(settings_frame, text="Fast Mode (Instant Run)", variable=self.fast_mode_var)
        self.chk_fast.grid(row=0, column=4, padx=10)

        self.start_btn = ttk.Button(settings_frame, text="START", command=self.start_simulation)
        self.start_btn.grid(row=0, column=5, padx=5)

        self.reset_btn = ttk.Button(settings_frame, text="RESET", command=self.reset_simulator)
        self.reset_btn.grid(row=0, column=6, padx=5)

        # --- Section 2: Process Details ---
        self.add_frame = ttk.LabelFrame(self.root, text=" 2. Add Process ")
        self.add_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(self.add_frame, text="PID:").grid(row=0, column=0, padx=2)
        self.ent_pid = ttk.Entry(self.add_frame, width=7)
        self.ent_pid.grid(row=0, column=1, padx=5)

        ttk.Label(self.add_frame, text="Arrival:").grid(row=0, column=2, padx=2)
        self.ent_arrival = ttk.Entry(self.add_frame, width=7)
        self.ent_arrival.insert(0, "0")
        self.ent_arrival.grid(row=0, column=3, padx=5)

        ttk.Label(self.add_frame, text="Burst:").grid(row=0, column=4, padx=2)
        self.ent_burst = ttk.Entry(self.add_frame, width=7)
        self.ent_burst.grid(row=0, column=5, padx=5)

        self.lbl_prio = ttk.Label(self.add_frame, text="Priority:")
        self.ent_prio = ttk.Entry(self.add_frame, width=7)

        self.btn_add = ttk.Button(self.add_frame, text="Add Process", command=self.handle_add_process)
        self.btn_add.grid(row=0, column=8, padx=10, pady=10)

        # --- Section 3: Live Table ---
        table_frame = ttk.LabelFrame(self.root, text=" 3. Process Table ")
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("PID", "Arrival", "Burst", "Remaining", "Priority")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=100)

        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

        # --- Section 4: Gantt Chart ---
        gantt_frame = ttk.LabelFrame(self.root, text=" Live Gantt Chart (1 unit = 1 sec) ")
        gantt_frame.pack(fill="x", padx=10, pady=10)

        canvas_wrapper = ttk.Frame(gantt_frame)
        canvas_wrapper.pack(fill="x", padx=5, pady=5)
        canvas_wrapper.grid_rowconfigure(0, weight=1)
        canvas_wrapper.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_wrapper, bg="white", height=120)
        self.canvas.grid(row=0, column=0, sticky="ew")

        h_scroll = ttk.Scrollbar(canvas_wrapper, orient="horizontal", command=self.canvas.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.canvas.config(xscrollcommand=h_scroll.set)
        
        self.stats_label = ttk.Label(self.root, text="Ready to Start", font=("Arial", 11, "bold"))
        self.stats_label.pack(pady=10)

        self.toggle_inputs()

    def toggle_inputs(self, event=None):
        algo = self.algo_var.get()
        if algo == "RR":
            self.lbl_quantum.grid(row=0, column=2, padx=5)
            self.ent_quantum.grid(row=0, column=3, padx=5)
        else:
            self.lbl_quantum.grid_forget()
            self.ent_quantum.grid_forget()

        if "PRIO" in algo:
            self.lbl_prio.grid(row=0, column=6, padx=5)
            self.ent_prio.grid(row=0, column=7, padx=5)
        else:
            self.lbl_prio.grid_forget()
            self.ent_prio.grid_forget()

    def handle_add_process(self):
            try:
                pid = self.ent_pid.get().strip()
                if not pid:
                    messagebox.showwarning("Input Error", "PID cannot be empty!")
                    return

                # Check if PID already exists (Works for both Static and Dynamic)
                current_list = self.scheduler.processes if self.scheduler else self.initial_processes
                if any(p.pid == pid for p in current_list):
                    messagebox.showerror("Error", f"Process ID '{pid}' already exists!")
                    return

                arrival = int(self.ent_arrival.get())
                burst = int(self.ent_burst.get())
                prio = int(self.ent_prio.get()) if "PRIO" in self.algo_var.get() else 0
                
                new_p = logic.Process(pid, arrival=arrival, burst=burst, priority=prio)
                
                if self.is_running:
                    self.scheduler.add_process(new_p)
                else:
                    self.initial_processes.append(new_p)
                
                self.refresh_table()
                self.ent_pid.delete(0, tk.END)
                self.ent_burst.delete(0, tk.END)

            except ValueError:
                messagebox.showerror("Error", "Arrival, Burst, and Priority must be integers.")

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        source = self.scheduler.processes if self.scheduler else self.initial_processes
        for p in source:
            prio_val = p.priority if "PRIO" in self.algo_var.get() else "N/A"
            self.tree.insert("", "end", values=(p.pid, p.arrival, p.burst, p.remaining, prio_val))

    def start_simulation(self):
        if not self.initial_processes:
            messagebox.showwarning("No Processes", "Please add at least one process before starting.")
            return
        algo, q = self.algo_var.get(), (int(self.ent_quantum.get()) if self.algo_var.get()=="RR" else 2)
        self.scheduler = logic.LiveScheduler(algorithm=algo, quantum=q)
        for p in self.initial_processes: self.scheduler.add_process(p)
        self.is_running = True
        self.start_btn.config(state="disabled")
        self.algo_menu.config(state="disabled")
        self.run_tick()

    def run_tick(self):
        if not self.is_running: return
        state = self.scheduler.tick()
        self.refresh_table()
        self.draw_gantt(state)
        
        # Update Arrival entry for dynamic adding convenience
        self.ent_arrival.delete(0, tk.END)
        self.ent_arrival.insert(0, str(state["current_time"]))

        if state["is_finished"]:
            w, t = self.scheduler.get_final_stats()
            self.stats_label.config(text=f"FINISHED | Avg Wait: {w}s | Avg Turnaround: {t}s")
            self.is_running = False
        else:
            # Fast Mode logic: 10ms for instant, 1000ms for live
            delay = 10 if self.fast_mode_var.get() else 1000
            self.root.after(delay, self.run_tick)

    def draw_gantt(self, state):
        self.canvas.delete("all")
        sec_w, h, y = 25, 50, 30
        
        # Calculate the required width for the chart
        if state["gantt_chart"]:
            max_time = max([block["end"] if block["end"] is not None else state["current_time"] + 1 for block in state["gantt_chart"]])
        else:
            max_time = state["current_time"] + 5  # Show at least 5 seconds on timeline
        
        required_width = max_time * sec_w + 50
        
        # Update scroll region so the scrollbar reflects full chart width
        self.canvas.config(scrollregion=(0, 0, max(required_width, 500), 120))
        
        # Auto-scroll to show the latest activity
        self.canvas.xview_moveto(1.0)
        
        # Draw time axis labels and grid
        for i in range(0, max_time + 1):
            x = i * sec_w
            self.canvas.create_line(x, y - 10, x, y + h + 20, fill="lightgray", width=1)
            if i % 2 == 0:
                self.canvas.create_text(x, y + h + 35, text=str(i), font=("Arial", 7), fill="gray")
        
        # Draw process blocks
        for block in state["gantt_chart"]:
            start, end = block["start"], (block["end"] if block["end"] is not None else state["current_time"] + 1)
            pid = block["pid"]
            if pid not in self.color_map: self.color_map[pid] = self.colors[len(self.color_map)%len(self.colors)]
            x0, x1 = start * sec_w, end * sec_w
            self.canvas.create_rectangle(x0, y, x1, y+h, fill=self.color_map[pid])
            self.canvas.create_text((x0+x1)/2, y+h/2, text=pid, fill="white", font=("Arial", 9, "bold"))
            self.canvas.create_text(x0, y+h+15, text=str(start), font=("Arial", 7))
            if block["end"] is not None: self.canvas.create_text(x1, y+h+15, text=str(end), font=("Arial", 7))

    def reset_simulator(self):
        self.is_running = False
        self.scheduler, self.initial_processes, self.color_map = None, [], {}
        self.tree.delete(*self.tree.get_children())
        self.canvas.delete("all")
        self.start_btn.config(state="normal")
        self.algo_menu.config(state="readonly")
        self.ent_arrival.delete(0, tk.END)
        self.ent_arrival.insert(0, "0")
        self.stats_label.config(text="Ready to Start")

if __name__ == "__main__":
    root = tk.Tk()
    app = CPUSchedulerApp(root)
    root.mainloop()
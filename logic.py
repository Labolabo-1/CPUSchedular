class Process:
    def __init__(self, pid, arrival, burst, priority=0):
        self.pid = pid
        self.arrival = arrival
        self.burst = burst
        self.remaining = burst
        self.priority = priority
        self.waiting = 0
        self.turnaround = 0
        self.completed = False
        
        # Internal flag used strictly for Round Robin queue management
        self._added_to_rr = False 


class LiveScheduler:
    """
    GUI TEAM INSTRUCTIONS:
    1. Create an instance of this class when the user clicks 'Start'.
       Example: scheduler = LiveScheduler(algorithm="RR", quantum=2)
    2. Set up a GUI Timer (e.g., root.after(1000, your_update_function)).
    3. Inside your timer function, call state = scheduler.tick()
    4. Use the returned 'state' dictionary to update your screen!
    """

    def __init__(self, algorithm="FCFS", quantum=2):
        # Supported algorithms: "FCFS", "SJF_NP", "SJF_P", "PRIO_NP", "PRIO_P", "RR"
        self.algorithm = algorithm
        self.quantum = quantum
        
        self.processes = []
        self.time_now = 0
        
        self.current_running = None
        self.gantt = []  # Format: [{"pid": "P1", "start": 0, "end": None}]
        
        # Round Robin specific trackers
        self.rr_queue = []
        self.rr_time_slice = 0

    def add_process(self, process):
        """
        GUI TEAM: Call this function the exact moment the user clicks the 
        'Add Process' button on the interface. It will automatically be 
        injected into the live scheduling on the next tick().
        """
        self.processes.append(process)

    def _get_ready_processes(self):
        """Returns processes that have arrived and are not finished."""
        return [p for p in self.processes if p.arrival <= self.time_now and p.remaining > 0]

    def _is_preemptive(self):
        return self.algorithm in ["SJF_P", "PRIO_P"]

    def tick(self):
        """
        GUI TEAM: This is the engine. Call this exactly once per second.
        It advances the math by 1 second and returns the exact data you 
        need to draw the screen.
        """
        
        # 1. ROUND ROBIN: Add newly arrived processes to the queue FIRST
        if self.algorithm == "RR":
            for p in sorted(self.processes, key=lambda x: x.arrival):
                if p.arrival <= self.time_now and p.remaining > 0 and not p._added_to_rr and p != self.current_running:
                    self.rr_queue.append(p)
                    p._added_to_rr = True

        # 2. Check if the currently running process just finished
        if self.current_running and self.current_running.remaining == 0:
            self.current_running.completed = True
            self.current_running.turnaround = self.time_now - self.current_running.arrival
            self.current_running.waiting = self.current_running.turnaround - self.current_running.burst
            
            # Close its block on the Gantt chart
            if self.gantt and self.gantt[-1]["pid"] == self.current_running.pid:
                self.gantt[-1]["end"] = self.time_now
                
            self.current_running = None
            self.rr_time_slice = 0

        # 3. ROUND ROBIN: Check if Time Quantum expired (Preemption)
        if self.algorithm == "RR" and self.current_running and self.rr_time_slice == self.quantum:
            self.rr_queue.append(self.current_running) # Put back in line
            
            # Close its block on the Gantt chart
            if self.gantt and self.gantt[-1]["pid"] == self.current_running.pid:
                self.gantt[-1]["end"] = self.time_now
                
            self.current_running = None
            self.rr_time_slice = 0

        # 4. SELECT THE NEXT PROCESS TO RUN
        ready = self._get_ready_processes()
        best = None

        if not ready and not self.current_running:
            # Nothing to do, advance time and return Idle
            state_package = self._build_state_package("Idle")
            self.time_now += 1
            return state_package

        # Apply Algorithm Rules if we don't have a process, or if algorithm is preemptive
        if not self.current_running or self._is_preemptive():
            
            if self.algorithm == "FCFS":
                best = min(ready, key=lambda x: x.arrival) if not self.current_running else self.current_running
                
            elif self.algorithm == "SJF_NP":
                best = min(ready, key=lambda x: x.burst) if not self.current_running else self.current_running
                
            elif self.algorithm == "SJF_P":
                best = min(ready, key=lambda x: x.remaining)
                
            elif self.algorithm == "PRIO_NP":
                best = min(ready, key=lambda x: (x.priority, x.arrival, x.burst)) if not self.current_running else self.current_running
                
            elif self.algorithm == "PRIO_P":
                best = min(ready, key=lambda x: (x.priority,x.arrival, x.remaining))
                
            elif self.algorithm == "RR":
                if not self.current_running and self.rr_queue:
                    best = self.rr_queue.pop(0)
                else:
                    best = self.current_running

            # If a Context Switch happened, update the Gantt Chart tracking
            if self.current_running and best and self.current_running.pid != best.pid:
                if self.gantt and self.gantt[-1]["pid"] == self.current_running.pid:
                    self.gantt[-1]["end"] = self.time_now
                self.gantt.append({"pid": best.pid, "start": self.time_now, "end": None})
                
            elif not self.current_running and best:
                self.gantt.append({"pid": best.pid, "start": self.time_now, "end": None})

            self.current_running = best

        # 5. EXECUTE 1 SECOND OF WORK
        if self.current_running:
            self.current_running.remaining -= 1
            if self.algorithm == "RR":
                self.rr_time_slice += 1

        # Package the state BEFORE we advance time so the GUI sees the current second accurately
        state_package = self._build_state_package(self.current_running.pid if self.current_running else "Idle")

        # 6. Advance the clock for the next tick
        self.time_now += 1
        return state_package

    def _build_state_package(self, running_pid):
        """Packages all necessary data for the GUI to draw the screen."""
        is_finished = len(self.processes) > 0 and all(p.completed for p in self.processes)
        
        return {
            "current_time": self.time_now,
            "running_pid": running_pid,
            "gantt_chart": self.gantt, # Draw rectangles based on this list
            "remaining_bursts": {p.pid: p.remaining for p in self.processes}, # Update your data table
            "is_finished": is_finished
        }

    def get_final_stats(self):
        """GUI TEAM: Call this once 'is_finished' is True to show final averages."""
        if not self.processes:
            return 0, 0
        avg_wait = sum(p.waiting for p in self.processes) / len(self.processes)
        avg_turn = sum(p.turnaround for p in self.processes) / len(self.processes)
        return round(avg_wait, 2), round(avg_turn, 2)


# ==============================================================================
# HOW TO TEST IT WITHOUT A GUI (Example Usage)
# ==============================================================================
if __name__ == "__main__":
    # 1. Initialize the Scheduler
    scheduler = LiveScheduler(algorithm="SJF_P", quantum=2)

    # 2. Add starting processes
    scheduler.add_process(Process("P1", arrival=0, burst=5))
    
    print("--- Starting Simulation ---")
    
    # 3. Simulate the GUI Timer Loop
    while True:
        # Simulate user dynamically clicking "Add Process" at time = 3
        if scheduler.time_now == 3:
            print("\n* USER CLICKED ADD PROCESS *")
            scheduler.add_process(Process("P2", arrival=3, burst=1))

        # Call tick() once per loop (this represents 1 second)
        state = scheduler.tick()

        # Print the data the GUI would use to draw the screen
        print(f"Time: {state['current_time']} | Running: {state['running_pid']} | Bursts: {state['remaining_bursts']}")

        if state["is_finished"]:
            print("\n--- Simulation Complete ---")
            break

    # Print Final Gantt and Stats
    print("\nFinal Gantt Chart Data for UI Drawing:")
    for block in state["gantt_chart"]:
        print(f"[{block['start']} - {block['end']}] : {block['pid']}")

    avg_w, avg_t = scheduler.get_final_stats()
    print(f"\nAverage Wait: {avg_w} | Average Turnaround: {avg_t}")
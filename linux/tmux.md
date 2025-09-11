# TMUX Cheat Sheet

`tmux` is a terminal multiplexer that allows to manage multiple terminal windows and panes from a single terminal session. It is especially useful for running multiple tasks simultaneously or keeping long-running processes active.

---

### Session Management
  Sessions are independent tmux environments. You can have multiple sessions running.
- ```$ tmux new-session -s session_name```  // Create a new session
- ```$ tmux rename-session -t old_name new_name```  // Rename
- ```$ tmux ls```  // List all sessions
- ```$ tmux attach -t session_name```  // Attach to an existing session
- ```$ Ctrl-b d``` Detach from a session
- ```$ tmux kill-session -t session_name``` // Kill session


## 🔹 Pane Management

Panes are sub-divisions of a tmux window. You can split a window into multiple panes.

- **Create a vertical (left/right) split:** Ctrl-b %
- **Create a horizontal (top/bottom) split:** Ctrl-b "
- Navigate between panes:
  ```
    Ctrl-b ←  # Move to the left pane
    Ctrl-b →  # Move to the right pane
    Ctrl-b ↑  # Move to the upper pane
    Ctrl-b ↓  # Move to the lower pane
  ```
- Resize panes: Hold Ctrl-b and then press Ctrl + arrow keys to resize panes (depends on tmux version).

### copy mode
 Copy mode allows scrolling through output or copying text inside tmux. 
- Enter copy mode: ctrl-b [
- Move cursor: Up/Down arrows, PageUp/PageDown(Scroll faster)
- Exit copy mode: q
- Paste copied text: Ctrl-b ]

### Window Management
 Windows are like tabs in your tmux session. Each window can have multiple panes.
- Create a new window: Ctrl-b c
- Switch between windows: Ctrl-b 0, Ctrl-b 1
- close a window: exit

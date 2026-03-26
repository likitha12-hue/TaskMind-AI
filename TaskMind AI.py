import requests
import json
from datetime import datetime, date

# ╔══════════════════════════════════════════════════════╗
#   STUDYDESK — Python Terminal Version
#   Backend  : Airtable
#   AI       : Claude (Anthropic)
#   Author   : Built for Likitha
# ╚══════════════════════════════════════════════════════╝

# ── Keys (already configured) ────────────────────────
AIRTABLE_TOKEN = "**********************************"
AIRTABLE_BASE  = "*************************************"
AIRTABLE_TABLE = "*************************************"
CLAUDE_KEY     = "*************************************************"

# ── URLs ──────────────────────────────────────────────
AT_URL     = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{requests.utils.quote(AIRTABLE_TABLE)}"
CLAUDE_URL = "https://api.anthropic.com/v1/messages"

AT_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type":  "application/json"
}
CLAUDE_HEADERS = {
    "x-api-key":          CLAUDE_KEY,
    "anthropic-version":  "2023-06-01",
    "Content-Type":       "application/json"
}

# ─────────────────────────────────────────────────────
#  AIRTABLE FUNCTIONS
# ─────────────────────────────────────────────────────

def fetch_all():
    """Load all homework records from Airtable."""
    try:
        res = requests.get(AT_URL, headers=AT_HEADERS, timeout=10)

        # Check raw response first
        if res.status_code != 200:
            print(f"  ⚠️ Airtable HTTP Error: {res.status_code}")
            print(f"  Response: {res.text}")
            return []

        data = res.json()

        # Ensure it's a dictionary
        if not isinstance(data, dict):
            print(f"  ⚠️ Unexpected response format: {data}")
            return []

        if "error" in data:
            print(f"  ⚠️ Airtable error: {data['error']['message']}")
            return []

        return data.get("records", [])

    except Exception as e:
        print(f"  ⚠️ Could not connect to Airtable: {e}")
        return []

def add_task(subject, task, due_date, priority):
    """Add a new homework task to Airtable."""
    fields = {
        "Subject":       subject,
        "Homework Task": task,
        "Priority":      priority,
        "Status":        "Not Started"
    }
    if due_date:
        fields["Due Date"] = due_date  # format: YYYY-MM-DD

    try:
        res  = requests.post(AT_URL, headers=AT_HEADERS, json={"fields": fields}, timeout=10)
        data = res.json()
        if "error" in data:
            print(f"  ⚠️  Could not add task: {data['error']['message']}")
            return None
        return data
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return None


def update_task(record_id, fields):
    """Update a task's fields in Airtable."""
    try:
        res  = requests.patch(f"{AT_URL}/{record_id}", headers=AT_HEADERS, json={"fields": fields}, timeout=10)
        data = res.json()
        if "error" in data:
            return False
        return True
    except Exception as e:
        print(f"  ⚠️  Update error: {e}")
        return False


def delete_task(record_id):
    """Delete a task from Airtable."""
    try:
        res = requests.delete(f"{AT_URL}/{record_id}", headers=AT_HEADERS, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"  ⚠️  Delete error: {e}")
        return False


# ─────────────────────────────────────────────────────
#  DISPLAY FUNCTIONS
# ─────────────────────────────────────────────────────

def fmt_date(d):
    """Format YYYY-MM-DD to readable date."""
    if not d:
        return "No date"
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %Y")
    except:
        return d


def is_urgent(due_date):
    """Check if task is due today or overdue."""
    if not due_date:
        return False
    try:
        due = datetime.strptime(due_date, "%Y-%m-%d").date()
        return due <= date.today()
    except:
        return False


def priority_icon(p):
    if p == "High":   return "🔴"
    if p == "Medium": return "🟡"
    if p == "Low":    return "🟢"
    return "⚪"


def status_icon(s):
    if s == "Done":        return "✅"
    if s == "In Progress": return "🔄"
    return "📌"


def print_tasks(records, title="📚 Your Homework Tasks"):
    """Pretty print all tasks in terminal."""
    if not records:
        print("\n  📭 No tasks found.\n")
        return

    today    = date.today().isoformat()
    tomorrow = date.fromordinal(date.today().toordinal() + 1).isoformat()

    print(f"\n  {'─'*55}")
    print(f"  {title}")
    print(f"  {'─'*55}")

    for i, r in enumerate(records, 1):
        f       = r["fields"]
        subject = f.get("Subject", "?")
        task    = f.get("Homework Task", "?")
        due     = f.get("Due Date", "")
        status  = f.get("Status", "Not Started")
        priority= f.get("Priority", "")

        urgent_flag = ""
        if due == today:    urgent_flag = " ⚠️  DUE TODAY!"
        elif due < today and due:   urgent_flag = " 🚨 OVERDUE!"
        elif due == tomorrow: urgent_flag = " ⏰ Due tomorrow"

        print(f"\n  [{i}] {status_icon(status)} {subject} — {task}")
        print(f"       📅 {fmt_date(due)}{urgent_flag}")
        print(f"       {priority_icon(priority)} {priority or 'No priority'} | {status}")

    print(f"\n  {'─'*55}\n")


def print_stats(records):
    """Show a quick stats summary."""
    total   = len(records)
    done    = sum(1 for r in records if r["fields"].get("Status") == "Done")
    pending = total - done
    today   = date.today().isoformat()
    urgent  = sum(1 for r in records if r["fields"].get("Due Date","") <= today and r["fields"].get("Status") != "Done" and r["fields"].get("Due Date"))

    print(f"\n  📊 Stats → Total: {total} | Pending: {pending} | Done: {done} | Urgent: {urgent}")


def print_reminders(records):
    """Show due soon reminders."""
    today    = date.today().isoformat()
    tomorrow = date.fromordinal(date.today().toordinal() + 1).isoformat()
    urgent   = [r for r in records if r["fields"].get("Status") != "Done" and r["fields"].get("Due Date","") in [today, tomorrow]]

    if urgent:
        print("\n  ⚠️  REMINDERS:")
        for r in urgent:
            f   = r["fields"]
            tag = "TODAY" if f.get("Due Date") == today else "Tomorrow"
            print(f"     → {f.get('Subject')} — {f.get('Homework Task')} ({tag})")
        print()


# ─────────────────────────────────────────────────────
#  MANUAL COMMANDS (without AI)
# ─────────────────────────────────────────────────────

def manual_add(records):
    """Manually add a task with prompts."""
    print("\n  ── Add New Task ──────────────────")
    subject  = input("  Subject  : ").strip()
    task     = input("  Task     : ").strip()
    due      = input("  Due Date (YYYY-MM-DD, press Enter to skip): ").strip()
    print("  Priority : 1=High  2=Medium  3=Low")
    p_choice = input("  Choose   : ").strip()
    priority = {"1":"High","2":"Medium","3":"Low"}.get(p_choice, "Medium")

    if not subject or not task:
        print("  ⚠️  Subject and task are required!")
        return records

    print("  ⏳ Saving to Airtable...")
    result = add_task(subject, task, due or None, priority)
    if result:
        records.insert(0, result)
        print(f"  ✅ '{subject} — {task}' added to Airtable!")
    return records


def manual_done(records):
    """Manually mark a task as done."""
    print_tasks(records, "Mark Task as Done")
    choice = input("  Enter task number: ").strip()
    try:
        idx  = int(choice) - 1
        r    = records[idx]
        ok   = update_task(r["id"], {"Status": "Done"})
        if ok:
            records[idx]["fields"]["Status"] = "Done"
            print(f"  ✅ Marked '{r['fields'].get('Subject')}' as Done!")
        else:
            print("  ⚠️  Could not update.")
    except (ValueError, IndexError):
        print("  ⚠️  Invalid number.")
    return records


def manual_delete(records):
    """Manually delete a task."""
    print_tasks(records, "Delete a Task")
    choice = input("  Enter task number to delete: ").strip()
    try:
        idx  = int(choice) - 1
        r    = records[idx]
        conf = input(f"  Delete '{r['fields'].get('Subject')}'? (y/n): ").strip().lower()
        if conf == 'y':
            ok = delete_task(r["id"])
            if ok:
                records.pop(idx)
                print("  🗑️  Deleted from Airtable!")
            else:
                print("  ⚠️  Could not delete.")
    except (ValueError, IndexError):
        print("  ⚠️  Invalid number.")
    return records


# ─────────────────────────────────────────────────────
#  AI CHAT
# ─────────────────────────────────────────────────────

def build_task_context(records):
    """Format tasks for Claude context."""
    if not records:
        return "No homework tasks yet."
    lines = []
    for r in records:
        f = r["fields"]
        lines.append(
            f"RecordID:{r['id']} | Subject:{f.get('Subject','?')} | "
            f"Task:{f.get('Homework Task','?')} | Due:{f.get('Due Date','none')} | "
            f"Status:{f.get('Status','Not Started')} | Priority:{f.get('Priority','none')}"
        )
    return "\n".join(lines)


def ask_ai(user_msg, records, history):
    """Send message to Claude with homework context."""
    if CLAUDE_KEY == "YOUR_CLAUDE_API_KEY_HERE":
        print("\n  ⚠️  Claude API key not set!")
        print("  → Get a free key at: console.anthropic.com")
        print("  → Open this file in PyCharm and replace YOUR_CLAUDE_API_KEY_HERE\n")
        return None, history

    system = f"""You are a homework assistant for Likitha, an engineering student in India.
Today is {date.today().strftime('%d %B %Y')}.

Her tasks:
{build_task_context(records)}

Rules:
- Be short, warm, helpful. Use emojis occasionally.
- If she wants to update status or priority, end your reply with EXACTLY:
  ACTION:{{"record_id":"recXXXXXX","fields":{{"Status":"Done"}}}}
- Match subject by name (case-insensitive partial match).
- Status values: Not Started, In Progress, Done
- Priority values: High, Medium, Low
- Keep replies under 5 lines. Plain text, no markdown.
- If no tasks exist, tell her to use 'add' command."""

    history.append({"role": "user", "content": user_msg})

    try:
        res  = requests.post(CLAUDE_URL, headers=CLAUDE_HEADERS,
                             json={"model":"claude-sonnet-4-20250514","max_tokens":600,"system":system,"messages":history},
                             timeout=15)
        data = res.json()
        if "error" in data:
            print(f"  ⚠️  Claude error: {data['error']['message']}")
            history.pop()
            return None, history

        reply = data["content"][0]["text"]
        history.append({"role": "assistant", "content": reply})
        if len(history) > 12:
            history = history[-12:]
        return reply, history

    except Exception as e:
        print(f"  ⚠️  AI connection error: {e}")
        history.pop()
        return None, history


def handle_ai_action(reply, records):
    """Check if Claude wants to update Airtable and do it."""
    if "ACTION:" not in reply:
        return reply, records, False

    try:
        action_str = reply.split("ACTION:")[1].strip().split("\n")[0]
        action     = json.loads(action_str)
        record_id  = action.get("record_id")
        fields     = action.get("fields")

        if record_id and fields:
            ok = update_task(record_id, fields)
            if ok:
                # Update local cache
                for r in records:
                    if r["id"] == record_id:
                        r["fields"].update(fields)
                        break
                clean = reply.split("ACTION:")[0].strip()
                return clean, records, True

    except Exception:
        pass

    clean = reply.split("ACTION:")[0].strip()
    return clean, records, False


# ─────────────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────────────

def print_help():
    print("""
  ╔══════════════════════════════════════╗
  ║         AVAILABLE COMMANDS           ║
  ╠══════════════════════════════════════╣
  ║  list      → Show all tasks          ║
  ║  pending   → Show pending tasks      ║
  ║  done      → Show completed tasks    ║
  ║  add       → Add a new task          ║
  ║  mark      → Mark a task as done     ║
  ║  delete    → Delete a task           ║
  ║  stats     → Show task statistics    ║
  ║  remind    → Check due reminders     ║
  ║  refresh   → Reload from Airtable    ║
  ║  help      → Show this menu          ║
  ║  exit      → Quit the app            ║
  ╠══════════════════════════════════════╣
  ║  OR just type naturally to chat!     ║
  ║  e.g: "when is maths due?"           ║
  ║       "mark OS as done"              ║
  ║       "show high priority tasks"     ║
  ╚══════════════════════════════════════╝
""")


def main():
    print("""
  ╔═══════════════════════════════════════════╗
  ║   🎓  STUDYDESK  —  Likitha's Tracker     ║
  ║       Backend: Airtable | AI: Claude       ║
  ╚═══════════════════════════════════════════╝
""")

    # Load data
    print("  ⏳ Connecting to Airtable...")
    records = fetch_all()
    if records:
        print(f"  ✅ Connected! Loaded {len(records)} task(s).")
    else:
        print("  ⚠️  No tasks found or connection failed.")

    # Show reminders on startup
    print_reminders(records)
    print_stats(records)
    print("\n  Type 'help' to see all commands or just chat naturally!")
    print("  Type 'exit' to quit.\n")

    history = []

    while True:
        try:
            user_input = input("  You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  👋 Goodbye Likitha! Good luck with your homework! 🎓\n")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        # ── Built-in commands ──────────────────────
        if cmd in ["exit", "quit", "bye"]:
            print("\n  👋 Goodbye Likitha! Good luck with your homework! 🎓\n")
            break

        elif cmd == "help":
            print_help()

        elif cmd == "list":
            print_tasks(records)

        elif cmd == "pending":
            pending = [r for r in records if r["fields"].get("Status") != "Done"]
            print_tasks(pending, "📌 Pending Tasks")

        elif cmd == "done":
            done = [r for r in records if r["fields"].get("Status") == "Done"]
            print_tasks(done, "✅ Completed Tasks")

        elif cmd == "stats":
            print_stats(records)

        elif cmd == "remind":
            print_reminders(records)
            if not any(r["fields"].get("Due Date","") <= date.today().isoformat() and r["fields"].get("Status") != "Done" for r in records if r["fields"].get("Due Date")):
                print("  ✅ No urgent tasks! You're all caught up.\n")

        elif cmd == "add":
            records = manual_add(records)

        elif cmd == "mark":
            records = manual_done(records)

        elif cmd == "delete":
            records = manual_delete(records)

        elif cmd == "refresh":
            print("  ⏳ Refreshing from Airtable...")
            records = fetch_all()
            print(f"  ✅ Refreshed! {len(records)} task(s) loaded.\n")

        # ── AI Chat ────────────────────────────────
        else:
            print("  🤔 Thinking...\n")
            reply, history = ask_ai(user_input, records, history)

            if reply:
                clean, records, updated = handle_ai_action(reply, records)
                print(f"  Bot: {clean}\n")
                if updated:
                    print("  ✅ Airtable updated automatically!\n")


if __name__ == "__main__":
    main()

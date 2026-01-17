# Quick Start: Dynamic Context Management

## What's New?

Your Interview Copilot now has **dynamic context management**! You can:

✅ Edit your profile and job context **directly in the UI**  
✅ Switch between different interview contexts **without restarting**  
✅ Your sessions are **automatically saved** and restored  
✅ Conversation history is maintained **(last 3 Q&A pairs)**  
✅ **Zero performance impact** - context is processed only once per session  

---

## How to Use

### 1️⃣ **Starting a New Session**

When you launch the app, you'll see a new **Context Panel** at the top:

```
┌──────────────────────────────────────────────────────────┐
│ ▼ Interview Context                                      │
│ ┌────────────────────────────────────────────────────┐   │
│ │ My Profile                                          │   │
│ │ [Your professional background, skills, experience] │   │
│ │                                                     │   │
│ │ Job Context                                         │   │
│ │ [Target role, company, requirements]               │   │
│ │                                                     │   │
│ │ [Start New Session]  [Load from Config]            │   │
│ └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

**Steps**:
1. Fill in **"My Profile"** with your background (e.g., "Senior Python Developer with 5 years experience...")
2. Fill in **"Job Context"** with the target role (e.g., "Applying for ML Engineer at AI Startup...")
3. Click **"Start New Session"** (green button)
4. The panel will auto-collapse and show session status

### 2️⃣ **Session Status**

After starting a session, you'll see:

```
Session: abc123 | Started: 2:30 PM | 2 Q&A
```

This tells you:
- **abc123** = Your unique session ID
- **Started: 2:30 PM** = When you created this session
- **2 Q&A** = Number of questions answered in this session

### 3️⃣ **Asking Questions**

Everything works the same as before:
1. Click **"Start Listening"** (or press `S`)
2. Speak your question
3. Click **"Process Question"** (or press `Space`/`Enter`)

**NEW**: The LLM now has access to your last 3 Q&A exchanges, so it can handle follow-up questions!

**Example**:
- Q1: "Tell me about your Python experience"
- A1: "I have 5 years of Python development..."
- Q2: "What frameworks do you use?" ← It remembers Q1!
- A2: "Based on my experience, I primarily use FastAPI and Django..."

### 4️⃣ **Switching to a New Interview**

Need to prepare for a different interview?

1. **Expand the context panel** (click the `▼` arrow)
2. **Edit** the My Profile and Job Context fields
3. Click **"Start New Session"** again

Your old session is replaced, and the new context is ready!

### 5️⃣ **Loading Config Defaults**

Don't want to type? Click **"Load from Config"** to automatically fill the fields with values from your `config.json` file. Then you can edit as needed.

---

## What If I Don't Start a Session?

If you try to process a question without an active session, you'll see a **warning**:

```
⚠️ No active session. Please start a session to begin.
```

Just expand the context panel and click "Start New Session"!

---

## Session Persistence

Your session is **automatically saved** after each question. If you close the app and reopen it:

- Your last session is **automatically restored**
- Your profile and job context are **still there**
- Your conversation history is **preserved**

No need to re-enter anything!

**Where is it saved?** `~/.interview-copilot/session.json`

---

## Tips & Tricks

### Make Your Profile Detailed

The more specific your profile, the better the answers!

**Good**:
```
Senior Python Developer with 5 years experience at TechCorp.
Built ML pipelines using FastAPI, Django, pandas, scikit-learn.
Led team of 3 developers on microservices project.
```

**Not as good**:
```
Python developer
```

### Update Job Context for Each Interview

Include:
- Role title (e.g., "Senior ML Engineer")
- Company name (e.g., "at AI Startup")
- Key requirements (e.g., "Python, ML, API design, leadership")
- Special focus (e.g., "Focus on scalable data processing")

### Use Follow-Up Questions

Since the system now remembers your last 3 exchanges, you can ask clarifying questions:

1. "Tell me about your ML projects"
2. "What was the biggest challenge in that project?" ← References previous answer!
3. "How did you solve it?"

---

## Keyboard Shortcuts

All the same as before:

- `S` - Start/Stop listening
- `Space` or `Enter` - Process question
- `Escape` - Clear transcription buffer

---

## Troubleshooting

### "The context panel isn't showing"

Make sure you're running the **latest version**. The panel appears at the top, right below the status bar.

### "I clicked Start Session but nothing happened"

Check that you've entered text in **at least one** of the fields (My Profile or Job Context). Both can't be empty.

### "My session wasn't restored after restart"

Check the logs: `tail -f interview_copilot.log`

If the session file is corrupted, delete it and start fresh:
```bash
rm ~/.interview-copilot/session.json
```

### "I want to go back to the old config-file method"

No problem! You can still edit `config.json` and click "Load from Config" to use those values. The old system still works.

---

## Performance

**Q: Will this slow down my responses?**

**A**: No! Context is processed **once when you create a session**, not on every question. Response speed is identical to before.

---

## What Changed Under the Hood?

For the technically curious:

1. **New `SessionManager`** class handles session lifecycle
2. **LLMClient** now uses pre-built prompts (no rebuilding per question)
3. **GUI** extended with context input panel and session status
4. **Session persistence** in `~/.interview-copilot/session.json`
5. **Conversation history** (last 3 Q&A) included in LLM context

See `SESSION_MANAGEMENT.md` for full technical documentation.

---

## Feedback

If you encounter any issues or have suggestions, please let me know! This is a major new feature, and your feedback helps improve it.

---

## Summary

The dynamic context management system makes Interview Copilot more flexible and user-friendly:

- ✅ No more editing config files
- ✅ No more app restarts to change context
- ✅ Automatic session persistence
- ✅ Conversation memory for follow-up questions
- ✅ Zero performance impact

**Enjoy your interviews!** 🎉

const { createElement: h, useState } = React;

const roles = [
  ["data_analyst", "Data Analyst"],
  ["data_engineer", "Data Engineer"],
  ["data_scientist", "Data Scientist"],
  ["machine_learning_engineer", "Machine Learning Engineer"],
  ["mlops", "MLOps"],
  ["ai_engineering", "AI Engineering"],
];

function InterviewApp() {
  const [focus, setFocus] = useState("");
  const [difficulty, setDifficulty] = useState("medium");
  const [role, setRole] = useState("data_scientist");
  const [prompt, setPrompt] = useState("Your next challenge will appear here.");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function generate() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("http://127.0.0.1:8000/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ focus, difficulty, role }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not generate a prompt.");
      setPrompt(data.prompt);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return h("main", { className: "page-shell" },
    h("section", { className: "hero", "aria-labelledby": "page-title" },
      h("p", { className: "eyebrow" }, "INTERVIEW PRACTICE · V0"),
      h("h1", { id: "page-title" }, "Think clearly.", h("br"), h("span", null, "Answer confidently.")),
      h("p", { className: "intro" }, "Generate one focused prompt to sharpen your reasoning across data, models, and decisions.")),
    h("section", { className: "practice-panel", "aria-label": "Generate an interview prompt" },
      h("fieldset", { className: "difficulty-fieldset" },
        h("legend", null, "Difficulty"),
        h("div", { className: "difficulty-control", role: "group", "aria-label": "Question difficulty" },
          ["easy", "medium", "hard"].map((level) =>
            h("button", {
              key: level,
              type: "button",
              className: `difficulty-button${difficulty === level ? " selected" : ""}`,
              "aria-pressed": difficulty === level,
              onClick: () => setDifficulty(level),
            }, level.charAt(0).toUpperCase() + level.slice(1))
          )
        )
      ),
      h("fieldset", { className: "role-fieldset" },
        h("legend", null, "Target role"),
        h("div", { className: "role-control", role: "group", "aria-label": "Target role" },
          roles.map(([value, label]) =>
            h("button", {
              key: value,
              type: "button",
              className: `role-button${role === value ? " selected" : ""}`,
              "aria-pressed": role === value,
              onClick: () => setRole(value),
            }, label)
          )
        )
      ),
      h("label", { htmlFor: "focus" }, "What are you working on?"),
      h("div", { className: "input-row" },
        h("input", { id: "focus", value: focus, onChange: (event) => setFocus(event.target.value), onKeyDown: (event) => event.key === "Enter" && generate(), maxLength: 200, placeholder: "e.g. Random Forest, SQL, NLP", autoComplete: "off" }),
        h("button", { type: "button", onClick: generate, disabled: loading }, h("span", null, loading ? "Thinking..." : "Generate"), h("span", { "aria-hidden": true }, "↗"))),
      h("p", { className: "hint" }, "Leave it blank for a scenario that tests your approach."),
      h("div", { className: "result", "aria-live": "polite" }, h("div", { className: "result-label" }, h("span", { className: "dot" }), "YOUR PROMPT"), h("p", null, error || prompt))),
    h("footer", null, h("span", null, "STATISTICS"), h("i"), h("span", null, "DATA SCIENCE"), h("i"), h("span", null, "ML & AI")));
}

ReactDOM.createRoot(document.getElementById("app")).render(h(InterviewApp));

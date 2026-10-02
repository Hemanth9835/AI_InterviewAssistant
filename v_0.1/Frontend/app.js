const { createElement: h, useEffect, useState } = React;

const roles = [
  ["data_analyst", "Data Analyst"],
  ["data_engineer", "Data Engineer"],
  ["data_scientist", "Data Scientist"],
  ["machine_learning_engineer", "Machine Learning Engineer"],
  ["mlops", "MLOps"],
  ["ai_engineering", "AI Engineering"],
];

const LOCAL_API_URL = "http://127.0.0.1:8000";
const CLOUD_API_URL = "https://ai-interviewassistant-z3kl.onrender.com";
const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const API_BASE_URL = isLocal ? LOCAL_API_URL : CLOUD_API_URL;
const DEFAULT_PROMPT = "Your next challenge will appear here.";

function promptStorageKey(name) {
  return `last_prompt_${encodeURIComponent(name.trim())}`;
}

function getApiError(data, fallback) {
  if (Array.isArray(data.detail)) {
    return data.detail
      .map((item) => item.msg || "Invalid input.")
      .join(" ");
  }

  if (data.detail && typeof data.detail === "object") {
    return data.detail.msg || fallback;
  }

  return data.detail || fallback;
}

function LoginPage({ onLogin, error, loading }) {
  const [registerMode, setRegisterMode] = useState(false);
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  function submit(event) {
    event.preventDefault();
    onLogin(name, password, registerMode ? confirmPassword : "", registerMode);
  }

  return h("main", { className: "login-shell" },
    h("section", { className: "login-card", "aria-labelledby": "login-title" },
      h("p", { className: "eyebrow" }, "INTERVIEW PRACTICE"),
      h("h1", { id: "login-title" }, registerMode ? "Create your account." : "Welcome back."),
      h("p", { className: "login-intro" }, registerMode ? "Create an account to start preparing." : "Sign in to continue your interview preparation."),
      h("form", { onSubmit: submit },
        h("label", { htmlFor: "login-name" }, "User name"),
        h("input", { id: "login-name", value: name, onChange: (event) => setName(event.target.value), autoComplete: "username", required: true }),
        h("label", { htmlFor: "login-password" }, "Password"),
        h("input", { id: "login-password", type: "password", value: password, onChange: (event) => setPassword(event.target.value), autoComplete: registerMode ? "new-password" : "current-password", minLength: registerMode ? 8 : undefined, required: true }),
        registerMode && h("label", { htmlFor: "confirm-password" }, "Confirm password"),
        registerMode && h("input", { id: "confirm-password", type: "password", value: confirmPassword, onChange: (event) => setConfirmPassword(event.target.value), autoComplete: "new-password", required: true }),
        error && h("p", { className: "form-error", role: "alert" }, error),
        h("button", { className: "login-button", type: "submit", disabled: loading }, loading ? (registerMode ? "Creating account..." : "Signing in...") : (registerMode ? "Create account" : "Sign in")),
        h("button", { className: "mode-button", type: "button", onClick: () => { setRegisterMode(!registerMode); setConfirmPassword(""); } }, registerMode ? "Already have an account? Sign in" : "New here? Create an account")
      )
    )
  );
}

function InterviewApp() {
  const [token, setToken] = useState(() => localStorage.getItem("access_token"));
  const [userName, setUserName] = useState(() => localStorage.getItem("user_name") || "");
  const [loginError, setLoginError] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);
  const [focus, setFocus] = useState("");
  const [difficulty, setDifficulty] = useState("medium");
  const [role, setRole] = useState("data_scientist");
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_name");
    setToken(null);
    setUserName("");
    setFocus("");
    setDifficulty("medium");
    setRole("data_scientist");
    setPrompt(DEFAULT_PROMPT);
    setError("");
    setLoginError("");
  }

  useEffect(() => {
    if (!token) return;
    const savedPrompt = userName && localStorage.getItem(promptStorageKey(userName));
    if (savedPrompt) setPrompt(savedPrompt);
    fetch(`${API_BASE_URL}/api/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then((response) => { if (!response.ok) logout(); })
      .catch(() => logout());
  }, []);

  async function login(name, password, confirmPassword, registerMode) {
    setLoginLoading(true);
    setLoginError("");
    try {
      if (registerMode && password !== confirmPassword) {
        throw new Error("Passwords do not match.");
      }
      const response = await fetch(`${API_BASE_URL}/api/auth/${registerMode ? "register" : "login"}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(getApiError(data, registerMode ? "Could not create account." : "Could not sign in."));
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_name", data.name);
      setToken(data.access_token);
      setUserName(data.name);
      setPrompt(localStorage.getItem(promptStorageKey(data.name)) || DEFAULT_PROMPT);
    } catch (requestError) {
      setLoginError(requestError.message === "Failed to fetch" ? "The login service is unavailable." : requestError.message);
    } finally {
      setLoginLoading(false);
    }
  }

  async function generate() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE_URL}/api/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ focus, difficulty, role }),
      });
      const data = await response.json();
      if (response.status === 401) {
        logout();
        throw new Error("Your session has expired. Please sign in again.");
      }
      if (!response.ok) throw new Error(getApiError(data, "Could not generate a prompt."));
      setPrompt(data.prompt);
      localStorage.setItem(promptStorageKey(userName), data.prompt);
    } catch (requestError) {
      setError(requestError.message === "Failed to fetch" ? "The interview service is unavailable." : requestError.message);
    } finally {
      setLoading(false);
    }
  }

  if (!token) return h(LoginPage, { onLogin: login, error: loginError, loading: loginLoading });

  return h("main", { className: "page-shell" },
    h("header", { className: "topbar" },
      h("span", { className: "signed-in" }, `Signed in as ${userName}`),
      h("button", { className: "logout-button", type: "button", onClick: logout }, "Sign out")
    ),
    h("section", { className: "hero", "aria-labelledby": "page-title" },
      h("p", { className: "eyebrow" }, "INTERVIEW PRACTICE · V0"),
      h("h1", { id: "page-title" }, "Think clearly.", h("br"), h("span", null, "Answer confidently.")),
      h("p", { className: "intro" }, "Generate one focused prompt to sharpen your reasoning across data, models, and decisions.")),
    h("section", { className: "practice-panel", "aria-label": "Generate an interview prompt" },
      h("fieldset", { className: "difficulty-fieldset" },
        h("legend", null, "Difficulty"),
        h("div", { className: "difficulty-control", role: "group", "aria-label": "Question difficulty" },
          ["easy", "medium", "hard"].map((level) => h("button", { key: level, type: "button", className: `difficulty-button${difficulty === level ? " selected" : ""}`, "aria-pressed": difficulty === level, onClick: () => setDifficulty(level) }, level.charAt(0).toUpperCase() + level.slice(1)))
        )
      ),
      h("fieldset", { className: "role-fieldset" },
        h("legend", null, "Target role"),
        h("div", { className: "role-control", role: "group", "aria-label": "Target role" },
          roles.map(([value, label]) => h("button", { key: value, type: "button", className: `role-button${role === value ? " selected" : ""}`, "aria-pressed": role === value, onClick: () => setRole(value) }, label))
        )
      ),
      h("label", { htmlFor: "focus" }, "What are you working on?"),
      h("div", { className: "input-row" },
        h("input", { id: "focus", value: focus, onChange: (event) => setFocus(event.target.value), onKeyDown: (event) => event.key === "Enter" && generate(), maxLength: 200, placeholder: "e.g. Random Forest, SQL, NLP", autoComplete: "off" }),
        h("button", { type: "button", onClick: generate, disabled: loading }, h("span", null, loading ? "Thinking..." : "Generate"), h("span", { "aria-hidden": true }, "↗"))),
      h("p", { className: "hint" }, "Leave it blank for a scenario that tests your approach."),
      h("div", { className: "result", "aria-live": "polite" }, h("div", { className: "result-label" }, h("span", { className: "dot" }), "YOUR PROMPT"), h("p", null, error || prompt))),
    h("footer", null, h("span", null, "STATISTICS"), h("i"), h("span", null, "DATA SCIENCE"), h("i"), h("span", null, "ML & AI"))
  );
}

ReactDOM.createRoot(document.getElementById("app")).render(h(InterviewApp));

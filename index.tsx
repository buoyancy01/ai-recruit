import React, { useState } from "react";
import ReactDOM from "react-dom/client";
import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";

const App = () => {
  const [file, setFile] = useState<File | null>(null);
  const [msg, setMsg] = useState("");

  const upload = async () => {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    const { data } = await axios.post(`${API}/upload-cv/`, form);
    setMsg(`AI saw: ${data.raw_text}`);
  };

  return (
    <>
      <h1>AI Recruiter</h1>
      <input type="file" onChange={(e) => setFile(e.target.files![0])} />
      <button onClick={upload}>Upload CV</button>
      <p>{msg}</p>
    </>
  );
};

const root = ReactDOM.createRoot(document.getElementById("root")!);
root.render(<App />);
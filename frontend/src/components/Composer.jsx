import { useState } from "react";

export default function Composer({ onSubmit, sending }) {
  const [content, setContent] = useState("");
  const [includeMarkdown, setIncludeMarkdown] = useState(false);
  const [maxSources, setMaxSources] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmed = content.trim();
    if (!trimmed || sending) {
      return;
    }

    await onSubmit({
      content: trimmed,
      include_markdown: includeMarkdown,
      max_sources: maxSources ? Number(maxSources) : null,
    });
    setContent("");
  }

  return (
    <form className="composer" onSubmit={handleSubmit}>
      <label className="composer__label" htmlFor="query-input">
        Message
      </label>
      <textarea
        id="query-input"
        name="query"
        rows="4"
        placeholder="Ask a research question..."
        required
        value={content}
        onChange={(event) => setContent(event.target.value)}
      />

      <div className="composer__controls">
        <label className="toggle">
          <input
            checked={includeMarkdown}
            type="checkbox"
            onChange={(event) => setIncludeMarkdown(event.target.checked)}
          />
          <span>Include markdown</span>
        </label>

        <label className="source-count">
          <span>Sources</span>
          <select value={maxSources} onChange={(event) => setMaxSources(event.target.value)}>
            <option value="">Default</option>
            <option value="3">3</option>
            <option value="5">5</option>
            <option value="7">7</option>
          </select>
        </label>

        <button className="primary-button" disabled={sending} type="submit">
          {sending ? "Thinking..." : "Send"}
        </button>
      </div>
    </form>
  );
}

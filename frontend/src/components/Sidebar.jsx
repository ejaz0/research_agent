export default function Sidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onCreateConversation,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <div>
          <p className="eyebrow">Research Agent</p>
          <h1>Briefing Console</h1>
        </div>
        <button className="ghost-button" type="button" onClick={onCreateConversation}>
          New Chat
        </button>
      </div>

      <p className="sidebar__copy">
        React frontend, FastAPI backend, and SQLite-backed conversation history.
      </p>

      <div className="history-list" aria-label="Conversation history">
        {conversations.length === 0 ? (
          <div className="empty-state">No conversations yet.</div>
        ) : null}

        {conversations.map((conversation) => (
          <button
            key={conversation.id}
            type="button"
            className={`history-card ${
              activeConversationId === conversation.id ? "is-active" : ""
            }`}
            onClick={() => onSelectConversation(conversation.id)}
          >
            <p className="history-card__title">{conversation.title}</p>
            <p className="history-card__meta">
              {new Date(conversation.updated_at).toLocaleString([], {
                month: "short",
                day: "numeric",
                hour: "numeric",
                minute: "2-digit",
              })}
            </p>
            {conversation.last_message_excerpt ? (
              <p className="history-card__excerpt">{conversation.last_message_excerpt}</p>
            ) : null}
          </button>
        ))}
      </div>
    </aside>
  );
}

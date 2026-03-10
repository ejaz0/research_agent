import { useEffect, useRef } from "react";

import AssistantReportCard from "./AssistantReportCard";

function MessageBubble({ message }) {
  const isAssistant = message.role === "assistant";

  return (
    <article className={`message message--${message.role}`}>
      <div className="message__meta">
        {message.role === "user"
          ? "You"
          : message.role === "assistant"
            ? "Research Agent"
            : "Error"}
      </div>

      {isAssistant ? (
        <AssistantReportCard report={message.report} content={message.content} />
      ) : (
        <div className="message__body">{message.content}</div>
      )}
    </article>
  );
}

export default function Thread({ conversation, sending }) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [conversation, sending]);

  return (
    <section className="messages" aria-live="polite">
      {!conversation?.messages?.length ? (
        <article className="message message--system">
          <div className="message__meta">System</div>
          <div className="message__body">
            Ask a research question to generate a structured brief. Conversation memory is stored on
            the server for this running app, so follow-up questions can use prior context.
          </div>
        </article>
      ) : null}

      {conversation?.messages?.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {sending ? (
        <article className="message message--assistant message--pending">
          <div className="message__meta">Research Agent</div>
          <div className="message__body">Thinking through the current conversation context...</div>
        </article>
      ) : null}

      <div ref={endRef} />
    </section>
  );
}

import { useEffect, useMemo, useState } from "react";

import { createConversation, getConversation, listConversations, sendMessage } from "./api";
import Composer from "./components/Composer";
import Sidebar from "./components/Sidebar";
import Thread from "./components/Thread";

export default function App() {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [activeConversation, setActiveConversation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [bannerError, setBannerError] = useState("");

  async function refreshConversations(nextActiveId = activeConversationId) {
    const items = await listConversations();
    setConversations(items);
    if (!items.length) {
      setActiveConversation(null);
      setActiveConversationId(null);
      return;
    }

    const targetId =
      nextActiveId && items.some((item) => item.id === nextActiveId)
        ? nextActiveId
        : items[0].id;
    setActiveConversationId(targetId);
    const conversation = await getConversation(targetId);
    setActiveConversation(conversation);
  }

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      try {
        const items = await listConversations();
        if (cancelled) {
          return;
        }

        if (!items.length) {
          const conversation = await createConversation();
          if (cancelled) {
            return;
          }
          setConversations([
            {
              id: conversation.id,
              title: conversation.title,
              updated_at: conversation.updated_at,
              last_message_excerpt: "",
            },
          ]);
          setActiveConversationId(conversation.id);
          setActiveConversation(conversation);
        } else {
          setConversations(items);
          setActiveConversationId(items[0].id);
          const conversation = await getConversation(items[0].id);
          if (!cancelled) {
            setActiveConversation(conversation);
          }
        }
      } catch (error) {
        if (!cancelled) {
          setBannerError(error instanceof Error ? error.message : "Failed to load conversations.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleCreateConversation() {
    setBannerError("");
    const conversation = await createConversation();
    setActiveConversationId(conversation.id);
    setActiveConversation(conversation);
    await refreshConversations(conversation.id);
  }

  async function handleSelectConversation(conversationId) {
    setBannerError("");
    setActiveConversationId(conversationId);
    try {
      const conversation = await getConversation(conversationId);
      setActiveConversation(conversation);
    } catch (error) {
      setBannerError(error instanceof Error ? error.message : "Failed to load conversation.");
    }
  }

  async function handleSubmitMessage(payload) {
    if (!activeConversationId) {
      return;
    }

    setSending(true);
    setBannerError("");
    try {
      const conversation = await sendMessage(activeConversationId, payload);
      setActiveConversation(conversation);
      await refreshConversations(conversation.id);
    } catch (error) {
      setBannerError(error instanceof Error ? error.message : "Failed to send message.");
      const conversation = await getConversation(activeConversationId);
      setActiveConversation(conversation);
      await refreshConversations(activeConversationId);
    } finally {
      setSending(false);
    }
  }

  const title = useMemo(() => {
    return activeConversation?.title || "New Conversation";
  }, [activeConversation]);

  return (
    <div className="shell">
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onCreateConversation={handleCreateConversation}
        onSelectConversation={handleSelectConversation}
      />

      <main className="workspace">
        <header className="workspace__header">
          <div>
            <p className="eyebrow">Live Workspace</p>
            <h2>{loading ? "Loading..." : title}</h2>
          </div>
          <div className="status-pill">
            <span className="status-pill__dot"></span>
            React + FastAPI
          </div>
        </header>

        {bannerError ? <div className="banner banner--error">{bannerError}</div> : null}

        <Thread conversation={activeConversation} sending={sending} />
        <Composer onSubmit={handleSubmitMessage} sending={sending || loading} />
      </main>
    </div>
  );
}

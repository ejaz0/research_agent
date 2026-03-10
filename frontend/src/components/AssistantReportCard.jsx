function renderFailures(failures) {
  if (!failures?.length) {
    return null;
  }

  return (
    <section className="report-card__section">
      <h4>Retrieval issues</h4>
      <ul>
        {failures.map((item, index) => (
          <li key={`${item.title}-${index}`}>
            <strong>{item.title}</strong>: {item.error}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function AssistantReportCard({ report, content }) {
  if (!report) {
    return <div className="message__body">{content}</div>;
  }

  return (
    <div className="report-card">
      <section className="report-card__section">
        <h3>Executive Summary</h3>
        <p>{report.executive_summary}</p>
      </section>

      {report.key_findings?.length ? (
        <section className="report-card__section">
          <h4>Key Findings</h4>
          <ul>
            {report.key_findings.map((item, index) => (
              <li key={`${item}-${index}`}>{item}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {report.source_summaries?.length ? (
        <section className="report-card__section">
          <h4>Sources</h4>
          <div className="source-grid">
            {report.source_summaries.map((item, index) => (
              <article className="source-card" key={`${item.url}-${index}`}>
                <p className="source-card__title">{item.title}</p>
                <a href={item.url} target="_blank" rel="noreferrer">
                  {item.url}
                </a>
                <p>{item.summary}</p>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {renderFailures(report.failures)}

      {report.markdown ? (
        <details className="report-card__details">
          <summary>Markdown view</summary>
          <pre>{report.markdown}</pre>
        </details>
      ) : null}
    </div>
  );
}

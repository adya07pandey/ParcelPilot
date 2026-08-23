import { Bot, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import Badge from "../components/Badge";
import DataTable, { EmptyState } from "../components/DataTable";
import { SelectFilter } from "../components/Filters";
import PageHeader from "../components/PageHeader";
import Panel from "../components/Panel";
import { supportApi } from "../supportApi";

export default function InvestigationPage({ customers, seed, embedded = false }) {
  const [accountId, setAccountId] = useState("ALL");
  const [question, setQuestion] = useState("Investigate the current support risk and recommend the next action.");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const customerOptions = useMemo(
    () => [
      { value: "ALL", label: "All Companies" },
      ...customers.map((customer) => ({
        value: customer.account_id,
        label: customer.account_name || customer.account_id
      }))
    ],
    [customers]
  );

  useEffect(() => {
    if (!seed) return;
    if (seed.account_id) setAccountId(seed.account_id);
    if (seed.question) setQuestion(seed.question);
  }, [seed]);

  async function runInvestigation(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = await supportApi.investigate({
        account_id: accountId === "ALL" ? null : accountId,
        question
      });
      setResult(payload);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      {!embedded ? <PageHeader title="AI Investigation" subtitle="Account-scoped investigation for support agents" /> : null}
      <div className="support-detail-grid investigation-layout">
        <Panel title="Investigation Scope">
          <form className="investigation-form" onSubmit={runInvestigation}>
            <SelectFilter
              label="Company / Scope"
              value={accountId}
              onChange={setAccountId}
              options={customerOptions}
            />
            <label className="investigation-question">
              Question
              <textarea value={question} onChange={(event) => setQuestion(event.target.value)} />
            </label>
            <button className="primary-action" disabled={loading || question.trim().length < 3}>
              <Search size={17} />
              {loading ? "Investigating..." : "Start Investigation"}
            </button>
          </form>
          <p className="muted">
            The support agent describes what to investigate. Backend authorization and account-scoped tools decide what data is accessible.
          </p>
        </Panel>

        <Panel title="How This Works">
          <div className="support-fields">
            <Field label="1" value="Authorize support user and selected account scope." />
            <Field label="2" value="Retrieve account, order, ticket, policy, agreement, and known issue evidence." />
            <Field label="3" value="Treat company agreements as higher authority than generic policy when applicable." />
            <Field label="4" value="Calculate confidence in backend and keep human review before actions." />
          </div>
        </Panel>
      </div>

      {error ? <div className="support-alert">{error}</div> : null}
      {result ? <InvestigationResult result={result} /> : null}
    </section>
  );
}

function InvestigationResult({ result }) {
  return (
    <div className="page-stack">
      <Panel title="Conclusion">
        <div className="investigation-result-header">
          <Bot size={20} />
          <Badge value={`${result.confidence} confidence`} />
        </div>
        <AssistantAnswer content={result.answer} />
      </Panel>

      <div className="support-grid two">
        <Panel title="Evidence Panel">
          <MiniEvidence title="Accounts" items={result.evidence.accounts} getKey={(item) => item.account_id} render={(item) => `${item.account_name} (${item.account_id})`} />
          <MiniEvidence title="Orders" items={result.evidence.orders} getKey={(item) => item.order_id} render={(item) => `${item.order_id} - ${item.carrier} - ${item.status}`} />
          <MiniEvidence title="Tickets" items={result.evidence.tickets} getKey={(item) => item.ticket_id} render={(item) => `${item.ticket_id} - ${item.subject}`} />
          <MiniEvidence title="Documents" items={result.evidence.documents} getKey={(item) => item.id} render={(item) => `${item.label} - ${item.status}`} />
        </Panel>

        <Panel title="Excluded / Lower Authority">
          <MiniEvidence
            title="Excluded"
            items={result.evidence.excluded}
            getKey={(item) => item.id}
            render={(item) => `${item.label} - ${item.reason}`}
          />
        </Panel>
      </div>

      <div className="support-grid two">
        <Panel title="Similar Tickets">
          {result.similar_tickets?.length ? (
            <DataTable
              columns={["Ticket", "Subject", "Match"]}
              rows={result.similar_tickets.map((ticket) => ({
                key: ticket.ticket_id,
                cells: [ticket.ticket_id, ticket.subject, `${ticket.match}%`]
              }))}
            />
          ) : (
            <EmptyState text="No similar ticket signals found." />
          )}
        </Panel>

        <Panel title="Known Issue Match">
          {result.known_issue ? (
            <div className="policy-row">
              <strong>{result.known_issue.id} - {result.known_issue.title}</strong>
              <span>{result.known_issue.status} - {result.known_issue.match}% match</span>
              <small>{result.known_issue.workaround}</small>
            </div>
          ) : (
            <EmptyState text="No known issue match found." />
          )}
        </Panel>
      </div>

      <div className="support-grid two">
        <Panel title="Recurring / Incident Candidates">
          <MiniEvidence
            title="Candidates"
            items={result.issue_candidates}
            getKey={(item) => item.name}
            render={(item) => `${item.name} - ${item.ticket_count} tickets / ${item.customer_count} companies - ${item.severity}`}
          />
        </Panel>
        <Panel title="Recommendations">
          <ul className="support-list">
            {result.recommendations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  );
}

function MiniEvidence({ title, items, getKey, render }) {
  if (!items?.length) return <EmptyState text={`No ${title.toLowerCase()} found.`} />;
  return (
    <div className="mini-evidence">
      <strong>{title}</strong>
      {items.map((item) => (
        <span key={getKey(item)}>{render(item)}</span>
      ))}
    </div>
  );
}

function AssistantAnswer({ content }) {
  return (
    <div className="assistant-content">
      {String(content || "")
        .split("\n")
        .filter(Boolean)
        .map((line, index) => {
          if (line.startsWith("### ")) return <h3 key={line}>{line.replace("### ", "")}</h3>;
          if (line.startsWith("- ")) return <p key={`${line}-${index}`}>{line}</p>;
          return <p key={`${line}-${index}`}>{line}</p>;
        })}
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div className="support-field">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

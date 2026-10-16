interface FeaturesPageProps {
  onBackToConsole: () => void;
}

export function FeaturesPage({ onBackToConsole }: FeaturesPageProps) {
  return (
    <div className="doc-page">
      <div className="doc-header">
        <button className="btn-secondary btn-sm" onClick={onBackToConsole}>
          ← Back to Console
        </button>
        <h1>Platform Architecture & Technical Specifications</h1>
        <p className="doc-subtitle">
          In-depth overview of the OpenTrace multi-source intelligence pipeline, correlation engine,
          and public deployment safeguards.
        </p>
      </div>

      <div className="doc-section">
        <h2>1. Massive Public Source Coverage (149 Adapters)</h2>
        <p>
          Unlike tools limited to a handful of social networks or those that depend on paid API keys,
          OpenTrace incorporates 149 active adapters covering diverse public registries:
        </p>
        <div className="table-wrapper">
          <table className="spec-table">
            <thead>
              <tr>
                <th>Category</th>
                <th>Count</th>
                <th>Target</th>
                <th>Key Implementations</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Social & Community</td>
                <td>48</td>
                <td>Username</td>
                <td>GitHub, Reddit, Twitter/X, Medium, Mastodon, Threads, Lemmy</td>
              </tr>
              <tr>
                <td>Developer & Code</td>
                <td>25</td>
                <td>Username</td>
                <td>GitLab, Bitbucket, Docker Hub, PyPI, NPM, Crates.io, SourceForge</td>
              </tr>
              <tr>
                <td>Gaming & Creative</td>
                <td>28</td>
                <td>Username</td>
                <td>Steam, Roblox, Twitch, ArtStation, DeviantArt, SoundCloud</td>
              </tr>
              <tr>
                <td>Email Intelligence</td>
                <td>13</td>
                <td>Email</td>
                <td>Gravatar, OpenPGP, Mail.ru, Disposable MX checks, DNS verification</td>
              </tr>
              <tr>
                <td>Phone & Carrier</td>
                <td>7</td>
                <td>Phone</td>
                <td>E.164 parsing, carrier prefix registries, national number plans</td>
              </tr>
              <tr>
                <td>Academic & Scholar</td>
                <td>9</td>
                <td>Name</td>
                <td>CrossRef, arXiv, Semantic Scholar, ORCID, OpenAlex</td>
              </tr>
              <tr>
                <td>Public Web Search</td>
                <td>2</td>
                <td>Web</td>
                <td>DuckDuckGo HTML, Wikipedia Search</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="doc-section">
        <h2>2. Non-Blocking Concurrency & Bounded Scheduling</h2>
        <p>
          Queries execute through an asynchronous <code>BoundedScheduler</code> configured with global
          and per-host semaphore locks. This guarantees:
        </p>
        <ul>
          <li>Zero server socket exhaustion on high-concurrency investigations</li>
          <li>Protection against accidental Denial-of-Service targeting external websites</li>
          <li>Immediate cancellation propagating through active coroutines upon user request</li>
          <li>Independent per-source execution: slow sources never block fast sources</li>
        </ul>
      </div>

      <div className="doc-section">
        <h2>3. Evidence Provenance & Conservative Classification</h2>
        <p>
          Every finding is accompanied by structured evidence metadata including observed timestamps,
          exact matching identifiers, HTTP status codes, and confidence ratings.
        </p>
        <p>
          If a website responds with a 403 Cloudflare challenge, 429 rate limit, or DNS timeout, OpenTrace
          honestly reports the source as <code>blocked</code>, <code>rate_limited</code>, or <code>unavailable</code>—never
          fabricating a false-negative "not found" or false-positive result.
        </p>
      </div>

      <div className="doc-section">
        <h2>4. Automatic Entity Graph & Recursive Pivoting</h2>
        <p>
          Findings automatically extract typed entities (usernames, emails, domains, phone numbers)
          and connect them via evidence-backed relationship edges. When enabled, the recursive pivot
          engine explores candidate identities across discovery layers with strict budget controls.
        </p>
      </div>

      <div className="doc-section">
        <h2>5. Export & Integration Engine</h2>
        <p>
          All investigation records can be exported in one click:
        </p>
        <ul>
          <li><strong>JSON:</strong> Raw structured machine-readable payload for SIEM ingestion</li>
          <li><strong>CSV:</strong> Tabular breakdown compatible with spreadsheets and data tools</li>
          <li><strong>HTML:</strong> Standalone, air-gapped forensic report with styled evidence tables</li>
        </ul>
      </div>
    </div>
  );
}
